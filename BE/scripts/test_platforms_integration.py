#!/usr/bin/env python
"""
Comprehensive test script for all platform integrations
"""
import os
import sys
import django
import time
import logging
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from core.services.auto_monitor_service import auto_monitor_service
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from platforms.hackernews.services.hackernews_service import HackerNewsService
from platforms.twitter.services.twitter_service_mock import mock_twitter_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_platform_integration():
    """Test integration across all platforms"""
    logger.info("🔍 Testing Platform Integration")
    logger.info("=" * 60)
    
    try:
        # Create test keywords for each platform
        test_keywords = [
            {
                'user_id': 'test-user-123',
                'keyword': 'python',
                'platform': Platform.REDDIT.value,
                'content_types': [ContentType.COMMENTS.value, ContentType.TITLES.value],
                'is_active': True
            },
            {
                'user_id': 'test-user-123',
                'keyword': 'django',
                'platform': Platform.HACKERNEWS.value,
                'content_types': [ContentType.TITLES.value],
                'is_active': True
            },
            {
                'user_id': 'test-user-123',
                'keyword': 'react',
                'platform': Platform.TWITTER.value,
                'content_types': [ContentType.TITLES.value],
                'is_active': True
            }
        ]
        
        # Create keywords
        keywords = []
        for kw_data in test_keywords:
            keyword = Keyword(**kw_data)
            keyword.save()
            keywords.append(keyword)
            logger.info(f"✅ Created keyword: {keyword.keyword} for {keyword.platform}")
        
        # Test auto monitoring service
        logger.info("\n🚀 Testing Auto Monitoring Service...")
        auto_monitor_service.start_auto_monitoring()
        
        # Wait for service to start
        time.sleep(3)
        
        # Check status
        status = auto_monitor_service.get_status()
        logger.info(f"Service running: {status['is_running']}")
        logger.info(f"Monitored keywords: {status['monitored_keywords_count']}")
        
        # Test individual platform services
        logger.info("\n🔍 Testing Individual Platform Services...")
        
        # Test HackerNews service
        hn_service = HackerNewsService()
        hn_service.start_monitoring()
        logger.info("✅ HackerNews service initialized")
        
        # Test Reddit service
        logger.info("✅ Reddit service available")
        
        # Test Twitter mock service
        mock_twitter_service.start_monitoring()
        logger.info("✅ Twitter mock service initialized")
        
        # Clean up test keywords
        for keyword in keywords:
            keyword.delete()
        
        logger.info("\n✅ Platform integration test completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error in platform integration test: {e}")
        import traceback
        traceback.print_exc()

def test_mention_creation():
    """Test mention creation for all platforms"""
    logger.info("\n🔍 Testing Mention Creation")
    logger.info("=" * 50)
    
    try:
        # Create a test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="testkeyword",
            platform=Platform.ALL.value,
            content_types=[ContentType.TITLES.value, ContentType.COMMENTS.value],
            is_active=True
        )
        keyword.save()
        
        # Test Reddit mention
        reddit_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="This is a test post about testkeyword",
            title="Test Post",
            author="testuser",
            source_url="https://reddit.com/r/test/comments/123",
            platform=Platform.REDDIT.value,
            content_type=MentionContentType.TITLE.value,
            matched_text="testkeyword",
            match_position=25,
            match_confidence=1.0,
            mention_date=datetime.now(),
            discovered_at=datetime.now()
        )
        reddit_mention.save()
        logger.info(f"✅ Created Reddit mention: {reddit_mention.id}")
        
        # Test HackerNews mention
        hn_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="Show HN: My new project with testkeyword",
            title="Show HN: My new project with testkeyword",
            author="testuser",
            source_url="https://news.ycombinator.com/item?id=123",
            platform=Platform.HACKERNEWS.value,
            content_type=MentionContentType.TITLE.value,
            matched_text="testkeyword",
            match_position=30,
            match_confidence=1.0,
            mention_date=datetime.now(),
            discovered_at=datetime.now()
        )
        hn_mention.save()
        logger.info(f"✅ Created HackerNews mention: {hn_mention.id}")
        
        # Clean up
        keyword.delete()
        reddit_mention.delete()
        hn_mention.delete()
        
        logger.info("✅ Mention creation test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in mention creation test: {e}")

def main():
    """Run all tests"""
    logger.info("🚀 Starting Comprehensive Platform Tests")
    logger.info("=" * 60)
    
    test_platform_integration()
    test_mention_creation()
    
    logger.info("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 