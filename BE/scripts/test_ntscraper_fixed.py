#!/usr/bin/env python
"""
Test script to verify Ntscraper functionality with different configurations
"""
import os
import sys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ntscraper_with_skip_check():
    """Test Ntscraper with skip_instance_check=True"""
    logger.info("🔍 Testing Ntscraper with skip_instance_check=True")
    logger.info("=" * 60)
    
    try:
        from ntscraper import Nitter
        
        # Initialize scraper with skip_instance_check=True
        scraper = Nitter(log_level=1, skip_instance_check=True)
        logger.info("✅ Nitter instance created with skip_instance_check=True")
        
        # Test tweet search
        logger.info("\n1. Testing tweet search...")
        query = "python"
        tweets = scraper.get_tweets(query, mode='term', number=3)
        
        if tweets and 'tweets' in tweets:
            tweet_list = tweets['tweets']
            logger.info(f"✅ Found {len(tweet_list)} tweets for 'python'")
            
            for i, tweet in enumerate(tweet_list[:2]):  # Show first 2
                logger.info(f"   Tweet {i+1}: {tweet.get('text', '')[:50]}...")
                logger.info(f"   Author: @{tweet.get('user', {}).get('username', 'Unknown')}")
                logger.info(f"   Date: {tweet.get('date', 'Unknown')}")
        else:
            logger.warning("⚠️  No tweets found or unexpected response format")
        
    except Exception as e:
        logger.error(f"❌ Error with skip_instance_check: {e}")
        import traceback
        traceback.print_exc()

def test_ntscraper_with_specific_instance():
    """Test Ntscraper with a specific instance"""
    logger.info("\n🔍 Testing Ntscraper with specific instance")
    logger.info("=" * 60)
    
    try:
        from ntscraper import Nitter
        
        # Try with a specific instance
        scraper = Nitter(log_level=1, skip_instance_check=False)
        
        # Get available instances
        logger.info("Getting available instances...")
        instances = scraper.get_working_instances()
        logger.info(f"Found {len(instances)} working instances")
        
        if instances:
            # Use the first working instance
            instance = instances[0]
            logger.info(f"Using instance: {instance}")
            
            # Test with specific instance
            tweets = scraper.get_tweets("python", mode='term', number=2, instance=instance)
            
            if tweets and 'tweets' in tweets:
                tweet_list = tweets['tweets']
                logger.info(f"✅ Found {len(tweet_list)} tweets using specific instance")
            else:
                logger.warning("⚠️  No tweets found with specific instance")
        else:
            logger.error("❌ No working instances found")
        
    except Exception as e:
        logger.error(f"❌ Error with specific instance: {e}")

def test_ntscraper_manual_instance():
    """Test Ntscraper with manually specified instance"""
    logger.info("\n🔍 Testing Ntscraper with manual instance")
    logger.info("=" * 60)
    
    try:
        from ntscraper import Nitter
        
        # Try with a known working instance (if any)
        known_instances = [
            "https://nitter.net",
            "https://nitter.it",
            "https://nitter.pw",
            "https://nitter.1d4.us"
        ]
        
        for instance in known_instances:
            logger.info(f"Trying instance: {instance}")
            try:
                scraper = Nitter(log_level=1, skip_instance_check=True)
                tweets = scraper.get_tweets("python", mode='term', number=1, instance=instance)
                
                if tweets and 'tweets' in tweets and tweets['tweets']:
                    logger.info(f"✅ Success with instance: {instance}")
                    tweet_list = tweets['tweets']
                    logger.info(f"   Found {len(tweet_list)} tweets")
                    break
                else:
                    logger.info(f"⚠️  No tweets found with instance: {instance}")
                    
            except Exception as e:
                logger.info(f"❌ Failed with instance {instance}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error with manual instances: {e}")

def test_alternative_approach():
    """Test alternative approaches for Twitter scraping"""
    logger.info("\n🔍 Testing alternative approaches")
    logger.info("=" * 60)
    
    try:
        # Test 1: Try with different modes
        from ntscraper import Nitter
        scraper = Nitter(log_level=1, skip_instance_check=True)
        
        logger.info("1. Testing different search modes...")
        
        modes = ['term', 'hashtag', 'user']
        for mode in modes:
            try:
                if mode == 'user':
                    tweets = scraper.get_tweets("elonmusk", mode=mode, number=1)
                else:
                    tweets = scraper.get_tweets("python", mode=mode, number=1)
                
                if tweets and 'tweets' in tweets and tweets['tweets']:
                    logger.info(f"✅ Mode '{mode}' works")
                else:
                    logger.info(f"⚠️  Mode '{mode}' returned no tweets")
                    
            except Exception as e:
                logger.error(f"❌ Mode '{mode}' failed: {e}")
        
        # Test 2: Try with different parameters
        logger.info("\n2. Testing with different parameters...")
        
        try:
            tweets = scraper.get_tweets(
                "python", 
                mode='term', 
                number=1,
                language='en',
                replies=False
            )
            
            if tweets and 'tweets' in tweets and tweets['tweets']:
                logger.info("✅ Search with parameters works")
            else:
                logger.info("⚠️  Search with parameters returned no tweets")
                
        except Exception as e:
            logger.error(f"❌ Search with parameters failed: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error in alternative approach: {e}")

def main():
    """Main test function"""
    logger.info("🔍 Starting Ntscraper alternative tests")
    logger.info("=" * 60)
    
    # Test 1: Skip instance check
    test_ntscraper_with_skip_check()
    
    # Test 2: Specific instance
    test_ntscraper_with_specific_instance()
    
    # Test 3: Manual instances
    test_ntscraper_manual_instance()
    
    # Test 4: Alternative approaches
    test_alternative_approach()
    
    logger.info("\n🎉 All Ntscraper alternative tests completed!")

if __name__ == "__main__":
    main() 