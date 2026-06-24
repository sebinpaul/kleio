import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from ..enums import (
    MatchMode, CaseSensitivity, ContentType, MentionContentType,
    PLATFORM_CONTENT_MAPPING
)

from .language_detection import detect_language

logger = logging.getLogger(__name__)


@dataclass
class MatchContext:
    author: str = ""
    subreddit: str = ""
    language: str = ""
    source_label: str = ""


class MatchResult:
    """Result of a keyword match"""
    
    def __init__(self, matched: bool, matched_text: str = "", position: int = -1, confidence: float = 1.0,
                 detected_language: str = ""):
        self.matched = matched
        self.matched_text = matched_text
        self.position = position
        self.confidence = confidence
        self.detected_language = detected_language
    
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
        content_types = keyword_obj.content_types or []
        return content_type in content_types

    def _normalize_handle(self, value: str) -> str:
        return (value or "").strip().lower().lstrip('@').lstrip('r/')

    def _keyword_has_language_filters(self, keyword_obj) -> bool:
        included = getattr(keyword_obj, 'included_languages', None) or []
        excluded = getattr(keyword_obj, 'excluded_languages', None) or []
        return bool(included or excluded)

    def _resolve_context_language(
        self,
        keyword_obj,
        content: str,
        context: Optional[MatchContext],
    ) -> MatchContext:
        if context is None:
            context = MatchContext()
        if context.language or not self._keyword_has_language_filters(keyword_obj):
            return context
        if content:
            context.language = detect_language(content)
        return context

    def _normalize_language(self, value: str) -> str:
        return (value or "").strip().lower()[:2]

    def _text_contains_term(self, content: str, term: str, case_sensitive: bool) -> bool:
        if not content or not term:
            return False
        if case_sensitive:
            return term in content
        return term.lower() in content.lower()

    def has_excluded_keywords(self, keyword_obj, content: str) -> bool:
        excluded = getattr(keyword_obj, 'excluded_keywords', None) or []
        if not excluded or not content:
            return False
        case_sensitive = bool(getattr(keyword_obj, 'case_sensitive', False))
        return any(
            self._text_contains_term(content, term, case_sensitive)
            for term in excluded
            if term
        )

    def passes_context_filters(self, keyword_obj, context: Optional[MatchContext]) -> bool:
        if context is None:
            return True

        subreddit = self._normalize_handle(context.subreddit)
        excluded_subreddits = getattr(keyword_obj, 'excluded_subreddits', None) or []
        if subreddit and excluded_subreddits:
            excluded = {self._normalize_handle(item) for item in excluded_subreddits}
            if subreddit in excluded:
                return False

        author = self._normalize_handle(context.author)
        included_users = getattr(keyword_obj, 'included_users', None) or []
        if included_users:
            allowed = {self._normalize_handle(item) for item in included_users}
            if not author or author not in allowed:
                return False

        excluded_users = getattr(keyword_obj, 'excluded_users', None) or []
        if author and excluded_users:
            blocked = {self._normalize_handle(item) for item in excluded_users}
            if author in blocked:
                return False

        language = self._normalize_language(context.language)
        included_languages = getattr(keyword_obj, 'included_languages', None) or []
        if included_languages:
            if not language:
                return False
            allowed_langs = {self._normalize_language(item) for item in included_languages}
            if language not in allowed_langs:
                return False

        excluded_languages = getattr(keyword_obj, 'excluded_languages', None) or []
        if language and excluded_languages:
            blocked_langs = {self._normalize_language(item) for item in excluded_languages}
            if language in blocked_langs:
                return False

        platform_filters = getattr(keyword_obj, 'platform_specific_filters', None) or []
        if platform_filters and context.source_label:
            allowed_sources = {self._normalize_handle(item) for item in platform_filters}
            source = self._normalize_handle(context.source_label)
            if source not in allowed_sources:
                return False

        return True

    def should_create_mention(
        self,
        keyword_obj,
        content: str,
        content_type: str,
        context: Optional[MatchContext] = None,
    ) -> MatchResult:
        if not self.should_monitor_content(keyword_obj, content_type):
            return MatchResult(matched=False)

        context = self._resolve_context_language(keyword_obj, content, context)
        if not self.passes_context_filters(keyword_obj, context):
            return MatchResult(matched=False)

        match_result = self.match_keyword(keyword_obj, content, content_type)
        if not match_result:
            return match_result
        if context:
            match_result.detected_language = context.language or ""
        if self.has_excluded_keywords(keyword_obj, content):
            return MatchResult(matched=False)
        return match_result 