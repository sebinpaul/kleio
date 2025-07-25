#!/usr/bin/env python
"""
Test script for Reddit comment monitoring
"""
import os
import sys
import django
from datetime import datetime

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_keyword_creation():
    """Test creating a keyword that monitors comments"""
    try:
        # Create a test keyword that monitors comments
        keyword = Keyword(
            user_id="test_user",
            keyword="test_keyword",
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
    """Test the matching engine with comments"""
    from core.services.matching_engine import GenericMatchingEngine
    
    matching_engine = GenericMatchingEngine()
    
    # Test keyword
    keyword = Keyword(
        user_id="test_user",
        keyword="python",
        platform=Platform.REDDIT.value,
        content_types=[ContentType.COMMENTS.value],
        is_active=True
    )
    
    # Test content
    test_content = "I love python programming language"
    
    # Test matching
    match_result = matching_engine.match_keyword(keyword, test_content, ContentType.COMMENTS.value)
    
    logger.info(f"Test content: {test_content}")
    logger.info(f"Keyword: {keyword.keyword}")
    logger.info(f"Match result: {match_result}")
    logger.info(f"Should monitor comments: {matching_engine.should_monitor_content(keyword, ContentType.COMMENTS.value)}")

def test_reddit_stream():
    """Test Reddit stream monitoring"""
    try:
        # Get active keywords
        keywords = Keyword.objects.filter(is_active=True)
        logger.info(f"Found {len(keywords)} active keywords")
        
        for keyword in keywords:
            logger.info(f"Keyword: {keyword.keyword}")
            logger.info(f"  Platform: {keyword.platform}")
            logger.info(f"  Content types: {keyword.content_types}")
            logger.info(f"  Active: {keyword.is_active}")
        
        # Start monitoring for a short time
        logger.info("Starting Reddit stream monitoring for 30 seconds...")
        realtime_stream_monitor.start_stream_monitoring(keywords)
        
        import time
        time.sleep(30)
        
        logger.info("Stopping Reddit stream monitoring...")
        realtime_stream_monitor.stop_stream_monitoring()
        
    except Exception as e:
        logger.error(f"Error testing Reddit stream: {e}")

if __name__ == "__main__":
    logger.info("=== Testing Reddit Comment Monitoring ===")
    
    # Test 1: Keyword creation
    logger.info("\n1. Testing keyword creation...")
    test_keyword = test_keyword_creation()
    
    # Test 2: Matching engine
    logger.info("\n2. Testing matching engine...")
    test_matching_engine()
    
    # Test 3: Reddit stream (only if you want to test live monitoring)
    # logger.info("\n3. Testing Reddit stream...")
    # test_reddit_stream()
    
    logger.info("\n=== Testing Complete ===") 