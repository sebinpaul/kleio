#!/usr/bin/env python
"""
Test script to show HackerNews API URLs being called
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
from platforms.hackernews.services.hackernews_service import HackerNewsService, HNConstants
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hn_urls():
    """Test and show HackerNews API URLs"""
    
    # Create a test keyword
    keyword = Keyword(
        user_id="test_user",
        keyword="python",
        platform=Platform.HACKERNEWS.value,
        content_types=[ContentType.COMMENTS.value, ContentType.TITLES.value],
        is_active=True
    )
    
    # Initialize HackerNews service
    hn_service = HackerNewsService()
    hn_service.start_monitoring()
    
    logger.info("🔍 Testing HackerNews API URLs")
    logger.info("=" * 60)
    
    # Show the base URLs
    logger.info(f"Base URLs:")
    logger.info(f"  ALGOLIA_SEARCH_URL: {HNConstants.ALGOLIA_SEARCH_URL}")
    logger.info(f"  ALGOLIA_SEARCH_BY_DATE_URL: {HNConstants.ALGOLIA_SEARCH_BY_DATE_URL}")
    logger.info(f"  FIREBASE_ITEM_URL: {HNConstants.FIREBASE_ITEM_URL}")
    logger.info(f"  HN_BASE_URL: {HNConstants.HN_BASE_URL}")
    
    # Show the actual request URL that would be called
    start_time = hn_service.monitoring_start_time
    logger.info(f"\n📊 Monitoring start time: {start_time}")
    
    # Construct the search parameters
    search_params = {
        'query': keyword.keyword,
        'tags': '(story,comment)',
        'hitsPerPage': 50,
        'numericFilters': f'created_at_i>{start_time}'
    }
    
    logger.info(f"\n🔗 Search parameters:")
    for key, value in search_params.items():
        logger.info(f"  {key}: {value}")
    
    # Build the full URL
    import urllib.parse
    full_url = f"{HNConstants.ALGOLIA_SEARCH_BY_DATE_URL}?{urllib.parse.urlencode(search_params)}"
    
    logger.info(f"\n🌐 Full API URL that would be called:")
    logger.info(f"  {full_url}")
    
    # Test the actual API call
    logger.info(f"\n🚀 Testing actual API call...")
    try:
        response = hn_service._make_api_request(HNConstants.ALGOLIA_SEARCH_BY_DATE_URL, params=search_params)
        if response:
            logger.info(f"✅ API call successful!")
            logger.info(f"   Found {len(response.get('hits', []))} items")
            logger.info(f"   Processing time: {response.get('processingTimeMS', 'N/A')}ms")
        else:
            logger.error("❌ API call failed")
    except Exception as e:
        logger.error(f"❌ Error making API call: {e}")
    
    # Test recent stories URL
    logger.info(f"\n📰 Testing recent stories URL...")
    utc_now = time.time()
    one_day_ago = utc_now - (24 * 60 * 60)
    
    recent_params = {
        'tags': 'story',
        'hitsPerPage': 10,
        'numericFilters': f'created_at_i>{int(one_day_ago)}'
    }
    
    recent_url = f"{HNConstants.ALGOLIA_SEARCH_URL}?{urllib.parse.urlencode(recent_params)}"
    logger.info(f"Recent stories URL: {recent_url}")
    
    try:
        recent_response = hn_service._make_api_request(HNConstants.ALGOLIA_SEARCH_URL, params=recent_params)
        if recent_response:
            logger.info(f"✅ Recent stories API call successful!")
            logger.info(f"   Found {len(recent_response.get('hits', []))} recent stories")
        else:
            logger.error("❌ Recent stories API call failed")
    except Exception as e:
        logger.error(f"❌ Error making recent stories API call: {e}")

if __name__ == "__main__":
    test_hn_urls() 