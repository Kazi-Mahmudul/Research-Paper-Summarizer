"""
Text chunking service for managing AI context limits.
Splits text into manageable chunks while preserving semantic boundaries.
"""

import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from services.section_detector import AcademicSection, SectionType

logger = logging.getLogger(__name__)

class TextChunk(BaseModel):
    """Model for text chunks with metadata."""
    content: str
    section: str
    section_type: str
    chunk_index: int
    character_count: int
    word_count: int
    sentence_count: int

class ChunkManager:
    """Service for intelligent text chunking with semantic boundary preservation."""
    
    def __init__(self, max_chunk_size: int = 10000):
        """
        Initialize chunk manager.
        
        Args:
            max_chunk_size: Maximum characters per chunk
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = 100  # Minimum viable chunk size
        self.overlap_size = 200  # Character overlap between chunks for context
        self.sentence_endings = r'[.!?]+\s+'
        
    def create_chunks(self, sections: List[AcademicSection]) -> List[TextChunk]:
        """
        Create chunks from academic sections with size and boundary constraints.
        
        Args:
            sections: List of detected academic sections
            
        Returns:
            List[TextChunk]: Generated text chunks
        """
        if not sections:
            return []
        
        all_chunks = []
        global_chunk_index = 0
        
        for section in sections:
            if not section.content or len(section.content.strip()) < self.min_chunk_size:
                logger.debug(f"Skipping small section: {section.name}")
                continue
            
            section_chunks = self._chunk_section(section, global_chunk_index)
            all_chunks.extend(section_chunks)
            global_chunk_index += len(section_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(sections)} sections")
        return all_chunks
    
    def _chunk_section(self, section: AcademicSection, start_index: int) -> List[TextChunk]:
        """
        Chunk a single academic section.
        
        Args:
            section: Academic section to chunk
            start_index: Starting chunk index for this section
            
        Returns:
            List[TextChunk]: Chunks for this section
        """
        content = section.content.strip()
        
        if len(content) <= self.max_chunk_size:
            # Section fits in one chunk
            return [self._create_chunk(
                content=content,
                section=section.name,
                section_type=section.section_type.value,
                chunk_index=start_index
            )]
        
        # Section needs to be split
        return self._split_large_section(section, start_index)
    
    def _split_large_section(self, section: AcademicSection, start_index: int) -> List[TextChunk]:
        """
        Split a large section into multiple chunks with sentence boundary preservation.
        
        Args:
            section: Section to split
            start_index: Starting chunk index
            
        Returns:
            List[TextChunk]: Split chunks
        """
        content = section.content.strip()
        chunks = []
        current_pos = 0
        chunk_index = start_index
        
        while current_pos < len(content):
            # Determine chunk end position
            chunk_end = min(current_pos + self.max_chunk_size, len(content))
            
            # If not at the end of content, try to find a good break point
            if chunk_end < len(content):
                chunk_end = self._find_optimal_break_point(content, current_pos, chunk_end)
            
            # Extract chunk content
            chunk_content = content[current_pos:chunk_end].strip()
            
            if len(chunk_content) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    content=chunk_content,
                    section=section.name,
                    section_type=section.section_type.value,
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            # Move to next chunk with overlap
            current_pos = max(chunk_end - self.overlap_size, current_pos + self.min_chunk_size)
            
            # Prevent infinite loop
            if current_pos >= len(content):
                break
        
        return chunks
    
    def _find_optimal_break_point(self, text: str, start: int, max_end: int) -> int:
        """
        Find the optimal break point for chunking, preferring sentence boundaries.
        
        Args:
            text: Full text content
            start: Start position of current chunk
            max_end: Maximum end position
            
        Returns:
            int: Optimal break point position
        """
        # Look for sentence endings within the last 20% of the chunk
        search_start = max_end - (self.max_chunk_size // 5)
        search_region = text[search_start:max_end]
        
        # Find sentence endings
        sentence_matches = list(re.finditer(self.sentence_endings, search_region))
        
        if sentence_matches:
            # Use the last sentence ending found
            last_match = sentence_matches[-1]
            return search_start + last_match.end()
        
        # Fallback: look for paragraph breaks
        paragraph_matches = list(re.finditer(r'\n\s*\n', text[search_start:max_end]))
        if paragraph_matches:
            last_match = paragraph_matches[-1]
            return search_start + last_match.start()
        
        # Fallback: look for any line break
        line_matches = list(re.finditer(r'\n', text[search_start:max_end]))
        if line_matches:
            last_match = line_matches[-1]
            return search_start + last_match.start()
        
        # Final fallback: use word boundary
        words = text[start:max_end].split()
        if len(words) > 1:
            # Remove last word to avoid cutting mid-word
            word_boundary = start + len(' '.join(words[:-1]))
            return min(word_boundary, max_end - 1)
        
        return max_end
    
    def _create_chunk(self, content: str, section: str, section_type: str, chunk_index: int) -> TextChunk:
        """
        Create a TextChunk object with metadata.
        
        Args:
            content: Chunk text content
            section: Section name
            section_type: Section type
            chunk_index: Global chunk index
            
        Returns:
            TextChunk: Created chunk with metadata
        """
        # Calculate statistics
        word_count = len(content.split())
        sentence_count = len(re.findall(self.sentence_endings, content + ' '))  # Add space for final sentence
        
        return TextChunk(
            content=content,
            section=section,
            section_type=section_type,
            chunk_index=chunk_index,
            character_count=len(content),
            word_count=word_count,
            sentence_count=max(sentence_count, 1)  # At least 1 sentence
        )
    
    def validate_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Validate chunks meet size and quality requirements.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            List[TextChunk]: Validated chunks
        """
        valid_chunks = []
        
        for chunk in chunks:
            # Check size constraints
            if chunk.character_count > self.max_chunk_size:
                logger.warning(f"Chunk {chunk.chunk_index} exceeds max size: {chunk.character_count}")
                continue
            
            if chunk.character_count < self.min_chunk_size:
                logger.debug(f"Skipping small chunk {chunk.chunk_index}: {chunk.character_count} chars")
                continue
            
            # Check content quality
            if not chunk.content.strip():
                logger.debug(f"Skipping empty chunk {chunk.chunk_index}")
                continue
            
            # Check for reasonable word count
            if chunk.word_count < 10:
                logger.debug(f"Skipping chunk {chunk.chunk_index} with too few words: {chunk.word_count}")
                continue
            
            valid_chunks.append(chunk)
        
        logger.info(f"Validated {len(valid_chunks)} out of {len(chunks)} chunks")
        return valid_chunks
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> dict:
        """
        Get statistics about the generated chunks.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            dict: Chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "total_words": 0,
                "average_chunk_size": 0,
                "sections_represented": 0
            }
        
        total_chars = sum(chunk.character_count for chunk in chunks)
        total_words = sum(chunk.word_count for chunk in chunks)
        sections = set(chunk.section for chunk in chunks)
        
        size_distribution = {
            "small": len([c for c in chunks if c.character_count < 3000]),
            "medium": len([c for c in chunks if 3000 <= c.character_count < 7000]),
            "large": len([c for c in chunks if c.character_count >= 7000])
        }
        
        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "total_words": total_words,
            "average_chunk_size": total_chars // len(chunks),
            "average_words_per_chunk": total_words // len(chunks),
            "sections_represented": len(sections),
            "section_names": list(sections),
            "size_distribution": size_distribution,
            "max_chunk_size": max(chunk.character_count for chunk in chunks),
            "min_chunk_size": min(chunk.character_count for chunk in chunks)
        }
    
    def optimize_chunks_for_ai(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Optimize chunks specifically for AI processing.
        
        Args:
            chunks: Original chunks
            
        Returns:
            List[TextChunk]: Optimized chunks
        """
        optimized = []
        
        for chunk in chunks:
            # Add context prefix for better AI understanding
            context_prefix = f"[Section: {chunk.section}]\n\n"
            
            # Ensure chunk doesn't exceed limit with prefix
            available_space = self.max_chunk_size - len(context_prefix)
            
            if len(chunk.content) > available_space:
                # Truncate content to fit with prefix
                truncated_content = chunk.content[:available_space - 3] + "..."
                optimized_content = context_prefix + truncated_content
            else:
                optimized_content = context_prefix + chunk.content
            
            # Create optimized chunk
            optimized_chunk = TextChunk(
                content=optimized_content,
                section=chunk.section,
                section_type=chunk.section_type,
                chunk_index=chunk.chunk_index,
                character_count=len(optimized_content),
                word_count=len(optimized_content.split()),
                sentence_count=chunk.sentence_count
            )
            
            optimized.append(optimized_chunk)
        
        return optimized