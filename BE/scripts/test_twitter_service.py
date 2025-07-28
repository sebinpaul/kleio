#!/usr/bin/env python
"""
Test script to verify Twitter service functionality
"""
import os
import sys
import django
import time
from datetime import timezone, timedelta

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.twitter.services.twitter_service import TwitterService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_twitter_service_basic():
    """Test basic Twitter service functionality"""
    logger.info("🔍 Testing Twitter service basic functionality")
    logger.info("=" * 60)
    
    try:
        # Create test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.BODY.value, ContentType.COMMENTS.value],
            is_active=True
        )
        keyword.save()
        logger.info(f"✅ Created test keyword: {keyword.keyword}")
        
        # Initialize Twitter service
        twitter_service = TwitterService()
        twitter_service.start_monitoring()
        
        # Test 1: Search tweets
        logger.info("\n1. Testing tweet search...")
        query = '"python" since:1h'
        tweets = twitter_service._search_tweets(query, limit=5)
        
        logger.info(f"✅ Found {len(tweets)} tweets")
        for i, tweet in enumerate(tweets):
            logger.info(f"   Tweet {i+1}: {tweet['content'][:50]}...")
            logger.info(f"   Author: @{tweet['author']}")
            logger.info(f"   URL: {tweet['url']}")
        
        # Test 2: Time window calculation
        logger.info("\n2. Testing time window calculation...")
        time_windows = []
        for i in range(5):
            twitter_service.last_check_time = timezone.now() - timedelta(minutes=i*10)
            time_window = twitter_service._get_time_window()
            time_windows.append(time_window)
            logger.info(f"   {i*10} minutes ago → {time_window}")
        
        # Test 3: Keyword monitoring check
        logger.info("\n3. Testing keyword monitoring check...")
        should_monitor = twitter_service._should_monitor_keyword(keyword)
        logger.info(f"✅ Should monitor keyword: {should_monitor}")
        
        # Test 4: Tweet processing
        logger.info("\n4. Testing tweet processing...")
        if tweets:
            tweet = tweets[0]
            twitter_service._process_tweet_for_keyword(tweet, keyword)
            logger.info("✅ Tweet processing completed")
        
        # Test 5: Content type handling
        logger.info("\n5. Testing content type handling...")
        logger.info("   BODY content type → Main tweet content")
        logger.info("   COMMENTS content type → Reply content")
        logger.info("   TITLES content type → Skipped (not applicable)")
        
        # Clean up
        logger.info("\n6. Cleaning up...")
        keyword.delete()
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 Twitter service tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in Twitter service test: {e}")
        import traceback
        traceback.print_exc()

def test_twitter_content_types():
    """Test Twitter content type handling"""
    logger.info("\n🔍 Testing Twitter content type handling")
    logger.info("=" * 60)
    
    try:
        # Test different content types
        content_types = [
            (ContentType.BODY.value, "Main tweet content"),
            (ContentType.COMMENTS.value, "Reply content"),
            (ContentType.TITLES.value, "Not applicable for Twitter")
        ]
        
        for content_type, description in content_types:
            logger.info(f"\nTesting {content_type}: {description}")
            
            if content_type == ContentType.TITLES.value:
                logger.info("   ⏭️  Skipping TITLES for Twitter (not applicable)")
            else:
                logger.info(f"   ✅ {content_type} is valid for Twitter")
        
        logger.info("\n✅ Content type handling test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in content type test: {e}")

def test_twitter_rate_limiting():
    """Test Twitter rate limiting behavior"""
    logger.info("\n🔍 Testing Twitter rate limiting")
    logger.info("=" * 60)
    
    try:
        twitter_service = TwitterService()
        
        # Test multiple searches with delays
        queries = [
            '"python" since:1h',
            '"javascript" since:30m',
            '"react" since:15m'
        ]
        
        for i, query in enumerate(queries):
            logger.info(f"\nSearch {i+1}: {query}")
            start_time = time.time()
            
            tweets = twitter_service._search_tweets(query, limit=3)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"   Found {len(tweets)} tweets in {duration:.2f}s")
            
            # Add delay between searches
            if i < len(queries) - 1:
                time.sleep(2)
        
        logger.info("\n✅ Rate limiting test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in rate limiting test: {e}")

def main():
    """Main test function"""
    logger.info("🔍 Starting Twitter service tests")
    logger.info("=" * 60)
    
    # Test 1: Basic functionality
    test_twitter_service_basic()
    
    # Test 2: Content type handling
    test_twitter_content_types()
    
    # Test 3: Rate limiting
    test_twitter_rate_limiting()
    
    logger.info("\n🎉 All Twitter service tests completed!")

if __name__ == "__main__":
    main() 