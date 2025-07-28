#!/usr/bin/env python
"""
Test script to verify Twitter integration using mock service
"""
import os
import sys
import django
import time

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
from core.enums import Platform, ContentType
from core.services.auto_monitor_service import auto_monitor_service
from platforms.twitter.services.twitter_service_mock import mock_twitter_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mock_twitter_service():
    """Test the mock Twitter service"""
    logger.info("🔍 Testing Mock Twitter service")
    logger.info("=" * 60)
    
    try:
        # Test 1: Create Twitter keywords
        logger.info("\n1. Creating Twitter keywords...")
        
        # Create different types of keywords
        keywords = []
        
        # Twitter-only keyword
        twitter_keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.BODY.value, ContentType.COMMENTS.value],
            is_active=True
        )
        twitter_keyword.save()
        keywords.append(twitter_keyword)
        logger.info(f"✅ Created Twitter keyword: {twitter_keyword.keyword}")
        
        # All-platform keyword
        all_platform_keyword = Keyword(
            user_id="test_user",
            keyword="javascript",
            platform=Platform.ALL.value,
            content_types=[ContentType.BODY.value],
            is_active=True
        )
        all_platform_keyword.save()
        keywords.append(all_platform_keyword)
        logger.info(f"✅ Created all-platform keyword: {all_platform_keyword.keyword}")
        
        # Test 2: Test mock Twitter service directly
        logger.info("\n2. Testing Mock Twitter service directly...")
        mock_twitter_service.start_monitoring()
        
        # Test mock tweet search
        mock_tweets = mock_twitter_service._get_mock_tweets("python")
        logger.info(f"✅ Found {len(mock_tweets)} mock tweets for 'python'")
        
        for i, tweet in enumerate(mock_tweets):
            logger.info(f"   Mock tweet {i+1}: {tweet['content'][:50]}...")
            logger.info(f"   Author: @{tweet['author']}")
            logger.info(f"   URL: {tweet['url']}")
        
        # Test 3: Test keyword processing
        logger.info("\n3. Testing keyword processing...")
        if mock_tweets:
            tweet = mock_tweets[0]
            mock_twitter_service._process_tweet_for_keyword(tweet, twitter_keyword)
            logger.info("✅ Tweet processing completed")
        
        # Test 4: Test auto monitor service integration
        logger.info("\n4. Testing auto monitor service integration...")
        
        # Start auto monitoring
        auto_monitor_service.start_auto_monitoring()
        logger.info("✅ Auto monitor service started")
        
        # Check status
        status = auto_monitor_service.get_status()
        logger.info(f"✅ Auto monitor status: {status}")
        
        # Wait a bit for monitoring to start
        time.sleep(2)
        
        # Test 5: Test mention creation
        logger.info("\n5. Testing mention creation...")
        
        # Check if any mentions were created
        mentions = Mention.objects.filter(
            keyword_id=str(twitter_keyword.id),
            platform=Platform.TWITTER.value
        )
        logger.info(f"✅ Found {mentions.count()} Twitter mentions")
        
        # Test 6: Test content type handling
        logger.info("\n6. Testing content type handling...")
        
        # Test BODY content type (main tweets)
        body_keyword = Keyword(
            user_id="test_user",
            keyword="react",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.BODY.value],
            is_active=True
        )
        body_keyword.save()
        logger.info(f"✅ Created BODY-only keyword: {body_keyword.keyword}")
        
        # Test COMMENTS content type (replies)
        comments_keyword = Keyword(
            user_id="test_user",
            keyword="vue",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.COMMENTS.value],
            is_active=True
        )
        comments_keyword.save()
        logger.info(f"✅ Created COMMENTS-only keyword: {comments_keyword.keyword}")
        
        # Test TITLES content type (should be skipped)
        titles_keyword = Keyword(
            user_id="test_user",
            keyword="angular",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.TITLES.value],
            is_active=True
        )
        titles_keyword.save()
        logger.info(f"✅ Created TITLES keyword (will be skipped): {titles_keyword.keyword}")
        
        # Test 7: Test platform separation
        logger.info("\n7. Testing platform separation...")
        
        # Create Reddit-only keyword
        reddit_keyword = Keyword(
            user_id="test_user",
            keyword="django",
            platform=Platform.REDDIT.value,
            content_types=[ContentType.TITLES.value],
            is_active=True
        )
        reddit_keyword.save()
        logger.info(f"✅ Created Reddit-only keyword: {reddit_keyword.keyword}")
        
        # Check which keywords should be monitored for Twitter
        all_keywords = Keyword.objects.filter(is_active=True)
        twitter_keywords = [kw for kw in all_keywords if kw.platform in [Platform.TWITTER.value, Platform.ALL.value]]
        reddit_keywords = [kw for kw in all_keywords if kw.platform in [Platform.REDDIT.value, Platform.ALL.value]]
        
        logger.info(f"✅ Twitter keywords: {len(twitter_keywords)}")
        logger.info(f"✅ Reddit keywords: {len(reddit_keywords)}")
        
        # Test 8: Test monitoring status
        logger.info("\n8. Testing monitoring status...")
        
        # Check Mock Twitter service status
        twitter_status = {
            'is_monitoring': mock_twitter_service.is_monitoring,
            'check_interval': mock_twitter_service.check_interval,
            'tweet_cache_size': len(mock_twitter_service.tweet_cache)
        }
        logger.info(f"✅ Mock Twitter service status: {twitter_status}")
        
        # Test 9: Test mock streaming
        logger.info("\n9. Testing mock streaming...")
        
        # Start mock Twitter streaming
        mock_twitter_service.start_stream_monitoring(twitter_keywords)
        logger.info("✅ Mock Twitter streaming started")
        
        # Wait a bit for processing
        time.sleep(3)
        
        # Check for mentions
        mentions = Mention.objects.filter(
            platform=Platform.TWITTER.value,
            user_id="test_user"
        )
        logger.info(f"✅ Found {mentions.count()} mentions from mock streaming")
        
        # Stop streaming
        mock_twitter_service.stop_stream_monitoring()
        logger.info("✅ Mock Twitter streaming stopped")
        
        # Test 10: Clean up
        logger.info("\n10. Cleaning up test data...")
        
        # Stop services
        auto_monitor_service.stop_auto_monitoring()
        
        # Delete test keywords
        for keyword in keywords + [body_keyword, comments_keyword, titles_keyword, reddit_keyword]:
            keyword.delete()
        
        # Delete test mentions
        Mention.objects.filter(user_id="test_user").delete()
        
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 Mock Twitter integration tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in Mock Twitter integration test: {e}")
        import traceback
        traceback.print_exc()

