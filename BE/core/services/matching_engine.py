import re
import logging
from typing import List, Dict, Optional, Tuple
from ..enums import (
    MatchMode, CaseSensitivity, ContentType, MentionContentType,
    PLATFORM_CONTENT_MAPPING
)

logger = logging.getLogger(__name__)


class MatchResult:
    """Result of a keyword match"""
    
    def __init__(self, matched: bool, matched_text: str = "", position: int = -1, confidence: float = 1.0):
        self.matched = matched
        self.matched_text = matched_text
        self.position = position
        self.confidence = confidence
    
    def __bool__(self):
        return self.matched


class GenericMatchingEngine:
    """Platform-agnostic keyword matching engine"""
    
    def __init__(self):
        self.case_modes = {
            CaseSensitivity.CASE_INSENSITIVE.value: lambda text: text.lower(),
            CaseSensitivity.CASE_SENSITIVE.value: lambda text: text,
            CaseSensitivity.SMART_CASE.value: self._smart_case_transform
        }
    
    def match_keyword(self, keyword_obj, content: str, content_type: str = ContentType.BODY.value) -> MatchResult:
        """
        Generic keyword matching logic
        
        Args:
            keyword_obj: Keyword model instance
            content: Text content to search in
            content_type: Type of content being searched
            
        Returns:
            MatchResult object with match details
        """
        try:
            # Check if content type is monitored
            if content_type not in keyword_obj.content_types:
                return MatchResult(matched=False)
            
            # Get keyword and matching settings
            keyword = keyword_obj.keyword
            match_mode = keyword_obj.match_mode
            case_sensitive = keyword_obj.case_sensitive
            
            # Apply case sensitivity
            case_mode = CaseSensitivity.CASE_SENSITIVE.value if case_sensitive else CaseSensitivity.CASE_INSENSITIVE.value
            transform_func = self.case_modes[case_mode]
            
            transformed_content = transform_func(content)
            transformed_keyword = transform_func(keyword)
            
            # Apply matching mode
            match_result = self._apply_matching_mode(
                transformed_content, 
                transformed_keyword, 
                match_mode,
                original_content=content,
                original_keyword=keyword
            )
            
            return match_result
            
        except Exception as e:
            logger.error(f"Error in keyword matching: {e}")
            return MatchResult(matched=False)
    
    def _apply_matching_mode(self, content: str, keyword: str, match_mode: str, 
                           original_content: str = "", original_keyword: str = "") -> MatchResult:
        """Apply specific matching mode"""
        
        if match_mode == MatchMode.EXACT.value:
            return self._exact_match(content, keyword, original_content, original_keyword)
        elif match_mode == MatchMode.CONTAINS.value:
            return self._contains_match(content, keyword, original_content, original_keyword)
        elif match_mode == MatchMode.WORD_BOUNDARY.value:
            return self._word_boundary_match(content, keyword, original_content, original_keyword)
        elif match_mode == MatchMode.STARTS_WITH.value:
            return self._starts_with_match(content, keyword, original_content, original_keyword)
        elif match_mode == MatchMode.ENDS_WITH.value:
            return self._ends_with_match(content, keyword, original_content, original_keyword)
        else:
            # Default to contains match
            return self._contains_match(content, keyword, original_content, original_keyword)
    
    def _exact_match(self, content: str, keyword: str, original_content: str, original_keyword: str) -> MatchResult:
        """Exact word match"""
        if content == keyword:
            return MatchResult(
                matched=True,
                matched_text=original_keyword,
                position=0,
                confidence=1.0
            )
        return MatchResult(matched=False)
    
    def _contains_match(self, content: str, keyword: str, original_content: str, original_keyword: str) -> MatchResult:
        """Contains match (default behavior)"""
        position = content.find(keyword)
        if position != -1:
            # Find the original text at this position
            original_matched = original_content[position:position + len(original_keyword)]
            return MatchResult(
                matched=True,
                matched_text=original_matched,
                position=position,
                confidence=1.0
            )
        return MatchResult(matched=False)
    
    def _word_boundary_match(self, content: str, keyword: str, original_content: str, original_keyword: str) -> MatchResult:
        """Word boundary match using regex"""
        try:
            # Create word boundary pattern
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, content)
            
            if match:
                start_pos = match.start()
                # Find corresponding position in original content
                original_matched = original_content[start_pos:start_pos + len(original_keyword)]
                return MatchResult(
                    matched=True,
                    matched_text=original_matched,
                    position=start_pos,
                    confidence=1.0
                )
            return MatchResult(matched=False)
        except Exception as e:
            logger.error(f"Error in word boundary match: {e}")
            return MatchResult(matched=False)
    
    def _starts_with_match(self, content: str, keyword: str, original_content: str, original_keyword: str) -> MatchResult:
        """Starts with match"""
        if content.startswith(keyword):
            return MatchResult(
                matched=True,
                matched_text=original_keyword,
                position=0,
                confidence=1.0
            )
        return MatchResult(matched=False)
    
    def _ends_with_match(self, content: str, keyword: str, original_content: str, original_keyword: str) -> MatchResult:
        """Ends with match"""
        if content.endswith(keyword):
            end_pos = len(content) - len(keyword)
            return MatchResult(
                matched=True,
                matched_text=original_keyword,
                position=end_pos,
                confidence=1.0
            )
        return MatchResult(matched=False)
    
    def _smart_case_transform(self, text: str) -> str:
        """Smart case transformation - preserve original case for display"""
        # For smart case, we'll use case-insensitive matching but preserve original
        return text.lower()
    
    def get_content_fields(self, platform: str, content_type: str) -> List[str]:
        """Get platform-specific content fields for a content type"""
        return PLATFORM_CONTENT_MAPPING.get(platform, {}).get(content_type, [])
    
    def extract_content_by_type(self, platform_obj, content_type: str) -> str:
        """
        Extract content from platform object based on content type
        
        Args:
            platform_obj: Platform-specific object (Reddit submission, HN item, etc.)
            content_type: Type of content to extract
            
        Returns:
            Extracted content as string
        """
        try:
            if hasattr(platform_obj, 'platform'):
                platform = platform_obj.platform
            else:
                # Default to reddit if platform not specified
                platform = 'reddit'
            
            fields = self.get_content_fields(platform, content_type)
            content_parts = []
            
            for field in fields:
                if hasattr(platform_obj, field):
                    value = getattr(platform_obj, field)
                    if value:
                        content_parts.append(str(value))
            
            return ' '.join(content_parts)
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ""
    
    def should_monitor_content(self, keyword_obj, content_type: str) -> bool:
        """Check if keyword should monitor this content type"""
        return content_type in keyword_obj.content_types 