"""
Basic tests to verify backend functionality.
"""

import pytest
import asyncio
from services.pdf_processor import PDFProcessor
from services.section_detector import SectionDetector
from services.chunk_manager import ChunkManager

def test_pdf_processor_initialization():
    """Test that PDFProcessor can be initialized."""
    processor = PDFProcessor()
    assert processor is not None
    assert processor.max_file_size == 50 * 1024 * 1024

def test_section_detector_initialization():
    """Test that SectionDetector can be initialized."""
    detector = SectionDetector()
    assert detector is not None
    assert detector.min_section_length == 50

def test_chunk_manager_initialization():
    """Test that ChunkManager can be initialized."""
    manager = ChunkManager()
    assert manager is not None
    assert manager.max_chunk_size == 10000

def test_pdf_content_validation():
    """Test PDF content validation."""
    processor = PDFProcessor()
    
    # Test valid PDF header
    valid_pdf = b'%PDF-1.4\n%some content'
    assert processor.validate_pdf_content(valid_pdf) == True
    
    # Test invalid content
    invalid_content = b'not a pdf'
    assert processor.validate_pdf_content(invalid_content) == False
    
    # Test empty content
    assert processor.validate_pdf_content(b'') == False

def test_section_detection_basic():
    """Test basic section detection functionality."""
    detector = SectionDetector()
    
    # Test with simple text
    text = "This is a simple text without sections."
    sections = detector.detect_sections(text)
    
    assert len(sections) >= 1
    assert sections[0].section_type.value == "unknown"

def test_chunk_creation_basic():
    """Test basic chunk creation."""
    from services.section_detector import AcademicSection, SectionType
    
    manager = ChunkManager()
    
    # Create a test section with enough content (minimum 100 chars)
    content = "This is a test introduction section with enough content to create a chunk. " * 3
    test_section = AcademicSection(
        name="Introduction",
        section_type=SectionType.INTRODUCTION,
        content=content,
        start_position=0,
        end_position=len(content),
        confidence=0.8
    )
    
    chunks = manager.create_chunks([test_section])
    assert len(chunks) >= 1
    assert chunks[0].section == "Introduction"

if __name__ == "__main__":
    pytest.main([__file__])