# 🚀 Real-time Reddit Monitoring with PRAW SubredditStream

This implementation uses PRAW's official `SubredditStream` for true real-time monitoring of Reddit submissions and comments. Based on the [PRAW documentation](https://praw.readthedocs.io/en/v7.1.4/code_overview/other/subredditstream.html?highlight=redditstream).

## 🎯 Features

- **True Real-time Monitoring**: Uses PRAW's `SubredditStream` for instant notifications
- **Multi-threaded**: Monitors multiple subreddits simultaneously
- **Duplicate Prevention**: Avoids saving duplicate mentions
- **Error Recovery**: Automatic restart on connection issues
- **API Integration**: REST endpoints to start/stop monitoring
- **Comprehensive Logging**: Detailed logs for debugging

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Django API    │    │  Stream Monitor  │    │   Reddit API    │
│                 │    │                  │    │                 │
│ • Start/Stop    │───▶│ • SubredditStream│───▶│ • Submissions   │
│ • Status Check  │    │ • Multi-threaded │    │ • Comments      │
│ • Keyword Mgmt  │    │ • Error Recovery │    │ • Real-time     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   MongoDB       │    │   Notifications  │
│                 │    │                  │
│ • Keywords      │    │ • Email/Slack    │
│ • Mentions      │    │ • Real-time      │
│ • User Data     │    │ • Instant        │
└─────────────────┘    └──────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd BE
pip install django-q praw
```

### 2. Start Real-time Monitoring

#### Option A: Management Command
```bash
# Start monitoring all active keywords
python manage.py start_stream_monitoring

# Monitor specific keywords
python manage.py start_stream_monitoring --keywords python django

# Monitor specific subreddit
python manage.py start_stream_monitoring --subreddit programming

# Monitor for specific user
python manage.py start_stream_monitoring --user-id user123
```

#### Option B: API Endpoints
```bash
# Start monitoring
curl -X POST http://localhost:8000/api/stream/start/ \
  -H "X-User-ID: your-user-id"

# Check status
curl http://localhost:8000/api/stream/status/

