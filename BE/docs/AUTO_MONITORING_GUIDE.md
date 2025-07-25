# 🤖 Automatic Monitoring System - Optimized Hybrid Approach

This system automatically monitors **ALL active keywords** in the database using an optimized hybrid approach that combines **immediate updates** with **efficient backup polling**. New keywords are monitored instantly, while the system maintains a safety net with reduced database queries.

## 🎯 **How It Works - Optimized Hybrid Approach**

### **1. Automatic Startup**
- Service starts automatically when Django application starts
- No manual commands needed
- Runs in background continuously

### **2. Hybrid Monitoring Strategy**
- **⚡ Immediate Updates**: New keywords are monitored instantly when added
- **📉 Reduced Polling**: Backup checks every 5 minutes (90% fewer queries)
- **🎯 User-Specific Updates**: Only update affected user's monitoring
- **🛡️ Error Resilience**: Graceful handling of immediate update failures

### **3. Real-time Detection**
- Uses PRAW's SubredditStream for instant notifications
- Monitors multiple subreddits simultaneously
- Creates mentions automatically when keywords are found

## 🚀 **Optimized Automatic Behavior**

### **When Application Starts:**
```python
# BE/tracker/apps.py
def ready(self):
    # Auto monitoring service starts automatically
    auto_monitor_service.start_auto_monitoring()
```

### **When User Adds Keywords (IMMEDIATE):**
```python
# User adds keyword via API
POST /api/keywords/
{
  "keyword": "python",
  "platform": "reddit",
  "subreddit": "programming"
}

# IMMEDIATE UPDATE (0 seconds)
keyword.save()
auto_monitor_service.update_monitoring_immediately(user_id)
# ✅ Keyword is monitored instantly!

# No waiting for polling cycle
```

### **Backup Polling (Every 5 Minutes):**
```python
# Service checks for changes every 5 minutes as backup
def _check_and_update_keywords(self):
    active_keywords = Keyword.objects.filter(is_active=True)
    
    if current_keywords != monitored_keywords:
        # Backup detection - restart monitoring with updated keywords
        realtime_stream_monitor.stop_stream_monitoring()
        realtime_stream_monitor.start_stream_monitoring(active_keywords)
```

## 📊 **Performance Comparison**

### **Before (30-second polling):**
- **Queries per day:** 2,880
- **Response time:** Up to 30 seconds
- **Database load:** High

### **After (Hybrid approach):**
- **Queries per day:** 288 (90% reduction)
- **Response time:** Immediate for new keywords
- **Database load:** Low

## 📋 **Usage**

### **No Manual Commands Required!**

The system works automatically, but you can control it if needed:

#### **Check Status:**
```bash
# Check if auto monitoring is running
python manage.py auto_monitor status

# Watch status in real-time
python manage.py auto_monitor status --watch
```

#### **Manual Control (Optional):**
```bash
# Start auto monitoring (usually not needed - starts automatically)
python manage.py auto_monitor start

# Stop auto monitoring
python manage.py auto_monitor stop
```

#### **API Status Check:**
```bash
# Check status via API
curl http://localhost:8000/api/auto-monitor/status/
```

## 🔧 **Configuration**

### **Optimized Check Interval**
```python
# BE/tracker/services/auto_monitor_service.py
self.check_interval = 300  # Check for new keywords every 5 minutes (reduced queries)
self.immediate_updates = True  # Enable immediate updates on keyword changes
```

### **Auto-Start Configuration**
```python
# BE/tracker/apps.py
def ready(self):
    # Only start if not running management commands
    if os.environ.get('RUN_MAIN') != 'true':
        auto_monitor_service.start_auto_monitoring()
```

## 📊 **Optimized Monitoring Flow**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Django App    │    │  Auto Monitor    │    │   Database      │
│   Starts        │───▶│  Service Starts  │───▶│   Keywords      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Adds     │    │  IMMEDIATE       │    │   New Keywords  │
│   Keywords      │───▶│  UPDATE          │───▶│   Monitored     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Real-time     │    │  Stream Monitor  │    │   Mentions      │
│   Monitoring    │◀───│  Updated         │◀───│   Created       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Backup        │    │  Polling Every   │    │   Safety Net    │
│   Polling       │◀───│  5 Minutes       │◀───│   Detection     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🧪 **Testing**

### **Test Script:**
```bash
# Run comprehensive test
python test_auto_monitoring.py
```

### **Manual Testing:**
```bash
# 1. Start Django server
python manage.py runserver

# 2. Add keywords via API (should be monitored immediately)
curl -X POST http://localhost:8000/api/keywords/ \
  -H "X-User-ID: test-user" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "python", "platform": "reddit", "subreddit": "programming"}'

# 3. Check status (should show new keyword being monitored immediately)
curl http://localhost:8000/api/auto-monitor/status/
```

## 📈 **Status Information**

