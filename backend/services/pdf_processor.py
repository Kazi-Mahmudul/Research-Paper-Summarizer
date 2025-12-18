"""
PDF text extraction service using PyMuPDF with pdfplumber fallback.
Handles text extraction, cleaning, and metadata extraction.
"""

import sys

# Handle different PyMuPDF versions with graceful fallback
try:
    if sys.version_info >= (3, 11):
        try:
            import fitz_new as fitz  # Newer versions
        except ImportError:
            import fitz  # Fallback to standard fitz
    else:
        import fitz  # Standard fitz for older Python versions
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

import pdfplumber
import re
import logging
from typing import Dict, Any, Optional
from io import BytesIO
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractedText(BaseModel):
    """Model for extracted PDF text and metadata."""
    content: str
    metadata: Dict[str, Any]
    page_count: int
    extraction_method: str

class PDFProcessor:
    """Service for extracting and processing text from PDF files."""
    
    def __init__(self):
        """Initialize PDF processor."""
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    async def extract_text(self, pdf_content: bytes, filename: str = "unknown.pdf") -> ExtractedText:
        """
        Extract text from PDF content using PyMuPDF with pdfplumber fallback.
        
        Args:
            pdf_content: Raw PDF file content as bytes
            filename: Original filename for logging
            
        Returns:
            ExtractedText: Extracted text with metadata
            
        Raises:
            ValueError: If PDF is corrupted or cannot be processed
            RuntimeError: If extraction fails with both methods
        """
        if len(pdf_content) == 0:
            raise ValueError("Empty PDF file")
        
        if len(pdf_content) > self.max_file_size:
            raise ValueError(f"PDF file too large: {len(pdf_content)} bytes")
        
        # Try PyMuPDF first if available (faster and more reliable)
        if PYMUPDF_AVAILABLE:
            try:
                logger.info(f"Attempting text extraction with PyMuPDF for {filename}")
                return await self._extract_with_pymupdf(pdf_content, filename)
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed for {filename}: {str(e)}")
                
                # Fallback to pdfplumber
                try:
                    logger.info(f"Attempting text extraction with pdfplumber for {filename}")
                    return await self._extract_with_pdfplumber(pdf_content, filename)
                except Exception as e2:
                    logger.error(f"Both extraction methods failed for {filename}")
                    raise RuntimeError(f"PDF text extraction failed: PyMuPDF error: {str(e)}, pdfplumber error: {str(e2)}")
        else:
            # If PyMuPDF is not available, use pdfplumber directly
            try:
                logger.info(f"Attempting text extraction with pdfplumber for {filename} (PyMuPDF not available)")
                return await self._extract_with_pdfplumber(pdf_content, filename)
            except Exception as e:
                logger.error(f"PDF extraction failed for {filename} with pdfplumber")
                raise RuntimeError(f"PDF text extraction failed: pdfplumber error: {str(e)}")
    
    async def _extract_with_pymupdf(self, pdf_content: bytes, filename: str) -> ExtractedText:
        """Extract text using PyMuPDF (fitz)."""
        # Check if fitz is available
        if not PYMUPDF_AVAILABLE or fitz is None:
            raise RuntimeError("PyMuPDF is not available")
            
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            if doc.is_encrypted:
                raise ValueError("PDF is password protected")
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    text_parts.append(text)
            
            # Get metadata
            metadata = doc.metadata or {}
            page_count = doc.page_count
            
            doc.close()
            
            # Combine and clean text
            raw_text = "\n\n".join(text_parts)
            cleaned_text = self._clean_text(raw_text)
            
            if not cleaned_text.strip():
                raise ValueError("No readable text found in PDF")
            
            return ExtractedText(
                content=cleaned_text,
                metadata={
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": str(metadata.get("creationDate", "")),
                    "modification_date": str(metadata.get("modDate", "")),
                    "filename": filename
                },
                page_count=page_count,
                extraction_method="pymupdf"
            )
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {str(e)}")
            raise
    
    async def _extract_with_pdfplumber(self, pdf_content: bytes, filename: str) -> ExtractedText:
        """Extract text using pdfplumber as fallback."""
        try:
            # Open PDF from bytes
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                
                if not pdf.pages:
                    raise ValueError("PDF has no pages")
                
                # Extract text from all pages
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():  # Only add non-empty pages
                        text_parts.append(text)
                
                # Get basic metadata
                metadata = pdf.metadata or {}
                page_count = len(pdf.pages)
                
                # Combine and clean text
                raw_text = "\n\n".join(text_parts)
                cleaned_text = self._clean_text(raw_text)
                
                if not cleaned_text.strip():
                    raise ValueError("No readable text found in PDF")
                
                return ExtractedText(
                    content=cleaned_text,
                    metadata={
                        "title": metadata.get("Title", ""),
                        "author": metadata.get("Author", ""),
                        "subject": metadata.get("Subject", ""),
                        "creator": metadata.get("Creator", ""),
                        "producer": metadata.get("Producer", ""),
                        "creation_date": str(metadata.get("CreationDate", "")),
                        "modification_date": str(metadata.get("ModDate", "")),
                        "filename": filename
                    },
                    page_count=page_count,
                    extraction_method="pdfplumber"
                )
                
        except Exception as e:
            logger.error(f"pdfplumber extraction error: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing artifacts and normalizing whitespace.
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)  # Control characters
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Non-ASCII characters (optional, might remove accents)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
        text = re.sub(r'[ \t]+\n', '\n', text)  # Trailing spaces before newlines
        text = re.sub(r'\n[ \t]+', '\n', text)  # Leading spaces after newlines
        
        # Remove page numbers and headers/footers (basic patterns)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip likely page numbers (single numbers or "Page X" patterns)
            if re.match(r'^\d+$', line) or re.match(r'^Page\s+\d+$', line, re.IGNORECASE):
                continue
            
            # Skip very short lines that are likely artifacts
            if len(line) < 3:
                continue
                
            cleaned_lines.append(line)
        
        # Rejoin and final cleanup
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Normalize paragraph breaks
        
        return cleaned_text.strip()
    
    def validate_pdf_content(self, content: bytes) -> bool:
        """
        Validate that content is a valid PDF file.
        
        Args:
            content: File content as bytes
            
        Returns:
            bool: True if valid PDF, False otherwise
        """
        if not content or len(content) < 4:
            return False
        
        # Check PDF magic number
        return content.startswith(b'%PDF-')
    
    def get_pdf_info(self, content: bytes) -> Dict[str, Any]:
        """
        Get basic PDF information without full text extraction.
        
        Args:
            content: PDF content as bytes
            
        Returns:
            dict: Basic PDF information
        """
        if not PYMUPDF_AVAILABLE:
            # Fallback method when PyMuPDF is not available
            return {
                "page_count": 0,
                "is_encrypted": False,
                "metadata": {},
                "file_size": len(content),
                "warning": "Detailed PDF info requires PyMuPDF"
            }
        
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            info = {
                "page_count": doc.page_count,
                "is_encrypted": doc.is_encrypted,
                "metadata": doc.metadata or {},
                "file_size": len(content)
            }
            doc.close()
            return info
        except Exception as e:
            logger.error(f"Failed to get PDF info: {str(e)}")
            return {
                "page_count": 0,
                "is_encrypted": False,
                "metadata": {},
                "file_size": len(content),
                "error": str(e)
            }