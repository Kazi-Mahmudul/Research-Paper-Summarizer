"""
Hierarchical summarization service orchestrating the complete summarization pipeline.
Coordinates chunk-level summarization and final aggregation.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from services.gemini_client import GeminiClient, GeminiResponse
from services.chunk_manager import TextChunk

logger = logging.getLogger(__name__)

class ChunkSummary(BaseModel):
    """Model for individual chunk summaries."""
    chunk_index: int
    section: str
    section_type: str
    summary: str
    key_points: List[str]
    processing_time: float

class SummaryResult(BaseModel):
    """Model for complete summarization results."""
    title: str
    sections: List[Dict[str, str]]
    chunk_summaries: List[ChunkSummary]
    total_processing_time: float
    chunk_count: int
    success_rate: float

class SummaryGenerator:
    """Service for orchestrating hierarchical PDF summarization."""
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize summary generator.
        
        Args:
            gemini_client: Configured Gemini API client
        """
        self.gemini_client = gemini_client
        self.max_concurrent_requests = 3  # Limit concurrent API calls
        self.chunk_timeout = 60.0  # Timeout for individual chunk processing
        self.aggregation_timeout = 120.0  # Timeout for final aggregation
        
    async def generate_summary(self, chunks: List[TextChunk], paper_title: str = "") -> SummaryResult:
        """
        Generate complete hierarchical summary from text chunks.
        
        Args:
            chunks: List of text chunks to summarize
            paper_title: Original paper title if available
            
        Returns:
            SummaryResult: Complete summarization results
        """
        if not chunks:
            raise ValueError("No chunks provided for summarization")
        
        start_time = time.time()
        logger.info(f"Starting hierarchical summarization of {len(chunks)} chunks")
        
        # Phase 1: Summarize individual chunks
        chunk_summaries = await self._summarize_chunks(chunks)
        
        # Phase 2: Aggregate chunk summaries into final summary
        final_summary = await self._aggregate_summaries(chunk_summaries, paper_title)
        
        total_time = time.time() - start_time
        success_rate = len(chunk_summaries) / len(chunks) if chunks else 0
        
        logger.info(f"Summarization completed in {total_time:.2f}s with {success_rate:.1%} success rate")
        
        return SummaryResult(
            title=paper_title or "Research Paper Summary",
            sections=final_summary,
            chunk_summaries=chunk_summaries,
            total_processing_time=total_time,
            chunk_count=len(chunks),
            success_rate=success_rate
        )
    
    async def _summarize_chunks(self, chunks: List[TextChunk]) -> List[ChunkSummary]:
        """
        Summarize individual chunks concurrently with rate limiting.
        
        Args:
            chunks: List of chunks to summarize
            
        Returns:
            List[ChunkSummary]: Successful chunk summaries
        """
        logger.info(f"Processing {len(chunks)} chunks with max {self.max_concurrent_requests} concurrent requests")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Create tasks for all chunks
        tasks = [
            self._summarize_single_chunk(chunk, semaphore)
            for chunk in chunks
        ]
        
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_summaries = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Chunk {i} summarization failed: {str(result)}")
                failed_count += 1
            elif result is not None:
                successful_summaries.append(result)
        
        logger.info(f"Chunk summarization completed: {len(successful_summaries)} successful, {failed_count} failed")
        
        if not successful_summaries:
            raise RuntimeError("All chunk summarizations failed")
        
        return successful_summaries
    
    async def _summarize_single_chunk(self, chunk: TextChunk, semaphore: asyncio.Semaphore) -> Optional[ChunkSummary]:
        """
        Summarize a single chunk with timeout and error handling.
        
        Args:
            chunk: Text chunk to summarize
            semaphore: Concurrency control semaphore
            
        Returns:
            ChunkSummary: Summary result or None if failed
        """
        async with semaphore:
            try:
                start_time = time.time()
                
                # Make API call with timeout
                response = await asyncio.wait_for(
                    self.gemini_client.summarize_chunk(chunk.content, chunk.section_type),
                    timeout=self.chunk_timeout
                )
                
                processing_time = time.time() - start_time
                
                # Extract key points from summary
                key_points = self._extract_key_points(response.content)
                
                return ChunkSummary(
                    chunk_index=chunk.chunk_index,
                    section=chunk.section,
                    section_type=chunk.section_type,
                    summary=response.content,
                    key_points=key_points,
                    processing_time=processing_time
                )
                
            except asyncio.TimeoutError:
                logger.error(f"Chunk {chunk.chunk_index} summarization timed out after {self.chunk_timeout}s")
                return None
            except Exception as e:
                logger.error(f"Chunk {chunk.chunk_index} summarization failed: {str(e)}")
                return None
    
    async def _aggregate_summaries(self, chunk_summaries: List[ChunkSummary], paper_title: str) -> List[Dict[str, str]]:
        """
        Aggregate chunk summaries into final structured summary.
        
        Args:
            chunk_summaries: List of chunk summaries
            paper_title: Paper title for context
            
        Returns:
            List[Dict[str, str]]: Structured final summary sections
        """
        if not chunk_summaries:
            raise ValueError("No chunk summaries to aggregate")
        
        logger.info(f"Aggregating {len(chunk_summaries)} chunk summaries")
        
        # Prepare summaries for aggregation
        summary_texts = [cs.summary for cs in chunk_summaries]
        
        try:
            # Make aggregation API call with timeout
            response = await asyncio.wait_for(
                self.gemini_client.aggregate_summaries(summary_texts, paper_title),
                timeout=self.aggregation_timeout
            )
            
            # Parse structured summary from response
            structured_summary = self._parse_structured_summary(response.content)
            
            logger.info("Summary aggregation completed successfully")
            return structured_summary
            
        except asyncio.TimeoutError:
            logger.error(f"Summary aggregation timed out after {self.aggregation_timeout}s")
            # Fallback to simple concatenation
            return self._create_fallback_summary(chunk_summaries)
        except Exception as e:
            logger.error(f"Summary aggregation failed: {str(e)}")
            # Fallback to simple concatenation
            return self._create_fallback_summary(chunk_summaries)
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """
        Extract key points from a summary text.
        
        Args:
            summary_text: Summary text to analyze
            
        Returns:
            List[str]: Extracted key points
        """
        # Simple extraction based on sentence structure
        sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
        
        # Filter for sentences that look like key points
        key_points = []
        for sentence in sentences[:5]:  # Limit to top 5 points
            if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                key_points.append(sentence + '.')
        
        return key_points
    
    def _parse_structured_summary(self, summary_text: str) -> List[Dict[str, str]]:
        """
        Parse structured summary from AI response.
        
        Args:
            summary_text: Raw summary text from AI
            
        Returns:
            List[Dict[str, str]]: Structured summary sections
        """
        sections = []
        current_section = None
        current_content = []
        
        lines = summary_text.split('\n')
        
        # Expected section headers
        section_headers = {
            'problem': ['problem', 'research problem', 'research question'],
            'methods': ['methods', 'methodology', 'approach', 'techniques'],
            'results': ['results', 'findings', 'outcomes', 'discoveries'],
            'implications': ['implications', 'significance', 'applications', 'impact'],
            'limitations': ['limitations', 'constraints', 'future work', 'future research']
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            is_header = False
            for section_key, header_variants in section_headers.items():
                for variant in header_variants:
                    if variant in line.lower() and (line.startswith('**') or line.startswith('#') or line.endswith(':')):
                        # Save previous section
                        if current_section and current_content:
                            sections.append({
                                'title': current_section.title(),
                                'content': ' '.join(current_content).strip()
                            })
                        
                        # Start new section
                        current_section = section_key
                        current_content = []
                        is_header = True
                        break
                if is_header:
                    break
            
            if not is_header and current_section:
                # Add content to current section
                clean_line = line.replace('**', '').replace('#', '').strip()
                if clean_line:
                    current_content.append(clean_line)
        
        # Add final section
        if current_section and current_content:
            sections.append({
                'title': current_section.title(),
                'content': ' '.join(current_content).strip()
            })
        
        # Ensure we have the required sections
        if len(sections) < 3:
            logger.warning("Structured parsing failed, using fallback approach")
            return self._create_simple_sections(summary_text)
        
        return sections
    
    def _create_simple_sections(self, summary_text: str) -> List[Dict[str, str]]:
        """
        Create simple sections when structured parsing fails.
        
        Args:
            summary_text: Raw summary text
            
        Returns:
            List[Dict[str, str]]: Simple section structure
        """
        # Split text into roughly equal parts
        words = summary_text.split()
        chunk_size = len(words) // 3
        
        sections = [
            {
                'title': 'Overview',
                'content': ' '.join(words[:chunk_size])
            },
            {
                'title': 'Key Findings',
                'content': ' '.join(words[chunk_size:chunk_size*2])
            },
            {
                'title': 'Conclusions',
                'content': ' '.join(words[chunk_size*2:])
            }
        ]
        
        return sections
    
    def _create_fallback_summary(self, chunk_summaries: List[ChunkSummary]) -> List[Dict[str, str]]:
        """
        Create fallback summary when aggregation fails.
        
        Args:
            chunk_summaries: List of chunk summaries
            
        Returns:
            List[Dict[str, str]]: Fallback summary structure
        """
        logger.info("Creating fallback summary from chunk summaries")
        
        # Group summaries by section type
        section_groups = {}
        for cs in chunk_summaries:
            section_type = cs.section_type
            if section_type not in section_groups:
                section_groups[section_type] = []
            section_groups[section_type].append(cs.summary)
        
        # Create sections from groups
        sections = []
        for section_type, summaries in section_groups.items():
            combined_content = ' '.join(summaries)
            sections.append({
                'title': section_type.title(),
                'content': combined_content
            })
        
        # Ensure minimum sections
        if not sections:
            sections.append({
                'title': 'Summary',
                'content': 'Unable to generate structured summary. Please try again.'
            })
        
        return sections
    
    async def test_summarization(self) -> Dict[str, Any]:
        """
        Test the summarization pipeline with a simple example.
        
        Returns:
            dict: Test results
        """
        try:
            # Test with simple content
            from services.chunk_manager import TextChunk
            
            test_chunk = TextChunk(
                content="This is a test research paper about machine learning applications in healthcare.",
                section="Introduction",
                section_type="introduction",
                chunk_index=0,
                character_count=80,
                word_count=12,
                sentence_count=1
            )
            
            start_time = time.time()
            result = await self.generate_summary([test_chunk], "Test Paper")
            test_time = time.time() - start_time
            
            return {
                "status": "success",
                "processing_time": test_time,
                "sections_generated": len(result.sections),
                "chunk_count": result.chunk_count
            }
            
        except Exception as e:
            logger.error(f"Summarization test failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }