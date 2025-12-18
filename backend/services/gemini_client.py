"""
Google Gemini AI client service for text summarization.
Handles API communication, rate limiting, and response validation.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)

class GeminiResponse(BaseModel):
    """Model for Gemini API responses."""
    model_config = {"protected_namespaces": ()}
    
    content: str
    model_name: str
    tokens_used: Optional[int] = None
    processing_time: float

class GeminiClient:
    """Service for interacting with Google Gemini AI API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
        """
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key is required")
        
        self.api_key = api_key
        self.model_name = "gemini-2.5-flash"  # Using Gemini 2.5 Flash (latest stable version)
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 16.0  # Maximum delay between retries
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info(f"Initialized Gemini client with model: {self.model_name}")
    
    async def summarize_chunk(self, chunk_content: str, section_type: str) -> GeminiResponse:
        """
        Summarize a single text chunk with academic focus.
        
        Args:
            chunk_content: Text content to summarize
            section_type: Type of academic section
            
        Returns:
            GeminiResponse: Summarization result
        """
        prompt = self._build_chunk_prompt(chunk_content, section_type)
        return await self._make_api_call(prompt, "chunk_summarization")
    
    async def aggregate_summaries(self, chunk_summaries: List[str], original_title: str = "") -> GeminiResponse:
        """
        Aggregate multiple chunk summaries into a cohesive academic summary.
        
        Args:
            chunk_summaries: List of individual chunk summaries
            original_title: Original paper title if available
            
        Returns:
            GeminiResponse: Final aggregated summary
        """
        prompt = self._build_aggregation_prompt(chunk_summaries, original_title)
        return await self._make_api_call(prompt, "summary_aggregation")
    
    def _build_chunk_prompt(self, content: str, section_type: str) -> str:
        """Build prompt for chunk-level summarization."""
        return f"""You are an expert academic researcher. Summarize this {section_type} section with appropriate detail.

Requirements:
- 2-4 sentences depending on content complexity
- Include key details that contribute to understanding the research
- Use clear, academic language
- Focus on the most important information

Text to summarize:
{content}

Detailed summary:"""
    
    def _build_aggregation_prompt(self, summaries: List[str], title: str) -> str:
        """Build prompt for final summary aggregation."""
        # Remove duplicate summaries and clean up
        unique_summaries = []
        seen_content = set()
        
        for summary in summaries:
            # Simple deduplication based on first 100 characters
            summary_key = summary.strip()[:100].lower()
            if summary_key not in seen_content and len(summary.strip()) > 20:
                seen_content.add(summary_key)
                unique_summaries.append(summary.strip())
        
        combined_summaries = "\n\n".join([f"Section {i+1}: {summary}" for i, summary in enumerate(unique_summaries)])
        
        title_context = f"Paper: {title}\n\n" if title else ""
        
        return f"""You are an expert academic researcher. Create a comprehensive, structured summary from these section summaries.

{title_context}Format your response with these sections (be detailed but focused):

**Problem**
[What research problem does this address? Include background and significance in 2-4 sentences]

**Methods**
[What methodology was used? Include key techniques, data sources, and experimental design in 3-5 sentences]

**Results**
[What were the key findings? Include specific results, metrics, or outcomes in 3-5 sentences]

**Implications**
[What are the broader implications? Include practical applications, theoretical contributions, and significance in 2-4 sentences]

**Limitations**
[What limitations are mentioned? Include study limitations and future research directions in 2-3 sentences]

IMPORTANT:
- Provide sufficient detail to give a comprehensive understanding of the research
- Use clear, academic language
- Avoid repetition between sections
- Focus on the most important and impactful information
- Balance comprehensiveness with conciseness (not too verbose)

Section summaries to synthesize:
{combined_summaries}