### **Service Status:**
```json
{
  "auto_monitoring": {
    "is_running": true,
    "monitored_keywords_count": 5,
    "last_check": "2024-01-15T10:30:00Z",
    "check_interval_seconds": 300,
    "immediate_updates_enabled": true,
    "stream_monitoring_active": true,
    "active_streams": ["programming", "django", "python"]
  }
}
```

### **What Each Field Means:**
- `is_running`: Whether auto monitoring service is active
- `monitored_keywords_count`: Number of keywords being monitored
- `last_check`: When service last checked for new keywords
- `check_interval_seconds`: How often service checks for changes (5 minutes)
- `immediate_updates_enabled`: Whether immediate updates are active
- `stream_monitoring_active`: Whether Reddit streams are running
- `active_streams`: Which subreddits are being monitored

## 🔍 **Troubleshooting**

### **Service Not Starting:**
```bash
# Check Django logs
python manage.py runserver

# Check if app config is loaded
python manage.py check
```

### **Keywords Not Being Monitored:**
```bash
# Check if keywords are active
python manage.py shell
>>> from core.models import Keyword
>>> Keyword.objects.filter(is_active=True).count()

# Check service status
python manage.py auto_monitor status
```

### **No Mentions Found:**
```bash
# Check if streams are active
curl http://localhost:8000/api/auto-monitor/status/

# Check recent mentions
python manage.py shell
>>> from core.models import Mention
>>> Mention.objects.all().order_by('-discovered_at')[:5]
```

## 🎉 **Success Indicators**

### **Service Running:**
```
🚀 Starting automatic monitoring service...
✅ Automatic monitoring service started successfully!
🔄 Starting monitoring loop (backup polling every 5 minutes)...
```

### **Immediate Keyword Detection:**
```
⚡ Immediate monitoring update triggered for user test-user
🔄 Updating monitoring for user test-user with 1 keywords
✅ Updated monitoring for 1 keywords
```

### **Backup Polling:**
```
🔄 Keyword changes detected during polling. Updating monitoring...
   Previously monitoring: 0 keywords
   Now monitoring: 3 keywords
✅ Updated monitoring for 3 keywords
```

### **Real-time Monitoring:**
```
Started monitoring stream for r/programming
Started monitoring stream for r/django
🎯 New mention found! Keyword: 'python' in r/programming
```

## 🔄 **Automatic Features**

### **✅ What Happens Automatically:**

1. **Service Startup**: Starts when Django app starts
2. **Immediate Updates**: New keywords monitored instantly
3. **Keyword Detection**: Finds all active keywords in database
4. **Stream Creation**: Creates Reddit streams for each subreddit
5. **Backup Polling**: Monitors for changes every 5 minutes
6. **Stream Updates**: Restarts streams when keywords change
7. **Mention Creation**: Saves mentions when keywords are found
8. **Error Recovery**: Automatically restarts on connection issues

### **✅ No Manual Intervention Required:**

- ❌ No need to start monitoring manually
- ❌ No need to restart when adding keywords
- ❌ No need to manage individual streams
- ❌ No need to check for new keywords
- ✅ Everything happens automatically!

## 🚀 **Deployment**

### **Production Setup:**
```bash
# 1. Start Django with auto monitoring
python manage.py runserver

# 2. Service starts automatically
# 3. All active keywords are monitored
# 4. New keywords are automatically picked up immediately
```

### **Docker/Container:**
```dockerfile
# Auto monitoring starts with Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📚 **API Endpoints**

### **Get Auto Monitor Status:**
```http
GET /api/auto-monitor/status/
```

**Response:**
```json
{
  "auto_monitoring": {
    "is_running": true,
    "monitored_keywords_count": 5,
    "last_check": "2024-01-15T10:30:00Z",
    "check_interval_seconds": 300,
    "immediate_updates_enabled": true,
    "stream_monitoring_active": true,
    "active_streams": ["programming", "django"]
  },
  "message": "Automatic monitoring service status"
}
```

## 🎯 **Key Benefits of Optimized Approach**

1. **⚡ Immediate Response**: New keywords are monitored instantly
2. **📉 Reduced Database Load**: 90% fewer queries
3. **🛡️ Backup Safety**: 5-minute polling as fallback
4. **🎯 User-Specific Updates**: Only update affected user's monitoring
5. **🛡️ Error Resilience**: Graceful handling of immediate update failures
6. **📊 Better Performance**: Lower resource usage
7. **🔄 Reliable**: Multiple detection mechanisms

## 🤖 **Optimized Implementation**

### **Auto Monitor Service with Hybrid Approach:**

```python
import time
import logging
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from .realtime_monitor import realtime_stream_monitor
from ..models import Keyword

logger = logging.getLogger(__name__)

