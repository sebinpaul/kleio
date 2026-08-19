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
from core.services.matching_engine import GenericMatchingEngine, MatchResult, MatchContext
from core.services.email_service import email_notification_service

logger = logging.getLogger(__name__)

# Constants for HackerNews Firebase API
class HNConstants:
    """Constants for HackerNews Firebase API integration"""
    FIREBASE_BASE_URL = "https://hacker-news.firebaseio.com/v0"
    MAX_ITEM_URL = f"{FIREBASE_BASE_URL}/maxitem.json"
    ITEM_URL = f"{FIREBASE_BASE_URL}/item/{{}}.json"
    HN_BASE_URL = "https://news.ycombinator.com"
    POLL_INTERVAL = 60  # seconds between maxitem checks
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
        self._cycle_mentions = 0
        
    def start_monitoring(self):
        """Start real-time monitoring by setting the start time"""
        self.monitoring_start_time = int(timezone.now().replace(tzinfo=dt_timezone.utc).timestamp())
        logger.debug("platform=hackernews monitoring start_time=%s", self.monitoring_start_time)
    
    def start_real_time_streaming(self, keywords: List[Keyword]):
        """Start real-time streaming of HackerNews items"""
        if self.is_streaming:
            logger.info("HackerNews streaming is already running")
            return
        
        self.is_streaming = True
        logger.info("platform=hackernews monitoring started keywords=%s", len(keywords))
        
        # Start streaming in a separate thread
        self.stream_thread = threading.Thread(
            target=self._run_streaming_loop,
            args=(keywords,),
            daemon=True
        )
        self.stream_thread.start()
    
    def stop_real_time_streaming(self):
        """Stop real-time streaming.

        The streaming thread owns the event loop and closes the aiohttp session in
        its finally block. After join(), the loop is already closed — never call
        run_coroutine_threadsafe on it here.
        """
        if not self.is_streaming and not (self.stream_thread and self.stream_thread.is_alive()):
            return

        self.is_streaming = False
        logger.info("platform=hackernews monitoring stopped")

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=15)

        self.stream_thread = None
        self.stream_loop = None
        self.session = None

    def _run_streaming_loop(self, keywords: List[Keyword]):
        """Run the async streaming loop in a separate thread"""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            self.stream_loop = loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._stream_hackernews_items(keywords))
        except Exception as e:
            logger.error("platform=hackernews streaming loop failed: %s", e)
        finally:
            try:
                if self.session and not self.session.closed and loop and not loop.is_closed():
                    loop.run_until_complete(self.session.close())
            except Exception:
                logger.debug("HN session close during shutdown failed", exc_info=True)
            self.session = None
            if loop and not loop.is_closed():
                loop.close()
            if self.stream_loop is loop:
                self.stream_loop = None
            self.is_streaming = False

    async def _stream_hackernews_items(self, keywords: List[Keyword]):
        """Stream all new HackerNews items and filter for keywords"""
        try:
            from aiohttp import ClientTimeout
            self.session = aiohttp.ClientSession(timeout=ClientTimeout(total=HNConstants.TIMEOUT))
            
            # Get current max item ID
            self.current_max_item = await self._fetch_max_item()
            logger.debug("platform=hackernews streaming from item_id=%s", self.current_max_item)
            
            while self.is_streaming:
                try:
                    await asyncio.sleep(HNConstants.POLL_INTERVAL)
                    started = time.time()
                    
                    # Get new max item ID
                    new_max_item = await self._fetch_max_item()
                    
                    if new_max_item > self.current_max_item:
                        new_items_count = new_max_item - self.current_max_item
                        self._cycle_mentions = 0
                        
                        # Process all new items
                        for item_id in range(self.current_max_item + 1, new_max_item + 1):
                            if not self.is_streaming:
                                break
                            
                            item = await self._fetch_item(item_id)
                            if item:
                                await self._process_item(item, keywords)
                        
                        self.current_max_item = new_max_item
                        logger.info(
                            "platform=hackernews poll completed items=%s mentions=%s duration_ms=%.0f",
                            new_items_count, self._cycle_mentions, (time.time() - started) * 1000,
                        )
                    else:
                        logger.debug(
                            "platform=hackernews poll completed items=0 duration_ms=%.0f",
                            (time.time() - started) * 1000,
                        )
                    
                except Exception as e:
                    logger.error("platform=hackernews poll failed: %s", e)
                    await asyncio.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            logger.error("platform=hackernews streaming setup failed: %s", e)
        # Session closed by _run_streaming_loop finally (owns the loop lifecycle).
    async def _fetch_max_item(self) -> int:
        """Fetch the current maximum item ID"""
        try:
            start_time = time.time()
            
            async with self.session.get(HNConstants.MAX_ITEM_URL) as response:
                response.raise_for_status()
                max_item = await response.json()
                
                response_time = (time.time() - start_time) * 1000  # milliseconds
                
                logger.debug("platform=hackernews maxitem=%s took_ms=%.0f", max_item, response_time)
                return max_item
                
        except Exception as e:
            logger.error("platform=hackernews maxitem request failed: %s", e)
            return self.current_max_item or 0
    
    async def _fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific item by ID"""
        try:
            url = HNConstants.ITEM_URL.format(item_id)
            start_time = time.time()
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                item = await response.json()
                
                response_time = (time.time() - start_time) * 1000  # milliseconds
                
                if item:
                    logger.debug(
                        "platform=hackernews item id=%s type=%s author=%s took_ms=%.0f",
                        item_id, item.get("type", "unknown"), item.get("by", "unknown"), response_time,
                    )
                else:
                    logger.debug("platform=hackernews item id=%s null took_ms=%.0f", item_id, response_time)
                
                return item if item else None
                
        except Exception as e:
            logger.error("platform=hackernews item id=%s request failed: %s", item_id, e)
            return None
    
    async def _process_item(self, item: Dict[str, Any], keywords: List[Keyword]):
        """Process a single HackerNews item and check for keyword matches"""
        try:
            item_type = item.get("type")
            item_time = item.get("time", 0)
            item_id = item.get("id")
            
            # Skip items created before monitoring started
            if item_time < self.monitoring_start_time:
                logger.debug("platform=hackernews skip id=%s created=%s start=%s", item_id, item_time, self.monitoring_start_time)
                return
            
            logger.debug("platform=hackernews processing id=%s type=%s", item_id, item_type)
            
            if item_type == "story":
                await self._process_story(item, keywords)
            elif item_type == "comment":
                await self._process_comment(item, keywords)
            else:
                logger.debug("platform=hackernews unknown item type=%s id=%s", item_type, item_id)
                
        except Exception as e:
            logger.error("platform=hackernews processing id=%s failed: %s", item.get('id'), e)
    
    async def _process_story(self, story: Dict[str, Any], keywords: List[Keyword]):
        """Process a story and check for keyword matches"""
        story_id = story.get("id")
        story_title = story.get("title", "")
        story_author = story.get("by", "")
        story_url = story.get("url", "")
        
        logger.debug("platform=hackernews story id=%s author=%s", story_id, story_author)
        
        for keyword in keywords:
            if not self._should_process_keyword(keyword, ContentType.TITLES.value):
                continue
            
            # Check title
            context = MatchContext(author=story_author)
            match_result = self.matching_engine.should_create_mention(
                keyword, story_title, ContentType.TITLES.value, context
            )
            
            if match_result:
                mention = self._create_mention_from_story(keyword, story, match_result, MentionContentType.TITLE.value)
                if mention:
                    await self._save_mention(mention, keyword)
            
            # Check URL/body if keyword monitors body content
            if self._should_process_keyword(keyword, ContentType.BODY.value):
                if story_url:
                    context = MatchContext(author=story_author)
                    match_result = self.matching_engine.should_create_mention(
                        keyword, story_url, ContentType.BODY.value, context
                    )
                    if match_result:
                        mention = self._create_mention_from_story(keyword, story, match_result, MentionContentType.BODY.value)
                        if mention:
                            await self._save_mention(mention, keyword)
    
    async def _process_comment(self, comment: Dict[str, Any], keywords: List[Keyword]):
        """Process a comment and check for keyword matches"""
        comment_id = comment.get("id")
        comment_text = comment.get("text", "")
        comment_author = comment.get("by", "")
        comment_parent = comment.get("parent", "")
        
        logger.debug("platform=hackernews comment id=%s author=%s parent=%s", comment_id, comment_author, comment_parent)
        
        for keyword in keywords:
            if not self._should_process_keyword(keyword, ContentType.COMMENTS.value):
                continue
            context = MatchContext(author=comment_author)
            match_result = self.matching_engine.should_create_mention(
                keyword, comment_text, ContentType.COMMENTS.value, context
            )
            
            if match_result:
                mention = self._create_mention_from_comment(keyword, comment, match_result)
                if mention:
                    await self._save_mention(mention, keyword)
    
    def _should_process_keyword(self, keyword: Keyword, content_type: str) -> bool:
        """Check if keyword should process this content type"""
        return (keyword.platform in [Platform.HACKERNEWS.value, Platform.ALL.value] and
                self.matching_engine.should_monitor_content(keyword, content_type))
    
    async def _save_mention(self, mention: Mention, keyword: Keyword, content_type: str = ""):
        """Save mention and send notification"""
        try:
            mention.save()
            self._cycle_mentions += 1
            logger.info(
                "platform=hackernews mention created keyword='%s' type=%s id=%s",
                keyword.keyword, content_type or mention.content_type, mention.id,
            )
            
            # Send email notification
            success = email_notification_service.send_mention_notification(mention)
            if not success:
                logger.error("platform=hackernews email failed mention=%s", mention.id)
                
        except Exception as e:
            logger.error("platform=hackernews mention save failed: %s", e)
    
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
                detected_language=getattr(match_result, 'detected_language', '') or '',
                mention_date=datetime.fromtimestamp(story.get("time", time.time())),
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = str(story['id'])
            mention.platform_score = story.get("score", 0)
            mention.platform_comments_count = story.get("descendants", 0)
            
            return mention
            
        except Exception as e:
            logger.error("platform=hackernews mention build failed (story): %s", e)
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
                detected_language=getattr(match_result, 'detected_language', '') or '',
                mention_date=datetime.fromtimestamp(comment.get("time", time.time())),
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = str(comment['id'])
            
            return mention
            
        except Exception as e:
            logger.error("platform=hackernews mention build failed (comment): %s", e)
            return None


