#!/usr/bin/env python
"""
Test script to verify Twitter integration with the entire Kleio system
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
from platforms.twitter.services.twitter_service import twitter_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_twitter_integration():
    """Test Twitter integration with the entire system"""
    logger.info("🔍 Testing Twitter integration with Kleio system")
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
        
        # Test 2: Test Twitter service directly
        logger.info("\n2. Testing Twitter service directly...")
        twitter_service.start_monitoring()
        
        # Test search functionality
        query = '"python" since:1h'
        tweets = twitter_service._search_tweets(query, limit=3)
        logger.info(f"✅ Found {len(tweets)} tweets for 'python'")
        
        # Test 3: Test keyword processing
        logger.info("\n3. Testing keyword processing...")
        if tweets:
            tweet = tweets[0]
            twitter_service._process_tweet_for_keyword(tweet, twitter_keyword)
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
        
        # Check Twitter service status
        twitter_status = {
            'is_monitoring': twitter_service.is_monitoring,
            'check_interval': twitter_service.check_interval,
            'tweet_cache_size': len(twitter_service.tweet_cache)
        }
        logger.info(f"✅ Twitter service status: {twitter_status}")
        
        # Test 9: Clean up
        logger.info("\n9. Cleaning up test data...")
        
        # Stop services
        auto_monitor_service.stop_auto_monitoring()
        twitter_service.stop_stream_monitoring()
        
        # Delete test keywords
        for keyword in keywords + [body_keyword, comments_keyword, titles_keyword, reddit_keyword]:
            keyword.delete()
        
        # Delete test mentions
        Mention.objects.filter(user_id="test_user").delete()
        
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 Twitter integration tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in Twitter integration test: {e}")
        import traceback
        traceback.print_exc()

def test_twitter_content_type_mapping():
    """Test Twitter content type mapping"""
    logger.info("\n🔍 Testing Twitter content type mapping")
    logger.info("=" * 60)
    
    try:
        # Test content type mapping
        content_type_mapping = {
            ContentType.BODY.value: "Main tweet content (tweet text itself)",
            ContentType.COMMENTS.value: "Reply content (replies to tweets)",
            ContentType.TITLES.value: "Not applicable for Twitter (should be skipped)"
        }
        
        for content_type, description in content_type_mapping.items():
            logger.info(f"\nContent Type: {content_type}")
            logger.info(f"Description: {description}")
            
            if content_type == ContentType.TITLES.value:
                logger.info("   ⏭️  Should be skipped for Twitter")
            else:
                logger.info("   ✅ Valid for Twitter monitoring")
        
        logger.info("\n✅ Content type mapping test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in content type mapping test: {e}")

def main():
    """Main test function"""
    logger.info("🔍 Starting Twitter integration tests")
    logger.info("=" * 60)
    
    # Test 1: Full integration
    test_twitter_integration()
    
    # Test 2: Content type mapping
    test_twitter_content_type_mapping()
    
    logger.info("\n🎉 All Twitter integration tests completed!")

if __name__ == "__main__":
    main() 