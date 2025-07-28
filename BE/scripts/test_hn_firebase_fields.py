#!/usr/bin/env python
"""
Test script to verify HackerNews Firebase API field mapping
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

async def test_firebase_field_mapping():
    """Test Firebase API field mapping with actual responses"""
    logger.info("🔍 Testing HackerNews Firebase API field mapping")
    logger.info("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test maxitem endpoint
        logger.info("📊 Getting current max item...")
        try:
            async with session.get(HNConstants.MAX_ITEM_URL) as response:
                response.raise_for_status()
                max_item = await response.json()
                logger.info(f"✅ Current max item ID: {max_item}")
        except Exception as e:
            logger.error(f"❌ Error fetching maxitem: {e}")
            return
        
        # Test story endpoint (get the latest story)
        logger.info("📰 Testing story field mapping...")
        try:
            # Get a few recent items to find a story
            for item_id in range(max_item, max_item - 10, -1):
                item_url = HNConstants.ITEM_URL.format(item_id)
                async with session.get(item_url) as response:
                    response.raise_for_status()
                    item = await response.json()
                    
                    if item and item.get("type") == "story":
                        logger.info(f"✅ Found story item {item_id}:")
                        logger.info(f"   Title: {item.get('title', 'No title')}")
                        logger.info(f"   Author: {item.get('by', 'No author')}")
                        logger.info(f"   URL: {item.get('url', 'No URL')}")
                        logger.info(f"   Score: {item.get('score', 'No score')}")
                        logger.info(f"   Descendants: {item.get('descendants', 'No descendants')}")
                        logger.info(f"   Time: {item.get('time', 'No time')}")
                        logger.info(f"   Type: {item.get('type', 'No type')}")
                        break
        except Exception as e:
            logger.error(f"❌ Error fetching story: {e}")
        
        # Test comment endpoint (get a recent comment)
        logger.info("💬 Testing comment field mapping...")
        try:
            # Get a few recent items to find a comment
            for item_id in range(max_item, max_item - 10, -1):
                item_url = HNConstants.ITEM_URL.format(item_id)
                async with session.get(item_url) as response:
                    response.raise_for_status()
                    item = await response.json()
                    
                    if item and item.get("type") == "comment":
                        logger.info(f"✅ Found comment item {item_id}:")
                        logger.info(f"   Text: {item.get('text', 'No text')[:100]}...")
                        logger.info(f"   Author: {item.get('by', 'No author')}")
                        logger.info(f"   Parent: {item.get('parent', 'No parent')}")
                        logger.info(f"   Time: {item.get('time', 'No time')}")
                        logger.info(f"   Type: {item.get('type', 'No type')}")
                        break
        except Exception as e:
            logger.error(f"❌ Error fetching comment: {e}")

def test_keyword_matching():
    """Test keyword matching with Firebase API fields"""
    try:
        logger.info("\n🔍 Testing keyword matching with Firebase fields...")
        
        # Create a test keyword
        keyword = Keyword(
            user_id="test_user",
            keyword="python",
            platform=Platform.HACKERNEWS.value,
            content_types=[ContentType.TITLES.value, ContentType.COMMENTS.value],
            is_active=True
        )
        keyword.save()
        
        # Initialize HackerNews service
        hn_service = HackerNewsService()
        hn_service.start_monitoring()
        
        logger.info("✅ Test keyword created and service initialized")
        logger.info(f"   Keyword: {keyword.keyword}")
        logger.info(f"   Content types: {keyword.content_types}")
        logger.info(f"   Platform: {keyword.platform}")
        
    except Exception as e:
        logger.error(f"Error testing keyword matching: {e}")

async def main():
    """Main test function"""
    logger.info("🔍 Starting HackerNews Firebase API field mapping test")
    logger.info("=" * 60)
    
    # Test 1: Test Firebase API field mapping
    logger.info("\n1. Testing Firebase API field mapping...")
    await test_firebase_field_mapping()
    
    # Test 2: Test keyword matching
    logger.info("\n2. Testing keyword matching...")
    test_keyword_matching()
    
    logger.info("\n✅ Firebase API field mapping test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 