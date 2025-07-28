#!/usr/bin/env python
"""
Test script to verify MongoDB connection
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword, Mention
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    logger.info("🔍 Testing MongoDB Connection")
    logger.info("=" * 50)
    
    try:
        # Test 1: Check if we can query keywords
        logger.info("1. Testing Keyword model...")
        keyword_count = Keyword.objects.count()
        logger.info(f"✅ Found {keyword_count} keywords in database")
        
        # Test 2: Check if we can query mentions
        logger.info("2. Testing Mention model...")
        mention_count = Mention.objects.count()
        logger.info(f"✅ Found {mention_count} mentions in database")
        
        # Test 3: Try to create a test keyword
        logger.info("3. Testing keyword creation...")
        test_keyword = Keyword(
            user_id="test_user_connection",
            keyword="test_connection",
            platform="reddit",
            is_active=False  # Set to False so it doesn't interfere with monitoring
        )
        test_keyword.save()
        logger.info(f"✅ Created test keyword: {test_keyword.id}")
        
        # Test 4: Try to query the test keyword
        retrieved_keyword = Keyword.objects.get(id=test_keyword.id)
        logger.info(f"✅ Retrieved test keyword: {retrieved_keyword.keyword}")
        
        # Test 5: Clean up test keyword
        test_keyword.delete()
        logger.info("✅ Deleted test keyword")
        
        logger.info("\n✅ MongoDB connection test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

def test_auto_monitor_service():
    """Test auto monitor service initialization"""
    logger.info("\n🔍 Testing Auto Monitor Service")
    logger.info("=" * 50)
    
    try:
        from core.services.auto_monitor_service import auto_monitor_service
        
        # Test service initialization
        logger.info("1. Testing service initialization...")
        status = auto_monitor_service.get_status()
        logger.info(f"✅ Service status: {status}")
        
        # Test starting the service
        logger.info("2. Testing service start...")
        auto_monitor_service.start_auto_monitoring()
        logger.info("✅ Service started successfully")
        
        # Test stopping the service
        logger.info("3. Testing service stop...")
        auto_monitor_service.stop_auto_monitoring()
        logger.info("✅ Service stopped successfully")
        
        logger.info("\n✅ Auto monitor service test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Auto monitor service test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

def main():
    """Run all tests"""
    logger.info("🚀 Starting MongoDB Connection Tests")
    logger.info("=" * 60)
    
    # Test MongoDB connection
    connection_ok = test_mongodb_connection()
    
    if connection_ok:
        # Test auto monitor service
        service_ok = test_auto_monitor_service()
        
        if service_ok:
            logger.info("\n🎉 All tests passed!")
        else:
            logger.error("\n❌ Auto monitor service test failed")
    else:
        logger.error("\n❌ MongoDB connection test failed")

if __name__ == "__main__":
    main() 