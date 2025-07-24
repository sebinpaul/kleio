#!/usr/bin/env python
"""
Test script to verify real-time Reddit stream monitoring using PRAW SubredditStream
"""
import os
import sys
import django
import time
import threading

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kleio_backend.settings')
django.setup()

from tracker.services.realtime_monitor import realtime_stream_monitor
from tracker.models import Keyword

def test_stream_monitoring():
    """Test real-time stream monitoring"""
    print("🚀 Testing Real-time Reddit Stream Monitoring...")
    print("=" * 60)
    
    # Create test keywords
    test_keywords = [
        {
            'user_id': 'test-user-123',
            'keyword': 'python',
            'platform': 'reddit',
            'platformSpecificFilters': ['test'],
            'is_active': True
        },
        {
            'user_id': 'test-user-123',
            'keyword': 'django',
            'platform': 'reddit',
            'platformSpecificFilters': [],
            'is_active': True
        }
    ]
    
    # Create or get keywords
    keywords = []
    for kw_data in test_keywords:
        # Check if keyword exists
        existing_keyword = Keyword.objects.filter(
            user_id=kw_data['user_id'],
            keyword=kw_data['keyword'],
            platform=kw_data['platform']
        ).first()
        
        if existing_keyword:
            keyword = existing_keyword
            print(f"📌 Using existing keyword: '{keyword.keyword}' with filters: {keyword.platform_specific_filters}")
        else:
            # Create new keyword
            keyword = Keyword(
                user_id=kw_data['user_id'],
                keyword=kw_data['keyword'],
                platform=kw_data['platform'],
                platform_specific_filters=kw_data['platformSpecificFilters'],
                is_active=kw_data['is_active']
            )
            keyword.save()
            print(f"✅ Created keyword: '{keyword.keyword}' with filters: {keyword.platform_specific_filters}")
        
        keywords.append(keyword)
    
    print(f"\n🎯 Starting stream monitoring for {len(keywords)} keywords...")
    print("   This will monitor Reddit in real-time for new posts/comments")
    print("   Press Ctrl+C to stop after testing")
    print("-" * 60)
    
    try:
        # Start stream monitoring
        realtime_stream_monitor.start_stream_monitoring(keywords)
        
        # Monitor for 5 minutes
        print("⏰ Monitoring for 5 minutes...")
        for i in range(300):  # 5 minutes = 300 seconds
            time.sleep(1)
            if i % 30 == 0:  # Print status every 30 seconds
                remaining = (300 - i) // 60
                print(f"⏱️  {remaining} minutes remaining...")
        
        print("\n⏹️  Test completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping stream monitoring...")
    finally:
        # Stop monitoring
        realtime_stream_monitor.stop_stream_monitoring()
        print("✅ Stream monitoring stopped")
    
    # Show results
    print("\n📊 Test Results:")
    print("-" * 30)
    
    from tracker.models import Mention
    recent_mentions = Mention.objects.filter(
        keyword_id__in=[str(kw.id) for kw in keywords]
    ).order_by('-discovered_at')[:10]
    
    if recent_mentions:
        print(f"✅ Found {recent_mentions.count()} mentions during test:")
        for mention in recent_mentions:
            print(f"  🎯 '{mention.keyword_id}' in r/{mention.subreddit}")
            print(f"     Title: {mention.title[:50]}...")
            print(f"     URL: {mention.source_url}")
            print()
    else:
        print("⏳ No mentions found during test period")
        print("   This is normal if no new posts/comments contained your keywords")
    
    print("🎉 Stream monitoring test complete!")

def test_single_subreddit_stream():
    """Test monitoring a single subreddit stream"""
    print("\n🔍 Testing Single Subreddit Stream...")
    print("=" * 40)
    
    from tracker.services.reddit_service import RedditService
    
    reddit_service = RedditService()
    reddit = reddit_service.get_reddit_instance()
    
    # Test monitoring r/python for 1 minute
    subreddit = reddit.subreddit("test")
    
    print(f"🎯 Monitoring r/{subreddit.display_name} for 1 minute...")
    print("   Looking for posts containing 'python'...")
    
    start_time = time.time()
    post_count = 0
    
    try:
        for submission in subreddit.stream.submissions(skip_existing=True):
            post_count += 1
            print(f"📝 New post: {submission.title[:60]}...")
            print(f"   Score: {submission.score} | Comments: {submission.num_comments}")
            print(f"   URL: https://reddit.com{submission.permalink}")
            print()
            
            # Stop after 1 minute or 5 posts
            if time.time() - start_time > 60 or post_count >= 5:
                break
                
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    print(f"✅ Stream test completed! Found {post_count} new posts")

if __name__ == "__main__":
    print("🚀 PRAW SubredditStream Real-time Monitoring Test")
    print("=" * 60)
    
    # Test single subreddit stream first
    # test_single_subreddit_stream()
    
    # Test full monitoring system
    test_stream_monitoring() 