# Stop monitoring
curl -X POST http://localhost:8000/api/stream/stop/
```

#### Option C: Test Script
```bash
# Run comprehensive test
python test_stream_monitoring.py
```

## 📋 API Endpoints

### Start Stream Monitoring
```http
POST /api/stream/start/
Headers: X-User-ID: your-user-id
```

**Response:**
```json
{
  "status": "success",
  "message": "Real-time stream monitoring started",
  "keywords_count": 3,
  "keywords": [
    {
      "id": "keyword-id-1",
      "keyword": "python",
      "platform": "reddit",
      "subreddit": "programming"
    }
  ]
}
```

### Stop Stream Monitoring
```http
POST /api/stream/stop/
```

**Response:**
```json
{
  "status": "success",
  "message": "Real-time stream monitoring stopped"
}
```

### Get Stream Status
```http
GET /api/stream/status/
```

**Response:**
```json
{
  "is_monitoring": true,
  "active_threads": 2,
  "monitored_subreddits": ["programming", "django"]
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Reddit API Configuration
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent

# MongoDB Configuration
MONGODB_URI=your_mongodb_atlas_uri
MONGODB_DATABASE=your_database_name
```

### Django Settings
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'django_q',
    'tracker',
]

# Django Q Configuration (optional, for scheduled monitoring)
Q_CLUSTER = {
    'name': 'kleio_realtime_cluster',
    'workers': 2,
    'recycle': 500,
    'timeout': 90,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
    }
}
```

## 🧪 Testing

### 1. Basic Stream Test
```bash
# Test single subreddit stream
python test_stream_monitoring.py
```

### 2. API Testing
```bash
# Test API endpoints
curl -X POST http://localhost:8000/api/stream/start/ \
  -H "X-User-ID: test-user-123" \
  -H "Content-Type: application/json"

curl http://localhost:8000/api/stream/status/

curl -X POST http://localhost:8000/api/stream/stop/
```

### 3. Manual Testing
```bash
# Start monitoring and watch logs
python manage.py start_stream_monitoring --keywords python

# In another terminal, check for mentions
python manage.py shell
>>> from core.models import Mention
>>> Mention.objects.all().order_by('-discovered_at')[:5]
```

## 📊 Monitoring Dashboard

### Check Active Monitoring
```python
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor

# Check if monitoring is active
is_active = len(realtime_stream_monitor.monitoring_threads) > 0
print(f"Monitoring active: {is_active}")

# List monitored subreddits
subreddits = list(realtime_stream_monitor.monitoring_threads.keys())
print(f"Monitored subreddits: {subreddits}")
```

### View Recent Mentions
```python
from core.models import Mention

# Get recent mentions
recent_mentions = Mention.objects.all().order_by('-discovered_at')[:10]

for mention in recent_mentions:
    print(f"🎯 {mention.keyword_id} in r/{mention.subreddit}")
    print(f"   Title: {mention.title}")
    print(f"   URL: {mention.source_url}")
    print(f"   Found: {mention.discovered_at}")
    print()
```

## 🔍 How It Works

### 1. Stream Initialization
```python
# Get Reddit instance
reddit = reddit_service.get_reddit_instance()
subreddit = reddit.subreddit("programming")

# Start stream with skip_existing=True
for submission in subreddit.stream.submissions(skip_existing=True):
    # Process new submission
    check_for_keywords(submission)
```

### 2. Keyword Matching
```python
def check_submission_for_keywords(submission, keywords):
    submission_text = f"{submission.title} {submission.selftext}".lower()
    
    for keyword in keywords:
        if keyword.keyword.lower() in submission_text:
            create_mention(keyword, submission)
```

### 3. Mention Creation
```python
def create_mention_from_submission(keyword, submission):
    # Check for duplicates
    existing = Mention.objects.filter(
        source_url=f"https://reddit.com{submission.permalink}",
        keyword_id=str(keyword.id)
    ).first()
    
    if not existing:
        mention = Mention(
            keyword_id=str(keyword.id),
            user_id=keyword.user_id,
            content=submission.selftext or submission.title,
            title=submission.title,
            author=str(submission.author),
            source_url=f"https://reddit.com{submission.permalink}",
            platform='reddit',
            subreddit=submission.subreddit.display_name,
            mention_date=datetime.fromtimestamp(submission.created_utc)
        )
        mention.save()
```

## 🚨 Error Handling

### Automatic Recovery
- **Connection Errors**: Automatic retry after 30 seconds
- **Rate Limiting**: Built-in PRAW rate limiting
- **Thread Management**: Graceful shutdown on Ctrl+C

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Stream monitoring logs
logger.info(f"🎯 New mention found! Keyword: '{keyword.keyword}' in r/{subreddit}")
logger.error(f"Error in submissions stream: {e}")
```

## 📈 Performance

### Optimizations
- **Multi-threading**: Separate thread per subreddit
- **Duplicate Prevention**: Database-level duplicate checking
- **Efficient Queries**: Minimal database operations
- **Memory Management**: Proper cleanup of threads

### Rate Limits
- **Reddit API**: PRAW handles rate limiting automatically
- **Database**: Efficient queries with proper indexing
- **Memory**: Thread cleanup and garbage collection

## 🔧 Troubleshooting

### Common Issues

#### 1. No Mentions Found
```bash
# Check if keywords are active
python manage.py shell
>>> from core.models import Keyword
>>> Keyword.objects.filter(is_active=True).count()

# Check if monitoring is running
curl http://localhost:8000/api/stream/status/
```

#### 2. Connection Errors
```bash
# Check Reddit API credentials
python manage.py shell
>>> from django.conf import settings
>>> print(f"Client ID: {settings.REDDIT_CLIENT_ID[:10]}...")
>>> print(f"User Agent: {settings.REDDIT_USER_AGENT}")
```

#### 3. Thread Issues
```bash
# Restart monitoring
curl -X POST http://localhost:8000/api/stream/stop/
curl -X POST http://localhost:8000/api/stream/start/ \
  -H "X-User-ID: your-user-id"
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test stream manually
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
realtime_stream_monitor.start_stream_monitoring()
```

## 🎉 Success Indicators

### Real-time Monitoring Active
```
🚀 Starting Real-time Reddit Stream Monitoring...
✅ Found 3 keywords to monitor
  📌 'python' in r/programming
  📌 'django' in r/django
  📌 'flask' in r/python

🎯 Starting real-time stream monitoring...
Started monitoring stream for r/programming
Started monitoring stream for r/django
Started monitoring stream for r/python
Real-time stream monitoring started successfully
```

### New Mentions Found
```
🎯 New mention found! Keyword: 'python' in r/programming
   Title: Best Python libraries for data science in 2024
   URL: https://reddit.com/r/programming/comments/abc123
📧 Would send notification for mention: keyword-id-1
```

## 📚 References

- [PRAW SubredditStream Documentation](https://praw.readthedocs.io/en/v7.1.4/code_overview/other/subredditstream.html?highlight=redditstream)
- [PRAW Installation Guide](https://praw.readthedocs.io/en/latest/getting_started/installation.html)
- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [Django Q Documentation](https://django-q.readthedocs.io/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 