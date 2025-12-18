"""
FastAPI backend for PDF Research Summarizer.
Handles PDF upload, text extraction, and AI-powered summarization.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging
import time
from config import get_config, validate_startup_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if os.getenv('LOG_TO_FILE', 'false').lower() == 'true' else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration at startup
startup_status = validate_startup_config()
if startup_status["status"] == "error":
    logger.error(f"Startup configuration error: {startup_status['message']}")
    if "details" in startup_status:
        logger.error(f"Details: {startup_status['details']}")
    raise SystemExit(1)

# Load configuration
try:
    config = get_config()
    logger.info(f"Configuration loaded successfully")
    logger.info(f"Backend URL: {config.backend_url}")
    logger.info(f"Frontend URL: {config.frontend_url}")
except Exception as e:
    logger.error(f"Failed to load configuration: {str(e)}")
    raise SystemExit(1)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Research Summarizer",
    description="AI-powered academic paper summarization service",
    version="1.0.0",
    docs_url="/docs" if os.getenv('ENVIRONMENT', 'development') == 'development' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT', 'development') == 'development' else None
)

# Configure CORS for frontend communication
allowed_origins = [
    config.frontend_url,
    "http://localhost:5173", 
    "http://127.0.0.1:5173"
]

# Add production origins if specified
if os.getenv('PRODUCTION_ORIGINS'):
    production_origins = os.getenv('PRODUCTION_ORIGINS').split(',')
    allowed_origins.extend([origin.strip() for origin in production_origins])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Only add HSTS in production with HTTPS
    if os.getenv('ENVIRONMENT') == 'production' and request.url.scheme == 'https':
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Response models
class SummarySection(BaseModel):
    title: str
    content: str

class SummaryResponse(BaseModel):
    title: str
    sections: List[SummarySection]
    processing_time: float
    chunk_count: int

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# File upload validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_CONTENT_TYPES = ["application/pdf"]

def validate_pdf_file(file: UploadFile) -> None:
    """Validate uploaded PDF file type and size."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are allowed. Received: {file.content_type}"
        )
    
    # Note: file.size might be None for some uploads, so we'll check during processing
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for system status monitoring."""
    try:
        # Check configuration status
        config_status = validate_startup_config()
        gemini_status = "configured" if config_status["status"] == "success" else "error"
        
        return HealthResponse(
            status="healthy" if config_status["status"] == "success" else "degraded",
            timestamp=datetime.now().isoformat(),
            services={
                "api": "running",
                "gemini_api": gemini_status,
                "configuration": config_status["status"]
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/api/summarize", response_model=SummaryResponse)
async def summarize_pdf(file: UploadFile = File(...)):
    """
    Process uploaded PDF and generate academic summary.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        SummaryResponse with structured academic summary
    """
    start_time = time.time()
    
    try:
        # Validate file
        validate_pdf_file(file)
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        logger.info(f"Processing PDF file: {file.filename} ({len(content)} bytes)")
        
        # Initialize services
        from services.pdf_processor import PDFProcessor
        from services.section_detector import SectionDetector
        from services.chunk_manager import ChunkManager
        from services.gemini_client import GeminiClient
        from services.summary_generator import SummaryGenerator
        
        pdf_processor = PDFProcessor()
        section_detector = SectionDetector()
        chunk_manager = ChunkManager()
        gemini_client = GeminiClient(config.gemini_api_key)
        summary_generator = SummaryGenerator(gemini_client)
        
        # Step 1: Extract text from PDF
        logger.info("Extracting text from PDF...")
        extracted_text = await pdf_processor.extract_text(content, file.filename or "unknown.pdf")
        logger.info(f"Extracted {len(extracted_text.content)} characters from {extracted_text.page_count} pages")
        
        # Step 2: Detect academic sections
        logger.info("Detecting academic sections...")
        sections = section_detector.detect_sections(extracted_text.content)
        logger.info(f"Detected {len(sections)} academic sections")
        
        # If no sections detected, create a fallback section with the full text
        if not sections:
            logger.info("No sections detected, creating fallback section with full text")
            from services.section_detector import AcademicSection, SectionType
            fallback_section = AcademicSection(
                name="Full Document",
                section_type=SectionType.UNKNOWN,
                content=extracted_text.content,
                start_position=0,
                end_position=len(extracted_text.content),
                confidence=1.0
            )
            sections = [fallback_section]
        
        # Step 3: Create chunks from sections
        logger.info("Creating text chunks...")
        chunks = chunk_manager.create_chunks(sections)
        validated_chunks = chunk_manager.validate_chunks(chunks)
        optimized_chunks = chunk_manager.optimize_chunks_for_ai(validated_chunks)
        logger.info(f"Created {len(optimized_chunks)} optimized chunks")
        
        if not optimized_chunks:
            raise HTTPException(
                status_code=422,
                detail="No valid text chunks could be created from the PDF. The document may be too short or contain no readable text."
            )
        
        # Step 4: Generate hierarchical summary
        logger.info("Generating hierarchical summary...")
        summary_result = await summary_generator.generate_summary(
            optimized_chunks, 
            extracted_text.metadata.get("title", "")
        )
        
        processing_time = time.time() - start_time
        logger.info(f"PDF processing completed in {processing_time:.2f}s")
        
        # Convert to response format
        response_sections = [
            SummarySection(title=section["title"], content=section["content"])
            for section in summary_result.sections
        ]
        
        return SummaryResponse(
            title=summary_result.title,
            sections=response_sections,
            processing_time=processing_time,
            chunk_count=len(optimized_chunks)
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"PDF validation error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"PDF processing error: {str(e)}"
        )
    except RuntimeError as e:
        logger.error(f"PDF processing runtime error: {str(e)}")
        if "api" in str(e).lower() or "gemini" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail=f"AI service unavailable: {str(e)}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Processing error: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error during PDF processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during PDF processing: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler for structured error responses."""
    error_response = ErrorResponse(
        error=exc.detail,
        timestamp=datetime.now().isoformat()
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    error_response = ErrorResponse(
        error="Internal server error",
        details=str(exc),
        timestamp=datetime.now().isoformat()
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)