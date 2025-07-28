#!/usr/bin/env python
"""
Mock Twitter monitoring service for testing (doesn't rely on external APIs)
"""
import os
import sys
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import logging

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service

logger = logging.getLogger(__name__)

class MockTwitterService:
    """Mock Twitter monitoring service for testing"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.tweet_cache = {}  # Cache to avoid duplicates
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = 30  # Check every 30 seconds
        
        # Mock tweet data for testing
        self.mock_tweets = [
            {
                'id': '123456789',
                'content': 'Just learned about Python programming! #python #coding',
                'author': 'testuser1',
                'author_id': 'user1',
                'date': timezone.now() - timedelta(minutes=5),
                'url': 'https://twitter.com/testuser1/status/123456789',
                'reply_count': 2,
                'retweet_count': 5,
                'like_count': 10,
                'is_reply': False,
                'parent_tweet_id': None,
                'hashtags': ['python', 'coding'],
                'mentions': []
            },
            {
                'id': '123456790',
                'content': 'Python is amazing for data science! #python #datascience',
                'author': 'testuser2',
                'author_id': 'user2',
                'date': timezone.now() - timedelta(minutes=3),
                'url': 'https://twitter.com/testuser2/status/123456790',
                'reply_count': 1,
                'retweet_count': 3,
                'like_count': 8,
                'is_reply': False,
                'parent_tweet_id': None,
                'hashtags': ['python', 'datascience'],
                'mentions': []
            },
            {
                'id': '123456791',
                'content': 'Great tutorial on Python! Thanks for sharing #python',
                'author': 'testuser3',
                'author_id': 'user3',
                'date': timezone.now() - timedelta(minutes=1),
                'url': 'https://twitter.com/testuser3/status/123456791',
                'reply_count': 0,
                'retweet_count': 1,
                'like_count': 5,
                'is_reply': True,
                'parent_tweet_id': '123456789',
                'hashtags': ['python'],
                'mentions': []
            }
        ]
        
    def start_monitoring(self):
        """Initialize monitoring start time"""
        self.last_check_time = timezone.now()
        logger.info("Mock Twitter monitoring initialized")
    
    def start_stream_monitoring(self, keywords: List[Keyword]):
        """Start mock Twitter monitoring"""
        if self.is_monitoring:
            logger.info("Mock Twitter monitoring already running")
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(keywords,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started Mock Twitter streaming for {len(keywords)} keywords")
    
    def stop_stream_monitoring(self):
        """Stop Twitter monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped Mock Twitter streaming")
    
    def _run_monitoring_loop(self, keywords: List[Keyword]):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_for_new_tweets(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in Mock Twitter monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_for_new_tweets(self, keywords: List[Keyword]):
        """Check for new tweets matching keywords"""
        try:
            current_time = timezone.now()
            
            for keyword in keywords:
                if not self._should_monitor_keyword(keyword):
                    continue
                
                logger.debug(f"Searching Mock Twitter for keyword: {keyword.keyword}")
                
                # Use mock tweets for testing
                tweets = self._get_mock_tweets(keyword.keyword)
                
                for tweet in tweets:
                    if self._is_new_tweet(tweet, keyword):
                        self._process_tweet_for_keyword(tweet, keyword)
                        
        except Exception as e:
            logger.error(f"Error checking for new tweets: {e}")
    
    def _get_mock_tweets(self, keyword: str) -> List[Dict]:
        """Get mock tweets that match the keyword"""
        matching_tweets = []
        for tweet in self.mock_tweets:
            if keyword.lower() in tweet['content'].lower():
                matching_tweets.append(tweet)
        return matching_tweets
    
    def _is_new_tweet(self, tweet: Dict, keyword: Keyword) -> bool:
        """Check if tweet is new and should be processed"""
        tweet_id = tweet['id']
        keyword_id = str(keyword.id)
        
        # Check cache
        cache_key = f"{keyword_id}_{tweet_id}"
        if cache_key in self.tweet_cache:
            return False
        
        # Add to cache
        self.tweet_cache[cache_key] = time.time()
        
        # Clean old cache entries (older than 1 hour)
        current_time = time.time()
        self.tweet_cache = {k: v for k, v in self.tweet_cache.items() 
                           if current_time - v < 3600}
        
        return True
    
    def _should_monitor_keyword(self, keyword: Keyword) -> bool:
        """Check if keyword should be monitored for Twitter"""
        return (keyword.platform in [Platform.TWITTER.value, Platform.ALL.value] and
                keyword.is_active)
    
    def _process_tweet_for_keyword(self, tweet: Dict, keyword: Keyword):
        """Process a tweet and check for keyword matches"""
        try:
            # Check content types based on keyword settings
            content_types_to_check = keyword.content_types or [ContentType.BODY.value]
            
            for content_type in content_types_to_check:
                if content_type == ContentType.BODY.value:
                    # Main tweet content
                    self._check_tweet_content(tweet, keyword, ContentType.BODY.value)
                    
                elif content_type == ContentType.COMMENTS.value:
                    # Only process if it's a reply
                    if tweet.get('is_reply'):
                        self._check_tweet_content(tweet, keyword, ContentType.COMMENTS.value)
                        
                elif content_type == ContentType.TITLES.value:
                    # Skip TITLES for Twitter (not applicable)
                    logger.debug(f"Skipping TITLES content type for Twitter tweet {tweet['id']}")
                    
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.get('id')}: {e}")
    
    def _check_tweet_content(self, tweet: Dict, keyword: Keyword, content_type: str):
        """Check if tweet content matches keyword"""
        content = tweet.get('content', '')
        
        # Check if keyword should monitor this content type
        if not self.matching_engine.should_monitor_content(keyword, content_type):
            return
        
        # Perform keyword matching
        match_result = self.matching_engine.match_keyword(keyword, content, content_type)
        
        if match_result:
            # Create mention
            mention = self._create_mention_from_tweet(tweet, keyword, match_result, content_type)
            if mention:
                self._save_mention(mention, keyword)
                logger.info(f"🎯 New Mock Twitter mention! Keyword: '{keyword.keyword}' - {content[:50]}...")
    
    def _create_mention_from_tweet(self, tweet: Dict, keyword: Keyword, match_result, content_type: str) -> Optional[Mention]:
        """Create a Mention object from a Twitter tweet"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=tweet['url'],
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=tweet['content'],
                title=f"Tweet by @{tweet['author']}",
                author=tweet['author'],
                source_url=tweet['url'],
                platform=Platform.TWITTER.value,
                subreddit='twitter',  # Using subreddit field for platform location
                content_type=content_type,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                mention_date=tweet['date'],
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = tweet['id']
            mention.platform_score = tweet.get('like_count', 0)
            mention.platform_comments_count = tweet.get('reply_count', 0)
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from tweet: {str(e)}")
            return None
    
    def _save_mention(self, mention: Mention, keyword: Keyword):
        """Save mention and send notification"""
        try:
            mention.save()
            logger.info(f"💾 Saved Mock Twitter mention: {mention.keyword_id} - {mention.title[:50]}...")
            
            # Send email notification
            success = email_notification_service.send_mention_notification(mention)
            if success:
                logger.info(f"📧 Email notification sent for mention {mention.id}")
            else:
                logger.error(f"Failed to send email notification for mention {mention.id}")
                
        except Exception as e:
            logger.error(f"Error saving mention: {e}")
    
    def reset_monitoring(self):
        """Reset monitoring state (useful for testing)"""
        self.last_check_time = None
        self.tweet_cache.clear()
        logger.info("Reset Mock Twitter monitoring - will start fresh on next run")

# Global instance
mock_twitter_service = MockTwitterService() 