#!/usr/bin/env python
"""
Test script to verify both Reddit and HackerNews platforms are working
"""
import os
import sys
import django

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
from core.enums import Platform, ContentType, MentionContentType
from django.utils import timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mention_creation():
    """Test creating mentions for both platforms"""
    logger.info("🔍 Testing mention creation for both platforms")
    logger.info("=" * 50)
    
    try:
        # Create a test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.ALL.value,
            content_types=[ContentType.TITLES.value, ContentType.COMMENTS.value],
            is_active=True
        )
        keyword.save()
        logger.info(f"✅ Created test keyword: {keyword.keyword}")
        
        # Test 1: Create a HackerNews mention
        logger.info("\n1. Testing HackerNews mention creation...")
        hn_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="My YC app: Dropbox - Throw away your USB drive",
            title="My YC app: Dropbox - Throw away your USB drive",
            author="dhouston",
            source_url="https://news.ycombinator.com/item?id=8863",
            platform=Platform.HACKERNEWS.value,
            content_type=MentionContentType.TITLE.value,
            matched_text="Dropbox",
            match_position=15,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        hn_mention.platform_item_id = "8863"
        hn_mention.platform_score = 104
        hn_mention.platform_comments_count = 71
        
        hn_mention.save()
        logger.info(f"✅ Created HackerNews mention: {hn_mention.id}")
        logger.info(f"   Platform: {hn_mention.platform}")
        logger.info(f"   Item ID: {hn_mention.platform_item_id}")
        logger.info(f"   Score: {hn_mention.platform_score}")
        
        # Test 2: Create a Reddit mention
        logger.info("\n2. Testing Reddit mention creation...")
        reddit_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="Check out this amazing Python tutorial!",
            title="Amazing Python Tutorial",
            author="reddit_user",
            source_url="https://reddit.com/r/Python/comments/abc123",
            platform=Platform.REDDIT.value,
            subreddit="Python",
            content_type=MentionContentType.TITLE.value,
            matched_text="Python",
            match_position=0,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        reddit_mention.save()
        logger.info(f"✅ Created Reddit mention: {reddit_mention.id}")
        logger.info(f"   Platform: {reddit_mention.platform}")
        logger.info(f"   Subreddit: {reddit_mention.subreddit}")
        
        # Test 3: Query mentions by platform
        logger.info("\n3. Testing queries by platform...")
        hn_mentions = Mention.objects.filter(platform=Platform.HACKERNEWS.value)
        reddit_mentions = Mention.objects.filter(platform=Platform.REDDIT.value)
        
        logger.info(f"✅ HackerNews mentions: {hn_mentions.count()}")
        logger.info(f"✅ Reddit mentions: {reddit_mentions.count()}")
        
        # Test 4: Query by platform-specific fields
        logger.info("\n4. Testing queries by platform-specific fields...")
        high_score_mentions = Mention.objects.filter(platform_score__gte=100)
        logger.info(f"✅ Mentions with score >= 100: {high_score_mentions.count()}")
        
        # Clean up test data
        logger.info("\n5. Cleaning up test data...")
        Mention.objects.filter(keyword_id=str(keyword.id)).delete()
        keyword.delete()
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 Both platforms are working correctly!")
        
    except Exception as e:
        logger.error(f"❌ Error testing platforms: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mention_creation() 