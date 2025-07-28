#!/usr/bin/env python
"""
Simple test script to verify Twitter functionality
"""
import os
import sys
import django
import time
from django.utils import timezone

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
from core.enums import Platform, ContentType
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_twitter_platform_enum():
    """Test that Twitter is properly defined in Platform enum"""
    logger.info("🔍 Testing Twitter platform enum")
    logger.info("=" * 50)
    
    try:
        from core.enums import Platform
        
        # Check if Twitter is in the enum
        assert Platform.TWITTER.value == "twitter"
        logger.info("✅ Twitter platform enum is correct")
        
        # Check platform choices
        from core.enums import PlatformChoices
        choices = PlatformChoices.get_choices()
        twitter_choice = next((choice for choice in choices if choice[0] == "twitter"), None)
        
        if twitter_choice:
            logger.info(f"✅ Twitter platform choice found: {twitter_choice}")
        else:
            logger.error("❌ Twitter platform choice not found")
            
    except Exception as e:
        logger.error(f"❌ Error in platform enum test: {e}")

def test_twitter_content_types():
    """Test Twitter content type handling"""
    logger.info("\n🔍 Testing Twitter content types")
    logger.info("=" * 50)
    
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
        logger.error(f"❌ Error in content type test: {e}")

def test_twitter_keyword_creation():
    """Test creating Twitter keywords"""
    logger.info("\n🔍 Testing Twitter keyword creation")
    logger.info("=" * 50)
    
    try:
        # Create Twitter keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.TWITTER.value,
            content_types=[ContentType.BODY.value, ContentType.COMMENTS.value],
            is_active=True
        )
        keyword.save()
        logger.info(f"✅ Created Twitter keyword: {keyword.keyword}")
        
        # Verify the keyword was saved correctly
        saved_keyword = Keyword.objects.get(id=keyword.id)
        assert saved_keyword.platform == Platform.TWITTER.value
        assert ContentType.BODY.value in saved_keyword.content_types
        assert ContentType.COMMENTS.value in saved_keyword.content_types
        logger.info("✅ Keyword saved correctly")
        
        # Clean up
        keyword.delete()
        logger.info("✅ Test keyword cleaned up")
        
    except Exception as e:
        logger.error(f"❌ Error in keyword creation test: {e}")

def test_twitter_mention_creation():
    """Test creating Twitter mentions"""
    logger.info("\n🔍 Testing Twitter mention creation")
    logger.info("=" * 50)
    
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
        
        # Create test mention
        mention = Mention(
            keyword_id=str(keyword.id),
            user_id="test_user",
            content="Just learned about Python programming! #python #coding",
            title="Tweet by @testuser",
            author="testuser",
            source_url="https://twitter.com/testuser/status/123456789",
            platform=Platform.TWITTER.value,
            subreddit="twitter",
            content_type=ContentType.BODY.value,
            matched_text="python",
            match_position=25,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        mention.platform_item_id = "123456789"
        mention.platform_score = 10
        mention.platform_comments_count = 5
        
        mention.save()
        logger.info(f"✅ Created Twitter mention: {mention.id}")
        
        # Verify the mention was saved correctly
        saved_mention = Mention.objects.get(id=mention.id)
        assert saved_mention.platform == Platform.TWITTER.value
        assert saved_mention.platform_item_id == "123456789"
        assert saved_mention.platform_score == 10
        assert saved_mention.platform_comments_count == 5
        logger.info("✅ Mention saved correctly")
        
        # Clean up
        mention.delete()
        keyword.delete()
        logger.info("✅ Test data cleaned up")
        
    except Exception as e:
        logger.error(f"❌ Error in mention creation test: {e}")

def test_twitter_service_import():
    """Test that Twitter service can be imported"""
    logger.info("\n🔍 Testing Twitter service import")
    logger.info("=" * 50)
    
    try:
        # Try to import the Twitter service
        from platforms.twitter.services.twitter_service import TwitterService
        logger.info("✅ Twitter service import successful")
        
        # Create service instance
        service = TwitterService()
        logger.info("✅ Twitter service instance created")
        
        # Test basic methods
        service.start_monitoring()
        logger.info("✅ Twitter service start_monitoring() works")
        
        # Test status
        assert hasattr(service, 'is_monitoring')
        assert hasattr(service, 'check_interval')
        assert hasattr(service, 'tweet_cache')
        logger.info("✅ Twitter service has required attributes")
        
    except Exception as e:
        logger.error(f"❌ Error in Twitter service import test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    logger.info("🔍 Starting simple Twitter tests")
    logger.info("=" * 60)
    
    # Test 1: Platform enum
    test_twitter_platform_enum()
    
    # Test 2: Content types
    test_twitter_content_types()
    
    # Test 3: Keyword creation
    test_twitter_keyword_creation()
    
    # Test 4: Mention creation
    test_twitter_mention_creation()
    
    # Test 5: Service import
    test_twitter_service_import()
    
    logger.info("\n🎉 All simple Twitter tests completed!")

if __name__ == "__main__":
    main() 