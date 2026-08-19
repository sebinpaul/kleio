import os
import logging
import threading
import time
from datetime import datetime, timezone as dt_timezone
from typing import List, Dict, Optional
import praw
from praw.models import Subreddit
from django.utils import timezone
from .reddit_service import RedditService
from core.services.matching_engine import GenericMatchingEngine, MatchResult, MatchContext
from core.services.email_service import email_notification_service
from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType

logger = logging.getLogger(__name__)

# PRAW streams are request-based under the hood. pause_after=-1 yields None after
# each listing response so we can enforce a fixed poll interval.
REDDIT_POLL_INTERVAL_SECS = 60


class RealtimeStreamMonitor:
    """Manages real-time monitoring of Reddit streams for keyword mentions"""
    
    def __init__(self):
        self.reddit = None
        self.stop_monitoring = False
        self.monitoring_threads = []
        self.matching_engine = GenericMatchingEngine()
        self.monitoring_start_time = None
        self.poll_interval = REDDIT_POLL_INTERVAL_SECS
    
    def start_stream_monitoring(self, keywords=None):
        """Start monitoring Reddit streams for keyword mentions"""
        self.monitoring_start_time = int(timezone.now().replace(tzinfo=dt_timezone.utc).timestamp())
        logger.debug("platform=reddit monitoring start_time=%s", self.monitoring_start_time)
        try:
            self.stop_monitoring = False
            
            # Initialize Reddit client
            if not self.reddit:
                self.reddit = praw.Reddit(
                    client_id=os.environ.get('REDDIT_CLIENT_ID'),
                    client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
                    user_agent=os.environ.get('REDDIT_USER_AGENT', 'KleioBot/1.0'),
                )
            
            # Get keywords to monitor
            if keywords is None:
                keywords = Keyword.objects.filter(is_active=True)
            
            if not keywords:
                logger.debug("platform=reddit no active keywords to monitor")
                return
            
            # Group keywords by subreddit
            subreddit_keywords = self._group_keywords_by_subreddit(keywords)
            
            # Start monitoring each subreddit
            for subreddit_name, keywords_list in subreddit_keywords.items():
                if self.stop_monitoring:
                    break
                
                thread = threading.Thread(
                    target=self._monitor_subreddit_stream,
                    args=(subreddit_name, keywords_list),
                    daemon=True
                )
                thread.start()
                self.monitoring_threads.append(thread)
                logger.debug("platform=reddit monitoring r/%s keywords=%s", subreddit_name, len(keywords_list))
            
            logger.info(
                "platform=reddit monitoring started subreddits=%s keywords=%s",
                len(subreddit_keywords), len(keywords),
            )
            
        except Exception as e:
            logger.error("platform=reddit monitoring start failed: %s", e)
    
    def stop_stream_monitoring(self):
        """Stop all monitoring threads"""
        self.stop_monitoring = True
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        self.monitoring_threads.clear()
        logger.info("platform=reddit monitoring stopped")
    
    def _group_keywords_by_subreddit(self, keywords):
        """Group keywords by subreddit for efficient monitoring"""
        subreddit_keywords = {}
        
        for keyword in keywords:
            if keyword.platform in [Platform.REDDIT.value, Platform.ALL.value]:
                # Get subreddit filters for this keyword
                subreddits = keyword.platform_specific_filters if keyword.platform_specific_filters else ['all']
                
                for subreddit in subreddits:
                    if subreddit not in subreddit_keywords:
                        subreddit_keywords[subreddit] = []
                    subreddit_keywords[subreddit].append(keyword)
        
        return subreddit_keywords
    
    def _monitor_subreddit_stream(self, subreddit_name, keywords):
        """Monitor a specific subreddit for mentions"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Start both submissions and comments monitoring in separate threads
            submissions_thread = threading.Thread(
                target=self._monitor_submissions_stream,
                args=(subreddit, keywords),
                daemon=True
            )
            comments_thread = threading.Thread(
                target=self._monitor_comments_stream,
                args=(subreddit, keywords),
                daemon=True
            )
            
            submissions_thread.start()
            comments_thread.start()

            self.monitoring_threads.extend([submissions_thread, comments_thread])

            logger.debug("platform=reddit streams started r/%s keywords=%s", subreddit_name, len(keywords))
        except Exception as e:
            logger.error("platform=reddit monitor r/%s failed: %s", subreddit_name, e)
    
    def _monitor_submissions_stream(self, subreddit, keywords):
        """Monitor submissions stream for mentions (reconnects after errors / rate limits)."""
        backoff_secs = self.poll_interval
        max_backoff_secs = 600
        while not self.stop_monitoring:
            try:
                # Refresh client in case a prior 429 left it in a bad state
                if not self.reddit:
                    self._rotate_reddit_client()
                live_subreddit = self.reddit.subreddit(subreddit.display_name)
                logger.debug(
                    "platform=reddit submissions stream r/%s poll_interval=%ss",
                    live_subreddit.display_name, self.poll_interval,
                )

                for submission in live_subreddit.stream.submissions(
                    skip_existing=True, pause_after=-1
                ):
                    if self.stop_monitoring:
                        break
                    if submission is None:
                        # End of this listing response — wait before the next Reddit poll.
                        time.sleep(self.poll_interval)
                        continue
                    self._check_submission_for_keywords(submission, keywords)
                    backoff_secs = self.poll_interval

            except Exception as e:
                logger.error("platform=reddit submissions stream r/%s failed: %s", subreddit.display_name, e)
                self._rotate_reddit_client()
                if self.stop_monitoring:
                    break
                logger.warning(
                    "platform=reddit submissions stream r/%s reconnect in %ss", subreddit.display_name, backoff_secs
                )
                time.sleep(backoff_secs)
                backoff_secs = min(backoff_secs * 2, max_backoff_secs)

    def _monitor_comments_stream(self, subreddit, keywords):
        """Monitor comments stream for mentions (reconnects after errors / rate limits)."""
        backoff_secs = self.poll_interval
        max_backoff_secs = 600
        while not self.stop_monitoring:
            try:
                if not self.reddit:
                    self._rotate_reddit_client()
                live_subreddit = self.reddit.subreddit(subreddit.display_name)
                logger.debug(
                    "platform=reddit comments stream r/%s poll_interval=%ss",
                    live_subreddit.display_name, self.poll_interval,
                )

                for comment in live_subreddit.stream.comments(
                    skip_existing=True, pause_after=-1
                ):
                    if self.stop_monitoring:
                        break
                    if comment is None:
                        time.sleep(self.poll_interval)
                        continue
                    self._check_comment_for_keywords(comment, keywords)
                    backoff_secs = self.poll_interval

            except Exception as e:
                logger.error("platform=reddit comments stream r/%s failed: %s", subreddit.display_name, e)
                self._rotate_reddit_client()
                if self.stop_monitoring:
                    break
                logger.warning(
                    "platform=reddit comments stream r/%s reconnect in %ss", subreddit.display_name, backoff_secs
                )
                time.sleep(backoff_secs)
                backoff_secs = min(backoff_secs * 2, max_backoff_secs)
 
    def _check_submission_for_keywords(self, submission, keywords):
        """Check if a submission matches any keywords"""
        try:
            # Check each content type that keywords might be monitoring
            content_types_to_check = [ContentType.TITLES.value, ContentType.BODY.value]
            
            for content_type in content_types_to_check:
                # Extract content based on type
                if content_type == ContentType.TITLES.value:
                    content = submission.title
                elif content_type == ContentType.BODY.value:
                    content = submission.selftext or ""
                
                # Check each keyword against this content
                for keyword in keywords:
                    context = MatchContext(
                        author=str(submission.author) if submission.author else '',
                        subreddit=submission.subreddit.display_name,
                    )
                    match_result = self.matching_engine.should_create_mention(
                        keyword, content, content_type, context
                    )
                    
                    if match_result:
                        # Determine mention content type
                        mention_content_type = self._map_content_type_to_mention_type(content_type)
                        
                        mention = self._create_mention_from_submission(
                            keyword, submission, match_result, mention_content_type
                        )
                        if mention:
                            try:
                                mention.save()
                                logger.info(
                                    "platform=reddit mention created keyword='%s' type=%s subreddit=r/%s",
                                    keyword.keyword, mention_content_type, submission.subreddit.display_name,
                                )
                                
                                # Send email notification
                                self._send_email_notification(mention, keyword)
                                
                            except Exception as e:
                                logger.error("platform=reddit mention save failed: %s", e)
        
        except Exception as e:
            logger.error("platform=reddit submission check failed: %s", e)
    
    def _check_comment_for_keywords(self, comment, keywords):
        """Check if a comment matches any keywords"""
        try:
            # Check comments content type
            content = comment.body
            
            for keyword in keywords:
                context = MatchContext(
                    author=str(comment.author) if comment.author else '',
                    subreddit=comment.subreddit.display_name,
                )
                match_result = self.matching_engine.should_create_mention(
                    keyword, content, ContentType.COMMENTS.value, context
                )
                
                if match_result:
                    mention = self._create_mention_from_comment(keyword, comment, match_result)
                    if mention:
                        try:
                            mention.save()
                            logger.info(
                                "platform=reddit mention created keyword='%s' type=comment subreddit=r/%s",
                                keyword.keyword, comment.subreddit.display_name,
                            )
                            
                            # Send email notification
                            self._send_email_notification(mention, keyword)
                            
                        except Exception as e:
                            logger.error("platform=reddit mention save failed: %s", e)
        
        except Exception as e:
            logger.error("platform=reddit comment check failed: %s", e)
    
    def _send_email_notification(self, mention, keyword):
        """Send email notification for a new mention"""
        try:
            # Send email notification using the service
            success = email_notification_service.send_mention_notification(mention)
            if not success:
                logger.error("platform=reddit email failed mention=%s", mention.id)
                
        except Exception as e:
            logger.error("platform=reddit email notification failed: %s", e)
    

    
    def _create_mention_from_submission(self, keyword, submission, match_result: MatchResult, content_type: str):
        """Create a Mention object from a Reddit submission"""
        try:
            # Check if mention already exists
            existing_mention = Mention.objects.filter(
                source_url=f"https://reddit.com{submission.permalink}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=submission.selftext or submission.title,
                title=submission.title,
                author=str(submission.author) if submission.author else '[deleted]',
                source_url=f"https://reddit.com{submission.permalink}",
                platform=Platform.REDDIT.value,
                subreddit=submission.subreddit.display_name,
                content_type=content_type,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                detected_language=getattr(match_result, 'detected_language', '') or '',
                mention_date=datetime.fromtimestamp(submission.created_utc)
            )
            

            
            return mention
            
        except Exception as e:
            logger.error("platform=reddit mention build failed (submission): %s", e)
            return None
    
    def _create_mention_from_comment(self, keyword, comment, match_result: MatchResult):
        """Create a Mention object from a Reddit comment"""
        try:
            # Check if mention already exists
            existing_mention = Mention.objects.filter(
                source_url=f"https://reddit.com{comment.permalink}",
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=comment.body,
                title=f"Comment on: {comment.submission.title if hasattr(comment, 'submission') else 'Unknown'}",
                author=str(comment.author) if comment.author else '[deleted]',
                source_url=f"https://reddit.com{comment.permalink}",
                platform=Platform.REDDIT.value,
                subreddit=comment.subreddit.display_name,
                content_type=MentionContentType.COMMENT.value,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                detected_language=getattr(match_result, 'detected_language', '') or '',
                mention_date=datetime.fromtimestamp(comment.created_utc)
            )
            

            
            return mention
            
        except Exception as e:
            logger.error("platform=reddit mention build failed (comment): %s", e)
            return None
    
    def _map_content_type_to_mention_type(self, content_type: str) -> str:
        """Map content type to mention content type"""
        mapping = {
            ContentType.COMMENTS.value: MentionContentType.COMMENT.value,
            ContentType.TITLES.value: MentionContentType.TITLE.value,
            ContentType.BODY.value: MentionContentType.BODY.value,
        }
        return mapping.get(content_type, MentionContentType.TITLE.value)

    def _rotate_reddit_client(self):
        try:
            self.reddit = praw.Reddit(
                client_id=os.environ.get('REDDIT_CLIENT_ID'),
                client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
                user_agent=os.environ.get('REDDIT_USER_AGENT', 'KleioBot/1.0'),
            )
        except Exception as e:
            logger.warning("platform=reddit client rotation failed: %s", e)

# Global instance
realtime_stream_monitor = RealtimeStreamMonitor() 