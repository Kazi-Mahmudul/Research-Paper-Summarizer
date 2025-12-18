"""
Academic section detection service for research papers.
Identifies and extracts standard academic sections from text.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class SectionType(str, Enum):
    """Enumeration of academic section types."""
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    ACKNOWLEDGMENTS = "acknowledgments"
    APPENDIX = "appendix"
    UNKNOWN = "unknown"

class AcademicSection(BaseModel):
    """Model for detected academic sections."""
    name: str
    section_type: SectionType
    content: str
    start_position: int
    end_position: int
    confidence: float

class SectionDetector:
    """Service for detecting academic sections in research papers."""
    
    def __init__(self):
        """Initialize section detector with patterns."""
        self.section_patterns = self._build_section_patterns()
        self.min_section_length = 50  # Minimum characters for a valid section
        self.max_section_length = 50000  # Maximum characters for a single section
    
    def _build_section_patterns(self) -> Dict[SectionType, List[str]]:
        """Build regex patterns for detecting academic sections."""
        return {
            SectionType.ABSTRACT: [
                r'\b(?:abstract|summary)\b',
                r'^\s*abstract\s*$',
                r'^\s*summary\s*$'
            ],
            SectionType.INTRODUCTION: [
                r'\b(?:introduction|background)\b',
                r'^\s*1\.?\s*introduction\s*$',
                r'^\s*introduction\s*$',
                r'^\s*background\s*$'
            ],
            SectionType.METHODOLOGY: [
                r'\b(?:methodology|methods?|materials?\s+and\s+methods?|experimental\s+setup|approach)\b',
                r'^\s*(?:\d+\.?\s*)?(?:methodology|methods?|materials?\s+and\s+methods?)\s*$',
                r'^\s*experimental\s+(?:setup|design|procedure)\s*$'
            ],
            SectionType.RESULTS: [
                r'\b(?:results?|findings?|experimental\s+results?)\b',
                r'^\s*(?:\d+\.?\s*)?results?\s*$',
                r'^\s*(?:\d+\.?\s*)?findings?\s*$',
                r'^\s*experimental\s+results?\s*$'
            ],
            SectionType.DISCUSSION: [
                r'\b(?:discussion|analysis|interpretation)\b',
                r'^\s*(?:\d+\.?\s*)?discussion\s*$',
                r'^\s*(?:\d+\.?\s*)?analysis\s*$',
                r'^\s*results?\s+and\s+discussion\s*$'
            ],
            SectionType.CONCLUSION: [
                r'\b(?:conclusions?|concluding\s+remarks?|final\s+thoughts?|summary\s+and\s+conclusions?)\b',
                r'^\s*(?:\d+\.?\s*)?conclusions?\s*$',
                r'^\s*concluding\s+remarks?\s*$',
                r'^\s*summary\s+and\s+conclusions?\s*$'
            ],
            SectionType.REFERENCES: [
                r'\b(?:references?|bibliography|works?\s+cited|literature\s+cited)\b',
                r'^\s*references?\s*$',
                r'^\s*bibliography\s*$',
                r'^\s*works?\s+cited\s*$'
            ],
            SectionType.ACKNOWLEDGMENTS: [
                r'\b(?:acknowledgments?|acknowledgements?|thanks?)\b',
                r'^\s*acknowledgments?\s*$',
                r'^\s*acknowledgements?\s*$'
            ],
            SectionType.APPENDIX: [
                r'\b(?:appendix|appendices|supplementary\s+materials?)\b',
                r'^\s*appendix\s*[a-z]?\s*$',
                r'^\s*supplementary\s+materials?\s*$'
            ]
        }
    
    def detect_sections(self, text: str) -> List[AcademicSection]:
        """
        Detect academic sections in the given text.
        
        Args:
            text: Full text content to analyze
            
        Returns:
            List[AcademicSection]: Detected sections with boundaries
        """
        if not text or len(text.strip()) < self.min_section_length:
            return [self._create_unknown_section(text, 0, len(text))]
        
        # Find section headers
        section_markers = self._find_section_markers(text)
        
        if not section_markers:
            logger.info("No clear section markers found, treating as continuous text")
            return [self._create_unknown_section(text, 0, len(text))]
        
        # Create sections from markers
        sections = self._create_sections_from_markers(text, section_markers)
        
        # Filter out references section if requested
        sections = self._filter_references_section(sections)
        
        # Validate and clean sections
        sections = self._validate_sections(sections)
        
        logger.info(f"Detected {len(sections)} academic sections")
        return sections
    
    def _find_section_markers(self, text: str) -> List[Tuple[int, str, SectionType, float]]:
        """
        Find potential section markers in text.
        
        Returns:
            List of tuples: (position, header_text, section_type, confidence)
        """
        markers = []
        lines = text.split('\n')
        current_pos = 0
        
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                current_pos += len(line) + 1
                continue
            
            # Check each section type
            for section_type, patterns in self.section_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, line_stripped, re.IGNORECASE)
                    if match:
                        confidence = self._calculate_confidence(line_stripped, section_type, line_idx, len(lines))
                        markers.append((current_pos, line_stripped, section_type, confidence))
                        break
                if markers and markers[-1][0] == current_pos:  # Found match for this line
                    break
            
            current_pos += len(line) + 1
        
        # Sort by position and filter overlapping/low confidence markers
        markers.sort(key=lambda x: x[0])
        return self._filter_markers(markers)
    
    def _calculate_confidence(self, line: str, section_type: SectionType, line_idx: int, total_lines: int) -> float:
        """Calculate confidence score for a section marker."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for exact matches
        if line.lower().strip() in [section_type.value, section_type.value + 's']:
            confidence += 0.3
        
        # Boost confidence for numbered sections
        if re.match(r'^\s*\d+\.?\s*', line):
            confidence += 0.2
        
        # Boost confidence for standalone headers (short lines)
        if len(line.strip()) < 30:
            confidence += 0.2
        
        # Boost confidence for uppercase headers
        if line.strip().isupper():
            confidence += 0.1
        
        # Position-based confidence adjustments
        relative_pos = line_idx / total_lines
        if section_type == SectionType.ABSTRACT and relative_pos < 0.2:
            confidence += 0.2
        elif section_type == SectionType.INTRODUCTION and relative_pos < 0.3:
            confidence += 0.1
        elif section_type == SectionType.CONCLUSION and relative_pos > 0.7:
            confidence += 0.2
        elif section_type == SectionType.REFERENCES and relative_pos > 0.8:
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _filter_markers(self, markers: List[Tuple[int, str, SectionType, float]]) -> List[Tuple[int, str, SectionType, float]]:
        """Filter out low-confidence and overlapping markers."""
        if not markers:
            return []
        
        # Remove markers with very low confidence
        filtered = [m for m in markers if m[3] >= 0.4]
        
        # Remove duplicate section types, keeping highest confidence
        seen_types = {}
        for marker in filtered:
            section_type = marker[2]
            if section_type not in seen_types or marker[3] > seen_types[section_type][3]:
                seen_types[section_type] = marker
        
        result = list(seen_types.values())
        result.sort(key=lambda x: x[0])  # Sort by position
        return result
    
    def _create_sections_from_markers(self, text: str, markers: List[Tuple[int, str, SectionType, float]]) -> List[AcademicSection]:
        """Create section objects from detected markers."""
        sections = []
        
        for i, (pos, header, section_type, confidence) in enumerate(markers):
            start_pos = pos
            
            # Find end position (start of next section or end of text)
            if i + 1 < len(markers):
                end_pos = markers[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            
            # Remove the header from content
            lines = section_content.split('\n')
            if lines and header.lower() in lines[0].lower():
                section_content = '\n'.join(lines[1:]).strip()
            
            if len(section_content) >= self.min_section_length:
                sections.append(AcademicSection(
                    name=section_type.value.title(),
                    section_type=section_type,
                    content=section_content,
                    start_position=start_pos,
                    end_position=end_pos,
                    confidence=confidence
                ))
        
        return sections
    
    def _filter_references_section(self, sections: List[AcademicSection]) -> List[AcademicSection]:
        """Filter out or de-prioritize references section."""
        # Remove references section as specified in requirements
        filtered_sections = []
        references_section = None
        
        for section in sections:
            if section.section_type == SectionType.REFERENCES:
                references_section = section
                logger.info("References section detected and will be skipped")
            else:
                filtered_sections.append(section)
        
        return filtered_sections
    
    def _validate_sections(self, sections: List[AcademicSection]) -> List[AcademicSection]:
        """Validate and clean detected sections."""
        valid_sections = []
        
        for section in sections:
            # Check minimum length
            if len(section.content.strip()) < self.min_section_length:
                logger.debug(f"Skipping short section: {section.name}")
                continue
            
            # Check maximum length
            if len(section.content) > self.max_section_length:
                logger.warning(f"Truncating long section: {section.name}")
                section.content = section.content[:self.max_section_length] + "..."
            
            # Clean content
            section.content = self._clean_section_content(section.content)
            
            valid_sections.append(section)
        
        return valid_sections
    
    def _clean_section_content(self, content: str) -> str:
        """Clean section content."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        return content.strip()
    
    def _create_unknown_section(self, text: str, start: int, end: int) -> AcademicSection:
        """Create an unknown section for unstructured text."""
        content = text[start:end].strip() if text else ""
        
        return AcademicSection(
            name="Full Text",
            section_type=SectionType.UNKNOWN,
            content=content,
            start_position=start,
            end_position=end,
            confidence=1.0
        )
    
    def get_section_summary(self, sections: List[AcademicSection]) -> Dict[str, any]:
        """Get summary information about detected sections."""
        section_counts = {}
        total_length = 0
        
        for section in sections:
            section_type = section.section_type.value
            section_counts[section_type] = section_counts.get(section_type, 0) + 1
            total_length += len(section.content)
        
        return {
            "total_sections": len(sections),
            "section_types": list(section_counts.keys()),
            "section_counts": section_counts,
            "total_content_length": total_length,
            "average_section_length": total_length // len(sections) if sections else 0
        }