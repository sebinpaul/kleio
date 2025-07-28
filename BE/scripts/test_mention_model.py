#!/usr/bin/env python
"""
Test script to verify the updated Mention model with generic platform-specific fields
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
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import MatchResult
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mention_model_fields():
    """Test the updated Mention model with generic platform-specific fields"""
    logger.info("🔍 Testing updated Mention model with generic platform-specific fields")
    logger.info("=" * 70)
    
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
        
        # Test 1: Create a HackerNews story mention
        logger.info("\n1. Testing HackerNews story mention...")
        hn_story_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="My YC app: Dropbox - Throw away your USB drive",
            title="My YC app: Dropbox - Throw away your USB drive",
            author="dhouston",
            source_url="https://news.ycombinator.com/item?id=8863",
            platform=Platform.HACKERNEWS.value,
            platform_specific_location="hackernews",
            subreddit="hackernews",  # Legacy field
            content_type=MentionContentType.TITLE.value,
            matched_text="Dropbox",
            match_position=15,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        hn_story_mention.platform_item_id = "8863"
        hn_story_mention.platform_score = 104
        hn_story_mention.platform_comments_count = 71
        
        # Legacy fields for backward compatibility
        hn_story_mention.hn_story_id = "8863"
        hn_story_mention.hn_points = 104
        hn_story_mention.hn_comments_count = 71
        
        hn_story_mention.save()
        logger.info(f"✅ Created HackerNews story mention: {hn_story_mention.id}")
        logger.info(f"   Platform: {hn_story_mention.platform}")
        logger.info(f"   Location: {hn_story_mention.platform_specific_location}")
        logger.info(f"   Item ID: {hn_story_mention.platform_item_id}")
        logger.info(f"   Score: {hn_story_mention.platform_score}")
        logger.info(f"   Comments: {hn_story_mention.platform_comments_count}")
        
        # Test 2: Create a HackerNews comment mention
        logger.info("\n2. Testing HackerNews comment mention...")
        hn_comment_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="This is a great Python library!",
            title="Comment on item 8863",
            author="pizza234",
            source_url="https://news.ycombinator.com/item?id=44694602",
            platform=Platform.HACKERNEWS.value,
            platform_specific_location="hackernews",
            subreddit="hackernews",  # Legacy field
            content_type=MentionContentType.COMMENT.value,
            matched_text="Python",
            match_position=10,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        hn_comment_mention.platform_item_id = "44694602"
        hn_comment_mention.platform_parent_id = "44694347"
        
        # Legacy fields for backward compatibility
        hn_comment_mention.hn_comment_id = "44694602"
        hn_comment_mention.hn_story_id = "44694347"
        
        hn_comment_mention.save()
        logger.info(f"✅ Created HackerNews comment mention: {hn_comment_mention.id}")
        logger.info(f"   Platform: {hn_comment_mention.platform}")
        logger.info(f"   Location: {hn_comment_mention.platform_specific_location}")
        logger.info(f"   Item ID: {hn_comment_mention.platform_item_id}")
        logger.info(f"   Parent ID: {hn_comment_mention.platform_parent_id}")
        
        # Test 3: Create a Reddit submission mention
        logger.info("\n3. Testing Reddit submission mention...")
        reddit_submission_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="Check out this amazing Python tutorial!",
            title="Amazing Python Tutorial",
            author="reddit_user",
            source_url="https://reddit.com/r/Python/comments/abc123",
            platform=Platform.REDDIT.value,
            platform_specific_location="Python",
            subreddit="Python",  # Legacy field
            content_type=MentionContentType.TITLE.value,
            matched_text="Python",
            match_position=0,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        reddit_submission_mention.platform_item_id = "abc123"
        reddit_submission_mention.platform_score = 150
        reddit_submission_mention.platform_comments_count = 25
        
        reddit_submission_mention.save()
        logger.info(f"✅ Created Reddit submission mention: {reddit_submission_mention.id}")
        logger.info(f"   Platform: {reddit_submission_mention.platform}")
        logger.info(f"   Location: {reddit_submission_mention.platform_specific_location}")
        logger.info(f"   Item ID: {reddit_submission_mention.platform_item_id}")
        logger.info(f"   Score: {reddit_submission_mention.platform_score}")
        logger.info(f"   Comments: {reddit_submission_mention.platform_comments_count}")
        
        # Test 4: Create a Reddit comment mention
        logger.info("\n4. Testing Reddit comment mention...")
        reddit_comment_mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content="I love Python for data science!",
            title="Comment on: Amazing Python Tutorial",
            author="reddit_commenter",
            source_url="https://reddit.com/r/Python/comments/abc123/def456",
            platform=Platform.REDDIT.value,
            platform_specific_location="Python",
            subreddit="Python",  # Legacy field
            content_type=MentionContentType.COMMENT.value,
            matched_text="Python",
            match_position=7,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now()
        )
        
        # Add platform-specific fields
        reddit_comment_mention.platform_item_id = "def456"
        reddit_comment_mention.platform_parent_id = "abc123"
        
        reddit_comment_mention.save()
        logger.info(f"✅ Created Reddit comment mention: {reddit_comment_mention.id}")
        logger.info(f"   Platform: {reddit_comment_mention.platform}")
        logger.info(f"   Location: {reddit_comment_mention.platform_specific_location}")
        logger.info(f"   Item ID: {reddit_comment_mention.platform_item_id}")
        logger.info(f"   Parent ID: {reddit_comment_mention.platform_parent_id}")
        
        # Test 5: Query mentions by platform
        logger.info("\n5. Testing queries by platform...")
        hn_mentions = Mention.objects.filter(platform=Platform.HACKERNEWS.value)
        reddit_mentions = Mention.objects.filter(platform=Platform.REDDIT.value)
        
        logger.info(f"✅ HackerNews mentions: {hn_mentions.count()}")
        logger.info(f"✅ Reddit mentions: {reddit_mentions.count()}")
        
        # Test 6: Query by platform-specific fields
        logger.info("\n6. Testing queries by platform-specific fields...")
        high_score_mentions = Mention.objects.filter(platform_score__gte=100)
        logger.info(f"✅ Mentions with score >= 100: {high_score_mentions.count()}")
        
        # Clean up test data
        logger.info("\n7. Cleaning up test data...")
        Mention.objects.filter(keyword_id=str(keyword.id)).delete()
        keyword.delete()
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 All Mention model tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Error testing Mention model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mention_model_fields() 