#!/usr/bin/env python
"""
Test script to verify that the keyword field is properly mandatory
"""
import os
import sys
import django

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from core.models import Keyword
from core.serializers import KeywordSerializer, KeywordCreateSerializer
from core.enums import Platform
from django.utils import timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_keyword_validation():
    """Test that keyword field is properly mandatory"""
    logger.info("🔍 Testing keyword field validation")
    logger.info("=" * 50)
    
    try:
        # Test 1: Valid keyword creation
        logger.info("\n1. Testing valid keyword creation...")
        valid_data = {
            'keyword': 'python',
            'platform': Platform.ALL.value,
            'user_id': 'test_user'
        }
        
        keyword = Keyword(**valid_data)
        keyword.save()
        logger.info(f"✅ Created valid keyword: {keyword.keyword}")
        
        # Test 2: Serializer validation with valid data
        logger.info("\n2. Testing serializer validation with valid data...")
        serializer = KeywordSerializer(data=valid_data)
        if serializer.is_valid():
            logger.info("✅ Serializer validation passed for valid data")
        else:
            logger.error(f"❌ Serializer validation failed: {serializer.errors}")
        
        # Test 3: Serializer validation with missing keyword
        logger.info("\n3. Testing serializer validation with missing keyword...")
        invalid_data = {
            'platform': Platform.ALL.value,
            'user_id': 'test_user'
        }
        
        serializer = KeywordSerializer(data=invalid_data)
        if not serializer.is_valid():
            logger.info("✅ Serializer correctly rejected missing keyword")
            logger.info(f"   Error: {serializer.errors}")
        else:
            logger.error("❌ Serializer should have rejected missing keyword")
        
        # Test 4: Model validation with empty keyword
        logger.info("\n4. Testing model validation with empty keyword...")
        try:
            empty_keyword = Keyword(
                keyword='',
                platform=Platform.ALL.value,
                user_id='test_user'
            )
            empty_keyword.save()
            logger.warning("⚠️  Model allowed empty keyword (this might be expected)")
        except Exception as e:
            logger.info(f"✅ Model correctly rejected empty keyword: {e}")
        
        # Test 5: Model validation with None keyword
        logger.info("\n5. Testing model validation with None keyword...")
        try:
            none_keyword = Keyword(
                keyword=None,
                platform=Platform.ALL.value,
                user_id='test_user'
            )
            none_keyword.save()
            logger.error("❌ Model should have rejected None keyword")
        except Exception as e:
            logger.info(f"✅ Model correctly rejected None keyword: {e}")
        
        # Test 6: CreateSerializer validation
        logger.info("\n6. Testing CreateSerializer validation...")
        create_serializer = KeywordCreateSerializer(data=valid_data)
        if create_serializer.is_valid():
            logger.info("✅ CreateSerializer validation passed for valid data")
        else:
            logger.error(f"❌ CreateSerializer validation failed: {create_serializer.errors}")
        
        # Test 7: CreateSerializer with missing keyword
        logger.info("\n7. Testing CreateSerializer with missing keyword...")
        create_serializer = KeywordCreateSerializer(data=invalid_data)
        if not create_serializer.is_valid():
            logger.info("✅ CreateSerializer correctly rejected missing keyword")
            logger.info(f"   Error: {create_serializer.errors}")
        else:
            logger.error("❌ CreateSerializer should have rejected missing keyword")
        
        # Clean up test data
        logger.info("\n8. Cleaning up test data...")
        Keyword.objects.filter(user_id='test_user').delete()
        logger.info("✅ Test data cleaned up")
        
        logger.info("\n🎉 Keyword validation tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Error testing keyword validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_keyword_validation() 