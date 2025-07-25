import logging
import requests
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Dict, Optional, Any
from django.utils import timezone
from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine, MatchResult
from core.services.email_service import email_notification_service

logger = logging.getLogger(__name__)

# Constants for HackerNews API
class HNConstants:
    """Constants for HackerNews API integration"""
    ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
    ALGOLIA_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"
    FIREBASE_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
    HN_BASE_URL = "https://news.ycombinator.com"
    RATE_LIMIT_DELAY = 1  # seconds between requests
    MAX_RETRIES = 3
    TIMEOUT = 30  # seconds

class HackerNewsService:
    """Service for monitoring HackerNews for keyword mentions"""
    
    def __init__(self):
        self.matching_engine = GenericMatchingEngine()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'KleioBot/1.0 (HackerNews Monitoring)'
        })
        # Track monitoring start time for real-time updates
        self.monitoring_start_time = None
    
    def start_monitoring(self):
        """Start real-time monitoring by setting the start time"""
        self.monitoring_start_time = int(timezone.now().replace(tzinfo=dt_timezone.utc).timestamp())
        logger.info(f"Started HackerNews monitoring at timestamp: {self.monitoring_start_time}")
    
    def monitor_keywords(self, keywords: List[Keyword]) -> List[Mention]:
        """
        Monitor HackerNews for keyword mentions
        
        Args:
            keywords: List of Keyword objects to monitor
            
        Returns:
            List of new Mention objects found
        """
        mentions = []
        
        # Initialize monitoring start time if not set
        if self.monitoring_start_time is None:
            self.start_monitoring()
        
        for keyword in keywords:
            if keyword.platform in [Platform.HACKERNEWS.value, Platform.ALL.value]:
                try:
                    logger.info(f"Monitoring HN for keyword: {keyword.keyword}")
                    
                    hn_mentions = self._search_hn_content(keyword)
                    mentions.extend(hn_mentions)
                    
                    logger.info(f"Found {len(hn_mentions)} mentions for keyword: {keyword.keyword}")
                    
                except Exception as e:
                    logger.error(f"Error monitoring keyword {keyword.keyword}: {str(e)}")
                    continue
        
        return mentions
    
    def reset_monitoring(self):
        """Reset monitoring start time (useful for testing)"""
        self.monitoring_start_time = None
        logger.info("Reset HackerNews monitoring - will start fresh on next run")
    
    def _extract_story_ids_from_filters(self, filters: List[str]) -> List[str]:
        story_ids = []
        for filter_item in filters or []:
            if 'news.ycombinator.com/item?id=' in filter_item:
                try:
                    story_id = filter_item.split('id=')[1].split('&')[0]
                    story_ids.append(story_id)
                except (IndexError, ValueError):
                    logger.warning(f"Invalid HN URL format: {filter_item}")
            elif filter_item.isdigit():
                story_ids.append(filter_item)
        return story_ids

    def _search_hn_content(self, keyword: Keyword) -> List[Mention]:
        """Search for keyword mentions in HackerNews stories and comments"""
        mentions = []
        
        try:
            url_filters = self._extract_story_ids_from_filters(keyword.platform_specific_filters)
            
            # Use monitoring start time for real-time updates
            # This ensures we only get content created after monitoring started
            start_time = self.monitoring_start_time
            logger.info(f"Getting HN content created after start time: {start_time}")
            
            search_params = {
                'query': keyword.keyword,
                'tags': '(story,comment)',
                'hitsPerPage': 50,
                'numericFilters': f'created_at_i>{start_time}'
            }
            
            response = self._make_api_request(HNConstants.ALGOLIA_SEARCH_BY_DATE_URL, params=search_params)
            
            if response and 'hits' in response:
                logger.info(f"Found {len(response['hits'])} total items, checking for keyword matches...")
                for item in response['hits']:
                    if url_filters and item.get('objectID') not in url_filters:
                        continue
                    if item.get('_tags', []) and 'story' in item['_tags']:
                        mention = self._create_mention_from_story(keyword, item)
                    elif item.get('_tags', []) and 'comment' in item['_tags']:
                        mention = self._create_mention_from_comment(keyword, item)
                    else:
                        continue
                    if mention:
                        mentions.append(mention)
                        
        except Exception as e:
            logger.error(f"Error searching HN content for keyword {keyword.keyword}: {str(e)}")
        
        return mentions
    
    def _create_mention_from_story(self, keyword: Keyword, story: Dict[str, Any]) -> Optional[Mention]:
        """Create a Mention object from a HackerNews story"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={story['objectID']}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Check content types that the keyword is monitoring
            content_types_to_check = [ContentType.TITLES.value, ContentType.BODY.value]
            
            for content_type in content_types_to_check:
                if not self.matching_engine.should_monitor_content(keyword, content_type):
                    continue
                
                # Extract content based on type
                if content_type == ContentType.TITLES.value:
                    content = story.get('title', '')
                elif content_type == ContentType.BODY.value:
                    content = story.get('text', '') or story.get('url', '')
                
                # Match keyword against content
                match_result = self.matching_engine.match_keyword(keyword, content, content_type)
                
                if match_result:
                    mention = Mention(
                        keyword_id=str(keyword.id),
                        user_id=keyword.user_id,
                        content=content,
                        title=story.get('title', ''),
                        author=story.get('author', ''),
                        source_url=f"{HNConstants.HN_BASE_URL}/item?id={story['objectID']}",
                        platform=Platform.HACKERNEWS.value,
                        platform_specific_location='hackernews',  # Use consistent field name
                        content_type=self._map_content_type_to_mention_type(content_type),
                        matched_text=match_result.matched_text,
                        match_position=match_result.position,
                        match_confidence=match_result.confidence,
                        mention_date=datetime.fromtimestamp(story.get('created_at_i', time.time())),
                        discovered_at=timezone.now()
                    )
                    
                    # Add HN-specific fields
                    mention.hn_story_id = story['objectID']
                    mention.hn_points = story.get('points', 0)
                    mention.hn_comments_count = story.get('num_comments', 0)
                    
                    return mention
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating mention from story: {str(e)}")
            return None
    
    def _create_mention_from_comment(self, keyword: Keyword, comment: Dict[str, Any]) -> Optional[Mention]:
        """Create a Mention object from a HackerNews comment"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={comment['objectID']}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Check if keyword monitors comments
            if not self.matching_engine.should_monitor_content(keyword, ContentType.COMMENTS.value):
                return None
            
            content = comment.get('text', '')
            
            # Match keyword against comment content
            match_result = self.matching_engine.match_keyword(keyword, content, ContentType.COMMENTS.value)
            
            if match_result:
                mention = Mention(
                    keyword_id=str(keyword.id),
                    user_id=keyword.user_id,
                    content=content,
                    title=f"Comment on: {comment.get('story_title', 'Unknown Story')}",
                    author=comment.get('author', ''),
                    source_url=f"{HNConstants.HN_BASE_URL}/item?id={comment['objectID']}",
                    platform=Platform.HACKERNEWS.value,
                    platform_specific_location='hackernews',  # Use consistent field name
                    content_type=MentionContentType.COMMENT.value,
                    matched_text=match_result.matched_text,
                    match_position=match_result.position,
                    match_confidence=match_result.confidence,
                    mention_date=datetime.fromtimestamp(comment.get('created_at_i', time.time())),
                    discovered_at=timezone.now()
                )
                
                # Add HN-specific fields
                mention.hn_comment_id = comment['objectID']
                mention.hn_story_id = comment.get('story_id')
                
                return mention
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating mention from comment: {str(e)}")
            return None
    
    def _map_content_type_to_mention_type(self, content_type: str) -> str:
        """Map content type to mention content type"""
        mapping = {
            ContentType.TITLES.value: MentionContentType.TITLE.value,
            ContentType.BODY.value: MentionContentType.BODY.value,
            ContentType.COMMENTS.value: MentionContentType.COMMENT.value,
        }
        return mapping.get(content_type, MentionContentType.TITLE.value)
    
    def _make_api_request(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic and rate limiting"""
        for attempt in range(HNConstants.MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=HNConstants.TIMEOUT
                )
                response.raise_for_status()
                
                # Rate limiting
                time.sleep(HNConstants.RATE_LIMIT_DELAY)
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}/{HNConstants.MAX_RETRIES}): {str(e)}")
                if attempt < HNConstants.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"API request failed after {HNConstants.MAX_RETRIES} attempts")
                    return None
        
        return None
    
    def get_recent_stories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent HackerNews stories for testing"""
        try:
            # Use UTC time for HackerNews API (which expects UTC timestamps)
            utc_now = timezone.now().replace(tzinfo=dt_timezone.utc)
            one_day_ago = utc_now - timedelta(hours=24)
            
            search_params = {
                'tags': 'story',
                'hitsPerPage': limit,
                'numericFilters': f'created_at_i>{int(one_day_ago.timestamp())}'
            }
            
            response = self._make_api_request(HNConstants.ALGOLIA_SEARCH_URL, params=search_params)
            
            if response and 'hits' in response:
                return response['hits']
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent stories: {str(e)}")
            return []