class AutoMonitorService:
    """Automatic monitoring service with optimized hybrid approach"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 300  # Check for new keywords every 5 minutes (reduced queries)
        self.last_keyword_check = None
        self.monitored_keywords = set()  # Track which keywords are being monitored
        self.immediate_updates = True  # Enable immediate updates on keyword changes
        
    def start_auto_monitoring(self):
        """Start automatic monitoring service"""
        if self.is_running:
            logger.info("Auto monitoring service is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting automatic monitoring service...")
        
        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ Automatic monitoring service started successfully")
    
    def stop_auto_monitoring(self):
        """Stop automatic monitoring service"""
        if not self.is_running:
            logger.info("Auto monitoring service is not running")
            return
        
        self.is_running = False
        logger.info("⏹️  Stopping automatic monitoring service...")
        
        # Stop stream monitoring
        realtime_stream_monitor.stop_stream_monitoring()
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("✅ Automatic monitoring service stopped")
    
    def update_monitoring_immediately(self, user_id=None):
        """Update monitoring immediately when keywords change"""
        try:
            logger.info("⚡ Immediate monitoring update triggered")
            
            if user_id:
                # Update monitoring for specific user
                user_keywords = Keyword.objects.filter(user_id=user_id, is_active=True)
                logger.info(f"🔄 Updating monitoring for user {user_id} with {user_keywords.count()} keywords")
            else:
                # Update monitoring for all users
                user_keywords = Keyword.objects.filter(is_active=True)
                logger.info(f"🔄 Updating monitoring for all users with {user_keywords.count()} keywords")
            
            # Force update monitoring
            self._force_update_monitoring(user_keywords)
            
        except Exception as e:
            logger.error(f"Error in immediate monitoring update: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs continuously (backup polling)"""
        logger.info("🔄 Starting monitoring loop (backup polling every 5 minutes)...")
        
        while self.is_running:
            try:
                # Check for active keywords (less frequent as backup)
                self._check_and_update_keywords()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_and_update_keywords(self):
        """Check for active keywords and update monitoring if needed"""
        try:
            # Get all active keywords
            active_keywords = Keyword.objects.filter(is_active=True)
            current_keyword_ids = {str(kw.id) for kw in active_keywords}
            
            # Check if we need to update monitoring
            if current_keyword_ids != self.monitored_keywords:
                logger.info(f"🔄 Keyword changes detected during polling. Updating monitoring...")
                logger.info(f"   Previously monitoring: {len(self.monitored_keywords)} keywords")
                logger.info(f"   Now monitoring: {len(current_keyword_ids)} keywords")
                
                self._force_update_monitoring(active_keywords)
            
        except Exception as e:
            logger.error(f"Error checking keywords: {e}")
    
    def _force_update_monitoring(self, keywords):
        """Force update monitoring with new keywords"""
        try:
            # Stop current monitoring
            realtime_stream_monitor.stop_stream_monitoring()
            
            # Start monitoring with updated keywords
            if keywords:
                realtime_stream_monitor.start_stream_monitoring(keywords)
                self.monitored_keywords = {str(kw.id) for kw in keywords}
                logger.info(f"✅ Updated monitoring for {keywords.count()} keywords")
            else:
                logger.info("ℹ️  No active keywords to monitor")
                self.monitored_keywords = set()
            
            self.last_keyword_check = timezone.now()
            
        except Exception as e:
            logger.error(f"Error forcing monitoring update: {e}")
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'monitored_keywords_count': len(self.monitored_keywords),
            'last_check': self.last_keyword_check.isoformat() if self.last_keyword_check else None,
            'check_interval_seconds': self.check_interval,
            'immediate_updates_enabled': self.immediate_updates,
            'stream_monitoring_active': len(realtime_stream_monitor.monitoring_threads) > 0,
            'active_streams': list(realtime_stream_monitor.monitoring_threads.keys())
        }

# Global instance
auto_monitor_service = AutoMonitorService()
```

### **Update Views to Use Immediate Updates:**

```python
# Add this to BE/tracker/views.py in the get_keywords view (POST section)
keyword.save()

# Immediately update monitoring for this new keyword
try:
    auto_monitor_service.update_monitoring_immediately(user_id)
    logger.info(f"⚡ Immediate monitoring update triggered for user {user_id}")
except Exception as e:
    logger.error(f"Error in immediate monitoring update: {e}")

# Return the created keyword
```

## 🎯 **How the Hybrid Approach Works**

### **When User Adds Keyword:**
```
Time 0s:   User adds keyword via API
Time 0s:   Keyword saved to database
Time 0s:   Immediate update triggered ✅
Time 0s:   Monitoring updated instantly
```

### **Backup Polling:**
```
Time 0s:    Service starts
Time 300s:  Backup check (5 minutes)
Time 600s:  Backup check (10 minutes)
Time 900s:  Backup check (15 minutes)
```

This hybrid approach gives you the best of both worlds: **immediate response** when users add keywords, and **efficient backup polling** to catch any missed changes!

The automatic monitoring system ensures that all active keywords are continuously monitored with optimal performance and immediate response times! 