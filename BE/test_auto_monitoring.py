#!/usr/bin/env python
"""
Test script to demonstrate automatic monitoring service
"""
import os
import sys
import django
import time
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kleio_backend.settings')
django.setup()

from tracker.services.auto_monitor_service import auto_monitor_service
from tracker.models import Keyword

def test_auto_monitoring():
    """Test automatic monitoring service"""
    print("🚀 Testing Automatic Monitoring Service")
    print("=" * 60)
    
    # Start auto monitoring service
    print("1️⃣  Starting automatic monitoring service...")
    auto_monitor_service.start_auto_monitoring()
    
    # Wait a moment for service to start
    time.sleep(2)
    
    # Check initial status
    print("\n2️⃣  Checking initial status...")
    status = auto_monitor_service.get_status()
    print(f"   Service running: {status['is_running']}")
    print(f"   Monitored keywords: {status['monitored_keywords_count']}")
    print(f"   Stream monitoring: {status['stream_monitoring_active']}")
    
    # Create test keywords
    print("\n3️⃣  Creating test keywords...")
    test_keywords = [
        {
            'user_id': 'test-user-123',
            'keyword': 'python',
            'platform': 'reddit',
            'platformSpecificFilters': ['programming'],
            'is_active': True
        },
        {
            'user_id': 'test-user-456',
            'keyword': 'django',
            'platform': 'reddit',
            'platformSpecificFilters': ['django'],
            'is_active': True
        }
    ]
    
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
            print(f"   📌 Using existing keyword: '{keyword.keyword}' with filters: {keyword.platform_specific_filters}")
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
            print(f"   ✅ Created keyword: '{keyword.keyword}' with filters: {keyword.platform_specific_filters}")
        
        keywords.append(keyword)
    
    # Wait for auto monitoring to detect new keywords
    print("\n4️⃣  Waiting for auto monitoring to detect new keywords...")
    time.sleep(35)  # Wait longer than check_interval (30 seconds)
    
    # Check updated status
    print("\n5️⃣  Checking updated status...")
    status = auto_monitor_service.get_status()
    print(f"   Service running: {status['is_running']}")
    print(f"   Monitored keywords: {status['monitored_keywords_count']}")
    print(f"   Stream monitoring: {status['stream_monitoring_active']}")
    if status['active_streams']:
        print(f"   Active streams: {', '.join(status['active_streams'])}")
    
    # Test API endpoint
    print("\n6️⃣  Testing API endpoint...")
    try:
        response = requests.get('http://localhost:8000/api/auto-monitor/status/')
        if response.status_code == 200:
            data = response.json()
            print(f"   API Status: {data['auto_monitoring']['is_running']}")
            print(f"   API Monitored Keywords: {data['auto_monitoring']['monitored_keywords_count']}")
        else:
            print(f"   API Error: {response.status_code}")
    except Exception as e:
        print(f"   API Error: {e}")
    
    # Monitor for a few minutes
    print("\n7️⃣  Monitoring for 2 minutes...")
    print("   The service will automatically detect any new keywords added to the database")
    print("   Press Ctrl+C to stop early")
    
    try:
        for i in range(120):  # 2 minutes
            time.sleep(1)
            if i % 30 == 0:  # Print status every 30 seconds
                status = auto_monitor_service.get_status()
                print(f"   ⏱️  {120-i} seconds remaining - Monitoring {status['monitored_keywords_count']} keywords")
    except KeyboardInterrupt:
        print("\n   ⏹️  Stopped by user")
    
    # Stop auto monitoring
    print("\n8️⃣  Stopping automatic monitoring service...")
    auto_monitor_service.stop_auto_monitoring()
    
    print("\n✅ Automatic monitoring test completed!")
    print("\n🎯 Key Features Demonstrated:")
    print("   • Service starts automatically")
    print("   • Monitors all active keywords")
    print("   • Automatically detects new keywords")
    print("   • No manual intervention required")
    print("   • Real-time Reddit monitoring")

def test_management_command():
    """Test the management command"""
    print("\n🔧 Testing Management Command")
    print("=" * 40)
    
    print("Run these commands in another terminal:")
    print("  python manage.py auto_monitor start")
    print("  python manage.py auto_monitor status")
    print("  python manage.py auto_monitor status --watch")
    print("  python manage.py auto_monitor stop")

if __name__ == "__main__":
    print("🚀 Automatic Monitoring Service Test")
    print("=" * 60)
    
    test_auto_monitoring()
    test_management_command() 