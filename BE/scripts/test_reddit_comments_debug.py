#!/usr/bin/env python
"""
Comprehensive test script for Reddit comment monitoring
"""
import os
import sys
import django
import time
import threading
from datetime import datetime

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
from core.enums import Platform, ContentType
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from core.services.matching_engine import GenericMatchingEngine
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_keyword_creation():
    """Test creating a keyword that monitors comments"""
    try:
        # Check if test keyword already exists
        existing_keyword = Keyword.objects.filter(keyword="testcomment").first()
        if existing_keyword:
            logger.info(f"Using existing keyword: {existing_keyword.keyword}")
            return existing_keyword
        
        # Create a test keyword that monitors comments
        keyword = Keyword(
            user_id="test_user",
            keyword="testcomment",
            platform=Platform.REDDIT.value,
            content_types=[ContentType.COMMENTS.value, ContentType.TITLES.value],
            is_active=True
        )
        keyword.save()
        
        logger.info(f"Created test keyword: {keyword.keyword}")
        logger.info(f"Content types: {keyword.content_types}")
        logger.info(f"Platform: {keyword.platform}")
        
        return keyword
        
    except Exception as e:
        logger.error(f"Error creating test keyword: {e}")
        return None

def test_matching_engine():
    """Test the matching engine with comment content"""
    try:
        matching_engine = GenericMatchingEngine()
        
        # Get the test keyword
        keyword = Keyword.objects.filter(keyword="testcomment").first()
        if not keyword:
            logger.error("Test keyword not found")
            return
        
        # Test comment content
        test_comment = "This is a test comment with testcomment keyword in it"
        
        # Check if keyword should monitor comments
        should_monitor = matching_engine.should_monitor_content(keyword, ContentType.COMMENTS.value)
        logger.info(f"Should monitor comments: {should_monitor}")
        
        if should_monitor:
            # Test matching
            match_result = matching_engine.match_keyword(keyword, test_comment, ContentType.COMMENTS.value)
            if match_result:
                logger.info(f"✅ Match found! Matched text: '{match_result.matched_text}'")
                logger.info(f"   Position: {match_result.position}")
                logger.info(f"   Confidence: {match_result.confidence}")
            else:
                logger.warning("❌ No match found")
        else:
            logger.warning("❌ Keyword is not configured to monitor comments")
            
    except Exception as e:
        logger.error(f"Error testing matching engine: {e}")

def test_stream_monitoring():
    """Test real-time stream monitoring"""
    try:
        logger.info("🚀 Testing Reddit stream monitoring...")
        
        # Get active keywords
        keywords = Keyword.objects.filter(is_active=True)
        logger.info(f"Found {len(keywords)} active keywords")
        
        # Start monitoring
        realtime_stream_monitor.start_stream_monitoring(keywords)
        
        logger.info("✅ Stream monitoring started")
        logger.info("📝 Now try posting a comment with 'testcomment' in it on Reddit")
        logger.info("⏰ Monitoring for 60 seconds...")
        
        # Monitor for 60 seconds
        time.sleep(60)
        
        # Check for mentions
        mentions = Mention.objects.filter(keyword_id__in=[str(kw.id) for kw in keywords])
        logger.info(f"Found {len(mentions)} total mentions")
        
        for mention in mentions:
            logger.info(f"  - {mention.title}: {mention.content[:50]}...")
        
        # Stop monitoring
        realtime_stream_monitor.stop_stream_monitoring()
        logger.info("⏹️ Stream monitoring stopped")
        
    except Exception as e:
        logger.error(f"Error testing stream monitoring: {e}")

def check_existing_mentions():
    """Check for existing mentions"""
    try:
        mentions = Mention.objects.all()
        logger.info(f"Found {len(mentions)} total mentions in database")
        
        for mention in mentions:
            logger.info(f"  - {mention.platform}: {mention.title[:50]}...")
            logger.info(f"    Content type: {mention.content_type}")
            logger.info(f"    Created: {mention.discovered_at}")
            
    except Exception as e:
        logger.error(f"Error checking mentions: {e}")

def main():
    """Main test function"""
    logger.info("🔍 Starting Reddit comment monitoring debug test")
    logger.info("=" * 60)
    
    # Test 1: Check existing mentions
    logger.info("\n1. Checking existing mentions...")
    check_existing_mentions()
    
    # Test 2: Test keyword creation
    logger.info("\n2. Testing keyword creation...")
    keyword = test_keyword_creation()
    
    # Test 3: Test matching engine
    logger.info("\n3. Testing matching engine...")
    test_matching_engine()
    
    # Test 4: Test stream monitoring
    logger.info("\n4. Testing stream monitoring...")
    test_stream_monitoring()
    
    logger.info("\n✅ Debug test completed!")

if __name__ == "__main__":
    main() 