#!/usr/bin/env python
"""
Test script for real-time HackerNews monitoring
Inspired by the provided monitoring approach
"""
import os
import sys
import django
import time
from datetime import datetime

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.hackernews.services.hackernews_service import HackerNewsService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_realtime_monitoring():
    """Test real-time HackerNews monitoring"""
    
    # Create a test keyword
    keyword = Keyword(
        user_id="test_user",
        keyword="python",
        platform=Platform.HACKERNEWS.value,
        content_types=[ContentType.COMMENTS.value, ContentType.TITLES.value],
        is_active=True
    )
    keyword.save()
    
    logger.info(f"Created test keyword: {keyword.keyword}")
    
    # Initialize HackerNews service
    hn_service = HackerNewsService()
    
    # Start monitoring
    hn_service.start_monitoring()
    
    logger.info("Starting real-time HackerNews monitoring...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            # Monitor for mentions
            mentions = hn_service.monitor_keywords([keyword])
            
            if mentions:
                logger.info(f"🎯 Found {len(mentions)} new mentions!")
                for mention in mentions:
                    logger.info(f"   - {mention.title[:50]}...")
                    logger.info(f"     URL: {mention.source_url}")
            else:
                logger.info("No new mentions found")
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        logger.info("Stopping monitoring...")
    
    # Clean up
    keyword.delete()
    logger.info("Test completed")

if __name__ == "__main__":
    test_realtime_monitoring() 