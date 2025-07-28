import logging
import time
import asyncio
import aiohttp
import threading
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Dict, Optional, Any
from django.utils import timezone
from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine, MatchResult
from core.services.email_service import email_notification_service

logger = logging.getLogger(__name__)

# Constants for HackerNews Firebase API
class HNConstants:
    """Constants for HackerNews Firebase API integration"""
    FIREBASE_BASE_URL = "https://hacker-news.firebaseio.com/v0"
    MAX_ITEM_URL = f"{FIREBASE_BASE_URL}/maxitem.json"
    ITEM_URL = f"{FIREBASE_BASE_URL}/item/{{}}.json"
    HN_BASE_URL = "https://news.ycombinator.com"
    POLL_INTERVAL = 8  # seconds between maxitem checks
    MAX_RETRIES = 3
    TIMEOUT = 30  # seconds

class HackerNewsService:
    """Service for real-time monitoring HackerNews for keyword mentions using Firebase API"""
    
    def __init__(self):
        self.matching_engine = GenericMatchingEngine()
        self.monitoring_start_time = None
        self.current_max_item = None
        self.is_streaming = False
        self.stream_thread = None
        self.stream_loop = None
        self.session = None
        
    def start_monitoring(self):
        """Start real-time monitoring by setting the start time"""
        self.monitoring_start_time = int(timezone.now().replace(tzinfo=dt_timezone.utc).timestamp())
        logger.info(f"Started HackerNews monitoring at timestamp: {self.monitoring_start_time}")
    
    def start_real_time_streaming(self, keywords: List[Keyword]):
        """Start real-time streaming of HackerNews items"""
        if self.is_streaming:
            logger.info("HackerNews streaming is already running")
            return
        
        self.is_streaming = True
        logger.info(f"🚀 Starting real-time HackerNews streaming for {len(keywords)} keywords")
        
        # Start streaming in a separate thread
        self.stream_thread = threading.Thread(
            target=self._run_streaming_loop,
            args=(keywords,),
            daemon=True
        )
        self.stream_thread.start()
    
    def stop_real_time_streaming(self):
        """Stop real-time streaming"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        logger.info("⏹️ Stopping HackerNews real-time streaming")
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=10)
        
        if self.session:
            asyncio.run_coroutine_threadsafe(self.session.close(), self.stream_loop)
    
    def _run_streaming_loop(self, keywords: List[Keyword]):
        """Run the async streaming loop in a separate thread"""
        try:
            self.stream_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.stream_loop)
            self.stream_loop.run_until_complete(self._stream_hackernews_items(keywords))
        except Exception as e:
            logger.error(f"Error in streaming loop: {e}")
        finally:
            if self.stream_loop:
                self.stream_loop.close()
    
    async def _stream_hackernews_items(self, keywords: List[Keyword]):
        """Stream all new HackerNews items and filter for keywords"""
        try:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HNConstants.TIMEOUT))
            
            # Get current max item ID
            self.current_max_item = await self._fetch_max_item()
            logger.info(f"Starting HackerNews streaming from item ID: {self.current_max_item}")
            
            while self.is_streaming:
                try:
                    await asyncio.sleep(HNConstants.POLL_INTERVAL)
                    
                    # Get new max item ID
                    new_max_item = await self._fetch_max_item()
                    
                    if new_max_item > self.current_max_item:
                        new_items_count = new_max_item - self.current_max_item
                        logger.info(f"🆕 Found {new_items_count} new items! Processing items {self.current_max_item + 1} to {new_max_item}")
                        
                        # Process all new items
                        for item_id in range(self.current_max_item + 1, new_max_item + 1):
                            if not self.is_streaming:
                                break
                            
                            item = await self._fetch_item(item_id)
                            if item:
                                await self._process_item(item, keywords)
                        
                        self.current_max_item = new_max_item
                        logger.info(f"✅ Completed processing {new_items_count} new items")
                    else:
                        logger.debug(f"📊 No new items found. Current max: {self.current_max_item}, Latest max: {new_max_item}")
                    
                except Exception as e:
                    logger.error(f"Error in streaming loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Error setting up streaming: {e}")
        finally:
            if self.session:
                await self.session.close()
    
    async def _fetch_max_item(self) -> int:
        """Fetch the current maximum item ID"""
        try:
            logger.info(f"🌐 Making API request to: {HNConstants.MAX_ITEM_URL}")
            start_time = time.time()
            
            async with self.session.get(HNConstants.MAX_ITEM_URL) as response:
                response.raise_for_status()
                max_item = await response.json()
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                logger.info(f"✅ MaxItem API response: {max_item} (took {response_time:.1f}ms)")
                return max_item
                
        except Exception as e:
            logger.error(f"❌ Error fetching max item: {e}")
            return self.current_max_item or 0
    
    async def _fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific item by ID"""
        try:
            url = HNConstants.ITEM_URL.format(item_id)
            logger.info(f"🌐 Making API request to: {url}")
            start_time = time.time()
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                item = await response.json()
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if item:
                    item_type = item.get("type", "unknown")
                    item_author = item.get("by", "unknown")
                    logger.info(f"✅ Item API response: ID={item_id}, Type={item_type}, Author={item_author} (took {response_time:.1f}ms)")
                else:
                    logger.warning(f"⚠️ Item API response: ID={item_id} is null (took {response_time:.1f}ms)")
                
                return item if item else None
                
        except Exception as e:
            logger.error(f"❌ Error fetching item {item_id}: {e}")
            return None
    
    async def _process_item(self, item: Dict[str, Any], keywords: List[Keyword]):
        "Process a single HackerNews item and check for keyword matches"""
        try:
            item_type = item.get("type")
            item_time = item.get("time", 0)
            item_id = item.get("id")
            
            # Skip items created before monitoring started
            if item_time < self.monitoring_start_time:
                logger.debug(f"⏭️ Skipping item {item_id} (created at {item_time}, monitoring started at {self.monitoring_start_time})")
                return
            
            logger.info(f"🔍 Processing item {item_id} (type: {item_type}, time: {item_time})")
            
            if item_type == "story":
                await self._process_story(item, keywords)
            elif item_type == "comment":
                await self._process_comment(item, keywords)
            else:
                logger.debug(f"⚠️ Unknown item type: {item_type} for item {item_id}")
                
        except Exception as e:
            logger.error(f"Error processing item {item.get('id')}: {e}")
    
    async def _process_story(self, story: Dict[str, Any], keywords: List[Keyword]):
        """Process a story and check for keyword matches"""
        story_id = story.get("id")
        story_title = story.get("title", "")
        story_author = story.get("by", "")
        story_url = story.get("url", "")
        
        logger.debug(f"📰 Processing story {story_id}: '{story_title}' by {story_author}")
        
        for keyword in keywords:
            if not self._should_process_keyword(keyword, ContentType.TITLES.value):
                continue
            
            # Check title
            match_result = self.matching_engine.match_keyword(keyword, story_title, ContentType.TITLES.value)
            
            if match_result:
                mention = self._create_mention_from_story(keyword, story, match_result, MentionContentType.TITLE.value)
                if mention:
                    await self._save_mention(mention, keyword)
                    logger.info(f"🎯 New story title mention! Keyword: '{keyword.keyword}' - '{story_title[:50]}...'")
            
            # Check URL/body if keyword monitors body content
            if self._should_process_keyword(keyword, ContentType.BODY.value):
                if story_url:
                    match_result = self.matching_engine.match_keyword(keyword, story_url, ContentType.BODY.value)
                    if match_result:
                        mention = self._create_mention_from_story(keyword, story, match_result, MentionContentType.BODY.value)
                        if mention:
                            await self._save_mention(mention, keyword)
                            logger.info(f"🎯 New story URL mention! Keyword: '{keyword.keyword}' - '{story_url[:50]}...'")
    
    async def _process_comment(self, comment: Dict[str, Any], keywords: List[Keyword]):
        """Process a comment and check for keyword matches"""
        comment_id = comment.get("id")
        comment_text = comment.get("text", "")
        comment_author = comment.get("by", "")
        comment_parent = comment.get("parent", "")
        
        logger.debug(f"💬 Processing comment {comment_id} by {comment_author} on parent {comment_parent}")
        
        for keyword in keywords:
            if not self._should_process_keyword(keyword, ContentType.COMMENTS.value):
                continue
            print(keyword, comment_text)
            match_result = self.matching_engine.match_keyword(keyword, comment_text, ContentType.COMMENTS.value)
            
            if match_result:
                mention = self._create_mention_from_comment(keyword, comment, match_result)
                if mention:
                    await self._save_mention(mention, keyword)
                    logger.info(f"🎯 New comment mention! Keyword: '{keyword.keyword}' - '{comment_text[:50]}...'")
    
    def _should_process_keyword(self, keyword: Keyword, content_type: str) -> bool:
        """Check if keyword should process this content type"""
        return (keyword.platform in [Platform.HACKERNEWS.value, Platform.ALL.value] and
                self.matching_engine.should_monitor_content(keyword, content_type))
    
    async def _save_mention(self, mention: Mention, keyword: Keyword):
        """Save mention and send notification"""
        try:
            mention.save()
            logger.info(f"💾 Saved HN mention: {mention.keyword_id} - {mention.title[:50]}...")
            
            # Send email notification
            success = email_notification_service.send_mention_notification(mention)
            if success:
                logger.info(f"📧 Email notification sent for mention {mention.id}")
            else:
                logger.error(f"Failed to send email notification for mention {mention.id}")
                
        except Exception as e:
            logger.error(f"Error saving mention: {e}")
    
    def _create_mention_from_story(self, keyword: Keyword, story: Dict[str, Any], match_result: MatchResult, content_type: str) -> Optional[Mention]:
        """Create a Mention object from a HackerNews story"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={story['id']}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=story.get("title", ""),
                title=story.get("title", ""),
                author=story.get("by", ""),
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={story['id']}",
                platform=Platform.HACKERNEWS.value,
                content_type=content_type,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                mention_date=datetime.fromtimestamp(story.get("time", time.time())),
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = str(story['id'])
            mention.platform_score = story.get("score", 0)
            mention.platform_comments_count = story.get("descendants", 0)
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from story: {str(e)}")
            return None
    
    def _create_mention_from_comment(self, keyword: Keyword, comment: Dict[str, Any], match_result: MatchResult) -> Optional[Mention]:
        """Create a Mention object from a HackerNews comment"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={comment['id']}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=comment.get("text", ""),
                title=f"Comment on item {comment.get('parent', 'Unknown')}",
                author=comment.get("by", ""),
                source_url=f"{HNConstants.HN_BASE_URL}/item?id={comment['id']}",
                platform=Platform.HACKERNEWS.value,
                content_type=MentionContentType.COMMENT.value,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                mention_date=datetime.fromtimestamp(comment.get("time", time.time())),
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = str(comment['id'])
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from comment: {str(e)}")
            return None
    
    # Legacy methods for backward compatibility
    def monitor_keywords(self, keywords: List[Keyword]) -> List[Mention]:
        """Legacy method - now uses real-time streaming"""
        logger.info("Using real-time streaming instead of periodic monitoring")
        return []
    
    def reset_monitoring(self):
        """Reset monitoring start time (useful for testing)"""
        self.monitoring_start_time = None
        logger.info("Reset HackerNews monitoring - will start fresh on next run")
    
    def get_recent_stories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent HackerNews stories for testing (legacy method)"""
        logger.warning("get_recent_stories is deprecated - use real-time streaming instead")
        return []