def test_mock_tweet_matching():
    """Test mock tweet matching functionality"""
    logger.info("\n🔍 Testing Mock Tweet Matching")
    logger.info("=" * 60)
    
    try:
        # Create test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.BODY.value],
            is_active=True
        )
        keyword.save()
        
        # Test matching with mock tweets
        mock_tweets = mock_twitter_service._get_mock_tweets("python")
        logger.info(f"✅ Found {len(mock_tweets)} mock tweets matching 'python'")
        
        for i, tweet in enumerate(mock_tweets):
            logger.info(f"\nMock Tweet {i+1}:")
            logger.info(f"   Content: {tweet['content']}")
            logger.info(f"   Author: @{tweet['author']}")
            logger.info(f"   Is Reply: {tweet['is_reply']}")
            
            # Test processing
            mock_twitter_service._process_tweet_for_keyword(tweet, keyword)
        
        # Clean up
        keyword.delete()
        Mention.objects.filter(user_id="test_user").delete()
        
        logger.info("\n✅ Mock tweet matching test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in mock tweet matching test: {e}")

def main():
    """Main test function"""
    logger.info("🔍 Starting Mock Twitter integration tests")
    logger.info("=" * 60)
    
    # Test 1: Full integration
    test_mock_twitter_service()
    
    # Test 2: Tweet matching
    test_mock_tweet_matching()
    
    logger.info("\n🎉 All Mock Twitter integration tests completed!")

if __name__ == "__main__":
    main() 