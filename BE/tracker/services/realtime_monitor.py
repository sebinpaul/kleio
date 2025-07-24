import time
import logging
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from .reddit_service import RedditService
from .matching_engine import GenericMatchingEngine, MatchResult
from ..models import Keyword, Mention
from ..enums import Platform, ContentType, MentionContentType
import mongoengine
import os

logger = logging.getLogger(__name__)

class RealtimeStreamMonitor:
    """Real-time keyword monitoring using PRAW SubredditStream"""
    
    def __init__(self):
        self.reddit_service = RedditService()
        self.matching_engine = GenericMatchingEngine()
        self.monitoring_threads = {}
        self.stop_monitoring = False
        
    def start_stream_monitoring(self, keywords=None):
        """Start real-time stream monitoring for keywords"""
        # Reset the stop flag to allow new monitoring
        self.stop_monitoring = False
        
        if keywords is None:
            keywords = Keyword.objects.filter(is_active=True)
        
        # Handle both QuerySet and list
        keywords_count = len(keywords)
            
        
        logger.info(f"Starting real-time stream monitoring for {keywords_count} keywords")
        
        # Group keywords by subreddit for efficient streaming
        subreddit_keywords = self._group_keywords_by_subreddit(keywords)
        for subreddit_name, keywords_list in subreddit_keywords.items():
            if not self.stop_monitoring:
                thread = threading.Thread(
                    target=self._monitor_subreddit_stream,
                    args=(subreddit_name, keywords_list),
                    daemon=True
                )
                thread.start()
                self.monitoring_threads[subreddit_name] = thread
                logger.info(f"Started monitoring stream for r/{subreddit_name}")
        
        logger.info("Real-time stream monitoring started successfully")
    
    def stop_stream_monitoring(self):
        """Stop all monitoring threads"""
        self.stop_monitoring = True
        logger.info("Stopping real-time stream monitoring...")
        
        # Wait for threads to finish
        for subreddit, thread in self.monitoring_threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"Stopped monitoring r/{subreddit}")
        
        self.monitoring_threads.clear()
        logger.info("Real-time stream monitoring stopped")
    
    def _group_keywords_by_subreddit(self, keywords):
        """Group keywords by subreddit for efficient streaming"""
        subreddit_keywords = {}
        
        for keyword in keywords:
            if keyword.platform in [Platform.REDDIT.value, Platform.ALL.value]:
                # Use platform-specific filters for subreddits
                if keyword.platform_specific_filters:
                    # If specific subreddits are specified, monitor each one
                    for subreddit in keyword.platform_specific_filters:
                        if subreddit not in subreddit_keywords:
                            subreddit_keywords[subreddit] = []
                        subreddit_keywords[subreddit].append(keyword)
                else:
                    # If no specific subreddits, monitor 'all'
                    if 'all' not in subreddit_keywords:
                        subreddit_keywords['all'] = []
                    subreddit_keywords['all'].append(keyword)
        
        return subreddit_keywords
    
    def _monitor_subreddit_stream(self, subreddit_name, keywords):
        """Monitor a specific subreddit stream for keywords"""
        try:
            reddit = self.reddit_service.get_reddit_instance()
            subreddit = reddit.subreddit(subreddit_name)
            
            logger.info(f"Starting stream monitoring for r/{subreddit_name} with {len(keywords)} keywords")
            
            # Monitor submissions stream
            self._monitor_submissions_stream(subreddit, keywords)
            
        except Exception as e:
            logger.error(f"Error in subreddit stream monitoring for r/{subreddit_name}: {e}")
    
    def _monitor_submissions_stream(self, subreddit, keywords):
        """Monitor submissions stream for keywords"""
        try:
            # Get the stream with skip_existing=True to only get new submissions
            for submission in subreddit.stream.submissions(skip_existing=True):
                if self.stop_monitoring:
                    break
                # Check if submission matches any keywords
                self._check_submission_for_keywords(submission, keywords)
                
        except Exception as e:
            logger.error(f"Error in submissions stream: {e}")
            # Restart the stream after a delay
            time.sleep(30)
            if not self.stop_monitoring:
                self._monitor_submissions_stream(subreddit, keywords)
    
    def _monitor_comments_stream(self, subreddit, keywords):
        """Monitor comments stream for keywords"""
        try:
            # Get the stream with skip_existing=True to only get new comments
            for comment in subreddit.stream.comments(skip_existing=True):
                if self.stop_monitoring:
                    break
                
                # Check if comment matches any keywords
                self._check_comment_for_keywords(comment, keywords)
                
        except Exception as e:
            logger.error(f"Error in comments stream: {e}")
            # Restart the stream after a delay
            time.sleep(30)
            if not self.stop_monitoring:
                self._monitor_comments_stream(subreddit, keywords)
    
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
                    if not self.matching_engine.should_monitor_content(keyword, content_type):
                        continue
                    
                    match_result = self.matching_engine.match_keyword(keyword, content, content_type)
                    
                    if match_result:
                        # Determine mention content type
                        mention_content_type = self._map_content_type_to_mention_type(content_type)
                        
                        mention = self._create_mention_from_submission(
                            keyword, submission, match_result, mention_content_type
                        )
                        if mention:
                            try:
                                mention.save()
                                logger.info(f"🎯 New mention found! Keyword: '{keyword.keyword}' in r/{submission.subreddit.display_name}")
                                logger.info(f"   Content Type: {content_type}")
                                logger.info(f"   Title: {submission.title[:50]}...")
                                logger.info(f"   URL: https://reddit.com{submission.permalink}")
                                
                                # Send notification (you can implement this)
                                self._send_notification(mention)
                                
                            except Exception as e:
                                logger.error(f"Error saving mention: {e}")
        
        except Exception as e:
            logger.error(f"Error checking submission for keywords: {e}")
    
    def _check_comment_for_keywords(self, comment, keywords):
        """Check if a comment matches any keywords"""
        try:
            # Check comments content type
            content = comment.body
            
            for keyword in keywords:
                if not self.matching_engine.should_monitor_content(keyword, ContentType.COMMENTS.value):
                    continue
                
                match_result = self.matching_engine.match_keyword(keyword, content, ContentType.COMMENTS.value)
                
                if match_result:
                    mention = self._create_mention_from_comment(keyword, comment, match_result)
                    if mention:
                        try:
                            mention.save()
                            logger.info(f"🎯 New mention found! Keyword: '{keyword.keyword}' in comment on r/{comment.subreddit.display_name}")
                            logger.info(f"   Comment: {comment.body[:50]}...")
                            logger.info(f"   URL: https://reddit.com{comment.permalink}")
                            
                            # Send notification (you can implement this)
                            self._send_notification(mention)
                            
                        except Exception as e:
                            logger.error(f"Error saving mention: {e}")
        
        except Exception as e:
            logger.error(f"Error checking comment for keywords: {e}")
    
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
                mention_date=datetime.fromtimestamp(submission.created_utc)
            )
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from submission: {str(e)}")
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
                mention_date=datetime.fromtimestamp(comment.created_utc)
            )
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from comment: {str(e)}")
            return None
    
    def _map_content_type_to_mention_type(self, content_type: str) -> str:
        """Map content type to mention content type"""
        mapping = {
            ContentType.COMMENTS.value: MentionContentType.COMMENT.value,
            ContentType.TITLES.value: MentionContentType.TITLE.value,
            ContentType.BODY.value: MentionContentType.BODY.value,
        }
        return mapping.get(content_type, MentionContentType.TITLE.value)
    
    def _send_notification(self, mention):
        """Send notification for new mention (placeholder)"""
        # TODO: Implement email/Slack notification
        logger.info(f"📧 Would send notification for mention: {mention.keyword_id}")

# Global instance
realtime_stream_monitor = RealtimeStreamMonitor() 