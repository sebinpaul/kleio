#!/usr/bin/env python
"""
Test script to demonstrate HackerNews API logging
"""
import os
import sys
import django
import time
import asyncio

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.hackernews.services.hackernews_service import HackerNewsService
import logging

# Set up logging to see all the API requests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_logging():
    """Test the new API logging functionality"""
    try:
        logger.info("🚀 Testing HackerNews API logging...")
        
        # Create a test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.HACKERNEWS.value,
            content_types=[ContentType.COMMENTS.value, ContentType.TITLES.value],
            is_active=True
        )
        keyword.save()
        
        # Initialize HackerNews service
        hn_service = HackerNewsService()
        hn_service.start_monitoring()
        
        # Start real-time streaming
        hn_service.start_real_time_streaming([keyword])
        
        logger.info("✅ Real-time streaming started with detailed logging")
        logger.info("📊 You should now see detailed logs for:")
        logger.info("   - MaxItem API requests every 2 seconds")
        logger.info("   - Individual item API requests when new items are found")
        logger.info("   - Processing details for each item")
        logger.info("⏰ Monitoring for 30 seconds...")
        
        # Monitor for 30 seconds
        time.sleep(30)
        
        # Stop streaming
        hn_service.stop_real_time_streaming()
        logger.info("⏹️ Real-time streaming stopped")
        
    except Exception as e:
        logger.error(f"Error testing API logging: {e}")

if __name__ == "__main__":
    test_api_logging() 