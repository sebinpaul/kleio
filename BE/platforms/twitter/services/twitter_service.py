#!/usr/bin/env python
"""
Twitter monitoring service using snscrape
"""
import os
import sys
import time
import threading
import snscrape.modules.twitter as sntwitter
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
import logging

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services import email_notification_service

logger = logging.getLogger(__name__)

class TwitterService:
    """Twitter monitoring service using snscrape"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.tweet_cache = {}  # Cache to avoid duplicates
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = 30  # Check every 30 seconds
        
    def start_monitoring(self):
        """Initialize monitoring start time"""
        self.last_check_time = timezone.now()
        logger.info("Twitter monitoring initialized")
    
    def start_stream_monitoring(self, keywords: List[Keyword]):
        """Start real-time Twitter monitoring"""
        if self.is_monitoring:
            logger.info("Twitter monitoring already running")
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(keywords,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started Twitter streaming for {len(keywords)} keywords")
    
    def stop_stream_monitoring(self):
        """Stop Twitter monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped Twitter streaming")
    
    def _run_monitoring_loop(self, keywords: List[Keyword]):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_for_new_tweets(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in Twitter monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_for_new_tweets(self, keywords: List[Keyword]):
        """Check for new tweets matching keywords"""
        try:
            current_time = timezone.now()
            
            for keyword in keywords:
                if not self._should_monitor_keyword(keyword):
                    continue
                
                # Build query with time window
                time_window = self._get_time_window()
                query = f'"{keyword.keyword}" since:{time_window}'
                logger.debug(f"Searching Twitter for: {query}")
                
                tweets = self._search_tweets(query, limit=20)
                
                for tweet in tweets:
                    if self._is_new_tweet(tweet, keyword):
                        self._process_tweet_for_keyword(tweet, keyword)
                        
        except Exception as e:
            logger.error(f"Error checking for new tweets: {e}")
    
    def _search_tweets(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for tweets using snscrape"""
        tweets = []
        try:
            scraper = sntwitter.TwitterSearchScraper(query)
            
            for tweet in scraper.get_items():
                if len(tweets) >= limit:
                    break
                    
                tweet_data = {
                    'id': str(tweet.id),
                    'content': tweet.rawContent,
                    'author': tweet.user.username,
                    'author_id': str(tweet.user.id),
                    'date': tweet.date,
                    'url': tweet.url,
                    'reply_count': tweet.replyCount,
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'is_reply': tweet.inReplyToTweetId is not None,
                    'parent_tweet_id': str(tweet.inReplyToTweetId) if tweet.inReplyToTweetId else None,
                    'hashtags': [hashtag for hashtag in tweet.hashtags] if tweet.hashtags else [],
                    'mentions': [mention for mention in tweet.mentionedUsers] if tweet.mentionedUsers else []
                }
                tweets.append(tweet_data)
                
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            
        return tweets
    
    def _get_time_window(self) -> str:
        """Get appropriate time window for query"""
        if not self.last_check_time:
            return "1h"  # Default to 1 hour
        
        # Calculate time since last check
        time_diff = timezone.now() - self.last_check_time
        minutes = int(time_diff.total_seconds() / 60)
        
        if minutes < 5:
            return "5m"
        elif minutes < 15:
            return "15m"
        elif minutes < 30:
            return "30m"
        else:
            return "1h"
    
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
                logger.info(f"🎯 New Twitter mention! Keyword: '{keyword.keyword}' - {content[:50]}...")
    
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
            logger.info(f"💾 Saved Twitter mention: {mention.keyword_id} - {mention.title[:50]}...")
            
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
        logger.info("Reset Twitter monitoring - will start fresh on next run")

# Global instance
twitter_service = TwitterService() 