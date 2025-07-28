#!/usr/bin/env python
"""
Test script for HackerNews Firebase API real-time streaming
"""
import os
import sys
import django
import time
import asyncio
import aiohttp

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.hackernews.services.hackernews_service import HackerNewsService, HNConstants
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_firebase_api():
    """Test Firebase API endpoints directly"""
    logger.info("🔍 Testing HackerNews Firebase API endpoints")
    logger.info("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test maxitem endpoint
        logger.info("📊 Testing maxitem endpoint...")
        try:
            async with session.get(HNConstants.MAX_ITEM_URL) as response:
                response.raise_for_status()
                max_item = await response.json()
                logger.info(f"✅ Current max item ID: {max_item}")
        except Exception as e:
            logger.error(f"❌ Error fetching maxitem: {e}")
            return
        
        # Test item endpoint
        logger.info("📰 Testing item endpoint...")
        try:
            item_url = HNConstants.ITEM_URL.format(max_item)
            async with session.get(item_url) as response:
                response.raise_for_status()
                item = await response.json()
                if item:
                    logger.info(f"✅ Latest item: {item.get('type', 'unknown')} by {item.get('by', 'unknown')}")
                    if item.get('type') == 'story':
                        logger.info(f"   Title: {item.get('title', 'No title')[:50]}...")
                    elif item.get('type') == 'comment':
                        logger.info(f"   Text: {item.get('text', 'No text')[:50]}...")
                else:
                    logger.warning("⚠️ Latest item is null")
        except Exception as e:
            logger.error(f"❌ Error fetching item: {e}")

def test_keyword_creation():
    """Create a test keyword for HackerNews monitoring"""
    try:
        # Check if test keyword already exists
        existing_keyword = Keyword.objects.filter(keyword="python").first()
        if existing_keyword:
            logger.info(f"Using existing keyword: {existing_keyword.keyword}")
            return existing_keyword
        
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
        return keyword
        
    except Exception as e:
        logger.error(f"Error creating test keyword: {e}")
        return None

def test_real_time_streaming():
    """Test the real-time streaming functionality"""
    try:
        logger.info("🚀 Testing HackerNews real-time streaming...")
        
        # Get active keywords
        keywords = Keyword.objects.filter(is_active=True)
        logger.info(f"Found {len(keywords)} active keywords")
        
        # Initialize HackerNews service
        hn_service = HackerNewsService()
        hn_service.start_monitoring()
        
        # Start real-time streaming
        hn_service.start_real_time_streaming(keywords)
        
        logger.info("✅ Real-time streaming started")
        logger.info("📝 Now try posting content with 'python' on HackerNews")
        logger.info("⏰ Monitoring for 60 seconds...")
        
        # Monitor for 60 seconds
        time.sleep(60)
        
        # Stop streaming
        hn_service.stop_real_time_streaming()
        logger.info("⏹️ Real-time streaming stopped")
        
    except Exception as e:
        logger.error(f"Error testing real-time streaming: {e}")

async def main():
    """Main test function"""
    logger.info("🔍 Starting HackerNews Firebase API streaming test")
    logger.info("=" * 60)
    
    # Test 1: Test Firebase API endpoints
    logger.info("\n1. Testing Firebase API endpoints...")
    await test_firebase_api()
    
    # Test 2: Test keyword creation
    logger.info("\n2. Testing keyword creation...")
    keyword = test_keyword_creation()
    
    # Test 3: Test real-time streaming
    logger.info("\n3. Testing real-time streaming...")
    test_real_time_streaming()
    
    logger.info("\n✅ Firebase API streaming test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 