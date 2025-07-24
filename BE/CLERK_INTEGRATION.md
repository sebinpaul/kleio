# Clerk Integration Guide

This guide explains how to set up and use Clerk authentication with email notifications in Kleio.

## Prerequisites

1. **Clerk Account**: Sign up at [clerk.com](https://clerk.com)
2. **Clerk Application**: Create a new application in Clerk dashboard
3. **API Keys**: Get your Clerk secret key from the dashboard

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# Clerk Configuration
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here

# Email Configuration (existing)
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=notifications@yourdomain.com
APP_URL=https://yourdomain.com
```

## How It Works

### 1. User Authentication Flow
```
Frontend (Clerk) → Backend (Django) → Email Service (Clerk API)
```

1. **User signs up/logs in** via Clerk frontend
2. **Frontend sends requests** with `X-User-ID` header (Clerk user ID)
3. **Backend processes requests** using Clerk user ID
4. **Email service looks up email** via Clerk API using user ID
5. **Email notifications sent** to user's email address

### 2. Email Lookup Process
The email service follows this priority order:

1. **Clerk API** - Gets email from Clerk user data
2. **Django User Model** - Fallback for legacy numeric user IDs
3. **Error handling** - Logs errors and returns None

## Testing the Integration

### Test with Real Clerk User ID

```bash
# Test Clerk email integration
python manage.py test_clerk_email --clerk-user-id "user_2abc123def456" --keyword "python"

# Test regular email notifications
python manage.py test_email_notifications --user-id "user_2abc123def456" --keyword "django"
```

### Test Clerk Service Directly

```python
from tracker.services.clerk_service import clerk_user_service

# Get user email
email = clerk_user_service.get_user_email("user_2abc123def456")
print(f"User email: {email}")

# Get full user info
user_info = clerk_user_service.get_user_info("user_2abc123def456")
print(f"User info: {user_info}")
```

## Features

### ✅ What's Implemented

- **Clerk API Integration**: Direct email lookup from Clerk
- **Fallback Support**: Django User model as backup
- **Error Handling**: Comprehensive logging and error recovery
- **Email Priority**: Primary → Verified → First email
- **Testing Tools**: Management commands for testing

### 🔧 Email Priority Logic

1. **Primary Email**: Uses `primary_email_address_id` from Clerk
2. **Verified Email**: Falls back to first verified email address
3. **Any Email**: Uses first available email address
4. **Django Fallback**: Uses Django User model for numeric IDs

### 📧 Email Service Methods

```python
# Get user email (Clerk API + Django fallback)
email = email_notification_service.get_user_email(clerk_user_id)

# Send single mention notification
success = email_notification_service.send_mention_notification(mention)

# Send digest notification
success = email_notification_service.send_digest_notification(user_id, mentions=mentions)
```

## Troubleshooting

### Common Issues

1. **"CLERK_SECRET_KEY not configured"**
   - Check your `.env` file has `CLERK_SECRET_KEY`
   - Verify the key is correct in Clerk dashboard

2. **"User not found in Clerk"**
   - Verify the Clerk user ID is correct
   - Check if user exists in your Clerk application

3. **"No email addresses found"**
   - User may not have verified their email
   - Check Clerk dashboard for user email status

4. **"Clerk API error"**
   - Check network connectivity
   - Verify API key permissions
   - Check Clerk API status

### Debug Commands

```bash
# Test Clerk service directly
python manage.py test_clerk_email --clerk-user-id "your_user_id"

# Check logs for detailed error information
tail -f logs/django.log
```

## Security Considerations

- **API Key Security**: Keep `CLERK_SECRET_KEY` secure and never commit to version control
- **Rate Limiting**: Clerk API has rate limits, consider caching for high-traffic applications
- **Error Logging**: Sensitive information is logged, ensure proper log security
- **Fallback Security**: Django User model fallback maintains backward compatibility

## Performance Optimization

### Caching Strategy (Future Enhancement)

```python
# Example caching implementation
from django.core.cache import cache

def get_user_email_cached(user_id: str) -> Optional[str]:
    cache_key = f"user_email_{user_id}"
    email = cache.get(cache_key)
    
    if not email:
        email = clerk_user_service.get_user_email(user_id)
        if email:
            cache.set(cache_key, email, timeout=3600)  # Cache for 1 hour
    
    return email
```

## Migration from Hardcoded Emails

If you were using hardcoded emails for testing:

1. **Remove hardcoded values** from `email_service.py`
2. **Set up Clerk integration** as described above
3. **Test with real user IDs** using the test commands
4. **Update any test scripts** to use real Clerk user IDs

## Support

For issues with:
- **Clerk Integration**: Check this guide and test commands
- **Email Delivery**: Check Resend dashboard and logs
- **User Authentication**: Check Clerk dashboard and frontend logs 