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
from core.services.matching_engine import GenericMatchingEngine, MatchResult
from core.services.email_service import email_notification_service
from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType

logger = logging.getLogger(__name__)

class RealtimeStreamMonitor:
    """Manages real-time monitoring of Reddit streams for keyword mentions"""
    
    def __init__(self):
        self.reddit = None
        self.stop_monitoring = False
        self.monitoring_threads = []
        self.matching_engine = GenericMatchingEngine()
        self.monitoring_start_time = None
    
    def start_stream_monitoring(self, keywords=None):
        """Start monitoring Reddit streams for keyword mentions"""
        self.monitoring_start_time = int(timezone.now().replace(tzinfo=dt_timezone.utc).timestamp())
        logger.info(f"Started Reddit monitoring at timestamp: {self.monitoring_start_time}")
        try:
            self.stop_monitoring = False
            
            # Initialize Reddit client
            if not self.reddit:
                self.reddit = praw.Reddit(
                    client_id=os.environ.get('REDDIT_CLIENT_ID'),
                    client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
                    user_agent=os.environ.get('REDDIT_USER_AGENT', 'KleioBot/1.0')
                )
            
            # Get keywords to monitor
            if keywords is None:
                keywords = Keyword.objects.filter(is_active=True)
            
            if not keywords:
                logger.info("No active keywords to monitor")
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
                logger.info(f"Started monitoring r/{subreddit_name} with {len(keywords_list)} keywords")
            
            logger.info(f"Started monitoring {len(subreddit_keywords)} subreddits with {len(keywords)} total keywords")
            
        except Exception as e:
            logger.error(f"Error starting stream monitoring: {e}")
    
    def stop_stream_monitoring(self):
        """Stop all monitoring threads"""
        logger.info("Stopping stream monitoring...")
        self.stop_monitoring = True
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        self.monitoring_threads.clear()
        logger.info("Stream monitoring stopped")
    
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
            
            # Add threads to monitoring list
            self.monitoring_threads.extend([submissions_thread, comments_thread])
            self.monitoring_threads.extend([comments_thread])
            
            logger.info(f"Started monitoring r/{subreddit_name} with {len(keywords)} keywords")
            
        except Exception as e:
            logger.error(f"Error monitoring r/{subreddit_name}: {e}")
    
    def _monitor_submissions_stream(self, subreddit, keywords):
        """Monitor submissions stream for mentions"""
        try:
            logger.info(f"Starting submissions stream monitoring for r/{subreddit.display_name} (skip_existing=True)")
            
            for submission in subreddit.stream.submissions(skip_existing=True):
                if self.stop_monitoring:
                    break
                
                self._check_submission_for_keywords(submission, keywords)
                
        except Exception as e:
            logger.error(f"Error in submissions stream for r/{subreddit.display_name}: {e}")
    
    def _monitor_comments_stream(self, subreddit, keywords):
        """Monitor comments stream for mentions"""
        try:
            logger.info(f"Starting comments stream monitoring for r/{subreddit.display_name} (skip_existing=True)")
            
            for comment in subreddit.stream.comments(skip_existing=True):
                if self.stop_monitoring:
                    break
                self._check_comment_for_keywords(comment, keywords)
                
        except Exception as e:
            logger.error(f"Error in comments stream for r/{subreddit.display_name}: {e}")
    
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
                                
                                # Send email notification
                                self._send_email_notification(mention, keyword)
                                
                            except Exception as e:
                                logger.error(f"Error saving mention: {e}")
        
        except Exception as e:
            logger.error(f"Error checking submission for keywords: {e}")
    
    def _check_comment_for_keywords(self, comment, keywords):
        """Check if a comment matches any keywords"""
        try:
            # Check comments content type
            content = comment.body
            
            # Debug logging
            logger.debug(f"Checking comment: {content[:100]}... in r/{comment.subreddit.display_name}")
            logger.debug(f"Keywords to check: {[kw.keyword for kw in keywords]}")
            
            for keyword in keywords:
                # Check if keyword should monitor comments
                should_monitor = self.matching_engine.should_monitor_content(keyword, ContentType.COMMENTS.value)
                logger.debug(f"Keyword '{keyword.keyword}' should monitor comments: {should_monitor}")
                logger.debug(f"Keyword content types: {keyword.content_types}")
                
                if not should_monitor:
                    logger.debug(f"Skipping keyword '{keyword.keyword}' - not monitoring comments")
                    continue
                
                match_result = self.matching_engine.match_keyword(keyword, content, ContentType.COMMENTS.value)
                
                if match_result:
                    logger.info(f"🎯 Match found! Keyword: '{keyword.keyword}' in comment")
                    mention = self._create_mention_from_comment(keyword, comment, match_result)
                    if mention:
                        try:
                            mention.save()
                            logger.info(f"🎯 New mention found! Keyword: '{keyword.keyword}' in comment on r/{comment.subreddit.display_name}")
                            logger.info(f"   Comment: {comment.body[:50]}...")
                            logger.info(f"   URL: https://reddit.com{comment.permalink}")
                            
                            # Send email notification
                            self._send_email_notification(mention, keyword)
                            
                        except Exception as e:
                            logger.error(f"Error saving mention: {e}")
                else:
                    logger.debug(f"No match for keyword '{keyword.keyword}' in comment")
        
        except Exception as e:
            logger.error(f"Error checking comment for keywords: {e}")
    
    def _send_email_notification(self, mention, keyword):
        """Send email notification for a new mention"""
        try:
            # Send email notification using the service
            success = email_notification_service.send_mention_notification(mention)
            if success:
                logger.info(f"Email notification sent for mention {mention.id}")
            else:
                logger.error(f"Failed to send email notification for mention {mention.id}")
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    

    
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

# Global instance
realtime_stream_monitor = RealtimeStreamMonitor() 