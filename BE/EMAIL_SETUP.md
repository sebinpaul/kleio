# Email Notification Setup Guide

This guide explains how to set up email notifications for Kleio using Resend.

## Prerequisites

1. **Resend Account**: Sign up at [resend.com](https://resend.com)
2. **Domain Verification**: Verify your domain in Resend dashboard
3. **API Key**: Generate an API key from Resend dashboard
4. **Django Users**: Ensure users have email addresses in Django User model

## Environment Variables

Add these environment variables to your `.env` file:

```bash
# Resend Configuration
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=notifications@yourdomain.com

# App Configuration
APP_URL=https://yourdomain.com
```

## Domain Setup

1. **Verify Domain**: In Resend dashboard, add and verify your domain
2. **From Email**: Use an email address from your verified domain (e.g., `notifications@yourdomain.com`)

## User Email Configuration

The system automatically gets user emails from the Django User model:

1. **Django User Model**: Ensure all users have valid email addresses
2. **User Profile Settings**: Users can control email notifications via UserProfile
3. **Automatic Lookup**: No manual email configuration needed

## Testing Email Notifications

Use the Django management command to test email notifications:

```bash
# Test with a real Django User ID
python manage.py test_email_notifications --user-id 1 --keyword "python"

# Test with different keyword
python manage.py test_email_notifications --user-id 1 --keyword "django"
```

**Note**: Replace `1` with an actual Django User ID that has a valid email address.

## Features

### Single Mention Notifications
- Sent immediately when a mention is found
- Includes keyword, platform, content type, and author
- Beautiful HTML template with responsive design
- Direct link to original content
- **Automatic user email lookup**

### Digest Notifications
- Grouped by keyword
- Multiple mentions in one email
- Reduces email frequency for active keywords
- Summary of all mentions found
- **Automatic user email lookup**

### Platform Support
- **Reddit**: Posts, comments, titles, body content
- **Hacker News**: Posts, comments
- **Twitter**: Tweets, replies
- **LinkedIn**: Posts, comments

### Content Types
- **Titles**: Post titles only
- **Body**: Post body content only
- **Comments**: Comment content only
- **Combined**: Any combination of the above

### User Control
- **Email Notifications**: Users can enable/disable via UserProfile
- **Notification Frequency**: Instant, hourly, or daily digests
- **Automatic Email Lookup**: No manual configuration needed

## Email Templates

The service includes beautiful, responsive HTML email templates:

- **Header**: Gradient background with app branding
- **Keyword Highlight**: Prominent display of the monitored keyword
- **Mention Card**: Clean layout with platform badges and content preview
- **Action Buttons**: Direct links to view original content
- **Footer**: Links to manage keywords and email preferences

## Error Handling

- Graceful handling of missing API keys
- Logging of all email operations
- **Automatic user email lookup with fallbacks**
- User notification preferences respected
- Retry logic for failed sends

## Customization

You can customize the email templates by modifying the `_generate_html_content` and `_generate_digest_html_content` methods in `EmailNotificationService`.

## Monitoring

Check the logs for email notification status:
- Success: `Email notification sent successfully`
- Errors: `Error sending email notification`
- Missing config: `RESEND_API_KEY not found`
- **User not found**: `User not found with ID: {user_id}`
- **No email**: `No email found for user {user_id}`
- **Notifications disabled**: `Email notifications disabled for user {user_id}`

## Security

- API keys are stored in environment variables
- No sensitive data in email content
- Secure HTTPS links to original content
- **User email privacy protection**
- **Automatic email lookup from Django User model** 