Structured summary:"""
    
    async def _make_api_call(self, prompt: str, call_type: str) -> GeminiResponse:
        """
        Make API call to Gemini with retry logic and error handling.
        
        Args:
            prompt: Text prompt for the model
            call_type: Type of API call for logging
            
        Returns:
            GeminiResponse: API response
        """
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making Gemini API call (attempt {attempt + 1}/{self.max_retries}) for {call_type}")
                
                # Make the API call
                response = await self._call_gemini_api(prompt)
                
                processing_time = time.time() - start_time
                
                # Validate response
                validated_response = self._validate_response(response, call_type)
                
                logger.info(f"Successful Gemini API call for {call_type} in {processing_time:.2f}s")
                
                return GeminiResponse(
                    content=validated_response,
                    model_name=self.model_name,
                    processing_time=processing_time
                )
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Gemini API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {call_type}")
        
        # All retries failed
        raise RuntimeError(f"Gemini API call failed after {self.max_retries} attempts: {str(last_exception)}")
    
    async def _call_gemini_api(self, prompt: str) -> Any:
        """Make the actual API call to Gemini."""
        try:
            # Use generate_content_async for async operation
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response
        except Exception as e:
            # Handle specific Gemini API errors
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate limit" in error_msg:
                raise RuntimeError(f"API rate limit exceeded: {str(e)}")
            elif "api key" in error_msg or "authentication" in error_msg:
                raise ValueError(f"API authentication failed: {str(e)}")
            elif "safety" in error_msg or "blocked" in error_msg:
                raise ValueError(f"Content blocked by safety filters: {str(e)}")
            else:
                raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def _validate_response(self, response: Any, call_type: str) -> str:
        """
        Validate and extract content from Gemini response.
        
        Args:
            response: Raw Gemini API response
            call_type: Type of API call for error context
            
        Returns:
            str: Validated response content
        """
        try:
            if not response:
                raise ValueError("Empty response from Gemini API")
            
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("No text content in Gemini response")
            
            content = response.text.strip()
            
            if not content:
                raise ValueError("Empty text content in Gemini response")
            
            # Basic content validation
            if len(content) < 10:
                raise ValueError(f"Response too short: {len(content)} characters")
            
            # Check for common error indicators
            error_indicators = [
                "i cannot", "i can't", "unable to", "sorry", "error",
                "failed to", "not possible", "cannot process"
            ]
            
            content_lower = content.lower()
            for indicator in error_indicators:
                if indicator in content_lower:
                    logger.warning(f"Potential error in response: {indicator}")
            
            # Post-process to enforce length limits
            content = self._enforce_length_limits(content, call_type)
            
            return content
            
        except Exception as e:
            logger.error(f"Response validation failed for {call_type}: {str(e)}")
            raise ValueError(f"Invalid Gemini response: {str(e)}")
    
    def _enforce_length_limits(self, content: str, call_type: str) -> str:
        """
        Enforce reasonable length limits on responses as a backup measure.
        
        Args:
            content: Response content to limit
            call_type: Type of call for appropriate limits
            
        Returns:
            str: Length-limited content
        """
        if call_type == "chunk_summarization":
            # For chunks: max 600 characters (allowing for more detailed summaries)
            if len(content) > 600:
                content = content[:597] + "..."
                logger.warning(f"Truncated chunk summary to 600 characters")
        
        elif call_type == "summary_aggregation":
            # For final summaries: max 3000 characters (allowing for more comprehensive summaries)
            if len(content) > 3000:
                content = self._truncate_structured_summary(content)
                logger.warning(f"Truncated final summary to fit length limits")
        
        return content
    
    def _truncate_structured_summary(self, content: str) -> str:
        """
        Truncate structured summary while preserving format.
        
        Args:
            content: Original summary content
            
        Returns:
            str: Truncated summary
        """
        lines = content.split('\n')
        truncated_lines = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if it's a section header
            if line.startswith('**') and line.endswith('**'):
                current_section = line
                truncated_lines.append(line)
            elif current_section:
                # Truncate content lines to max 50 words (more reasonable)
                words = line.split()
                if len(words) > 50:
                    line = ' '.join(words[:50]) + "..."
                truncated_lines.append(line)
                truncated_lines.append('')  # Add spacing
        
        return '\n'.join(truncated_lines)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Gemini API.
        
        Returns:
            dict: Connection test results
        """
        try:
            test_prompt = "Please respond with 'Connection successful' to confirm the API is working."
            
            start_time = time.time()
            response = await self._make_api_call(test_prompt, "connection_test")
            test_time = time.time() - start_time
            
            return {
                "status": "success",
                "model": self.model_name,
                "response_time": test_time,
                "response_preview": response.content[:100] + "..." if len(response.content) > 100 else response.content
            }
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "model": self.model_name
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model."""
        return {
            "model_name": self.model_name,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "api_configured": bool(self.api_key)
        }