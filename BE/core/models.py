from mongoengine import Document, StringField, BooleanField, DateTimeField, ReferenceField, IntField, URLField, ListField, DictField, FloatField
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from .enums import (
    PlatformChoices, NotificationFrequencyChoices, CaseSensitivityChoices, 
    MatchModeChoices, ContentTypeChoices, MentionContentTypeChoices,
    DEFAULT_CONTENT_TYPES
)


class Keyword(Document):
    """Model for tracking keywords to monitor"""
    
    user_id = StringField(required=True, help_text="Django User ID")
    keyword = StringField(required=True, max_length=255, help_text="Keyword to monitor")
    platform = StringField(choices=PlatformChoices.get_choices(), default=PlatformChoices.ALL[0], max_length=20)
    platform_specific_filters = ListField(StringField(), default=list, help_text="Platform-specific filters (e.g., subreddits, accounts, channels)")
    excluded_keywords = ListField(StringField(), default=list, help_text="Keywords that suppress notifications when present alongside the main keyword")
    excluded_subreddits = ListField(StringField(), default=list, help_text="Subreddits to exclude from monitoring")
    included_users = ListField(StringField(), default=list, help_text="Only notify for posts/comments from these users (empty = all users)")
    excluded_users = ListField(StringField(), default=list, help_text="Never notify for posts/comments from these users")
    included_languages = ListField(StringField(), default=list, help_text="Only notify when content language matches (empty = all languages)")
    excluded_languages = ListField(StringField(), default=list, help_text="Never notify when content language matches")
    
    # Enhanced matching criteria
    case_sensitive = BooleanField(default=False, help_text="Whether keyword matching is case sensitive")
    match_mode = StringField(
        choices=MatchModeChoices.get_choices(),
        default=MatchModeChoices.CONTAINS[0],
        help_text="How to match the keyword in content"
    )
    content_types = ListField(
        StringField(),
        choices=ContentTypeChoices.get_choices(),
        default=lambda: DEFAULT_CONTENT_TYPES.get(PlatformChoices.ALL[0], [ContentTypeChoices.TITLES[0], ContentTypeChoices.BODY[0], ContentTypeChoices.COMMENTS[0]]),
        help_text="Which content types to monitor"
    )

    email_notifications = BooleanField(default=True, help_text="Send email alerts for mentions of this keyword")
    slack_notifications = BooleanField(default=False, help_text="Send Slack alerts for mentions of this keyword")
    
    is_active = BooleanField(default=True, help_text="Whether this keyword is actively being monitored")
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)
    
    meta = {
        'collection': 'keywords',
        'indexes': [
            ('user_id', 'keyword', 'platform'),
            ('user_id', 'is_active'),
            ('created_at',)
        ]
    }
    
    def __str__(self):
        return f"{self.keyword} ({self.platform}) - {self.user_id}"
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class Mention(Document):
    """Model for storing discovered mentions"""
    
    keyword_id = StringField(required=True, help_text="Keyword ID")
    user_id = StringField(required=True, help_text="Django User ID")
    
    # Content details
    content = StringField(required=True, help_text="The content where the keyword was found")
    title = StringField(max_length=500, help_text="Title of the post")
    author = StringField(max_length=100, help_text="Author of the post/comment")
    source_url = URLField(required=True, help_text="URL to the source post/comment")
    
    # Platform details
    platform = StringField(
        choices=[c for c in PlatformChoices.get_choices() if c[0] != 'all'],
        required=True
    )  # Exclude 'all' for mentions, include YouTube
    subreddit = StringField(max_length=100, help_text="Subreddit where mention was found (legacy field)")
    
    # Content type tracking
    content_type = StringField(
        choices=MentionContentTypeChoices.get_choices(),
        required=True,
        help_text="Type of content where keyword was found"
    )
    
    # Matching details for analytics
    matched_text = StringField(help_text="The exact text that matched the keyword")
    match_position = IntField(help_text="Position where keyword was found in content")
    match_confidence = FloatField(default=1.0, help_text="Confidence score of the match")
    detected_language = StringField(max_length=10, default='', help_text="Detected ISO 639-1 language code")
    
    # Timestamps
    mention_date = DateTimeField(help_text="When the mention was created on the platform")
    discovered_at = DateTimeField(default=timezone.now, help_text="When we discovered this mention")
    
    # Notification tracking
    email_sent = BooleanField(default=False, help_text="Whether email notification was sent")
    email_sent_at = DateTimeField(help_text="When email notification was sent")
    is_read = BooleanField(default=False, help_text="Whether the user has read this mention")
    is_archived = BooleanField(default=False, help_text="Whether the user archived this mention")
    
    # Platform-specific fields (generic)
    platform_item_id = StringField(help_text="Platform-specific item ID (e.g., story ID, post ID)")
    platform_score = IntField(help_text="Platform-specific score (e.g., upvotes, points)")
    platform_comments_count = IntField(help_text="Platform-specific comments count")
    
    meta = {
        'collection': 'mentions',
        'indexes': [
            ('user_id', 'platform', 'discovered_at'),
            ('keyword_id', 'discovered_at'),
            ('source_url',),
            ('discovered_at',),
            ('platform', 'platform_item_id'),
            ('user_id', 'is_archived', 'is_read'),
        ]
    }
    
    def __str__(self):
        return f"{self.keyword_id} on {self.platform} - {self.discovered_at.strftime('%Y-%m-%d %H:%M')}"
    
    def mark_email_sent(self):
        """Mark that email notification has been sent"""
        self.email_sent = True
        self.email_sent_at = timezone.now()
        self.save()


class RedditToken(Document):
    """Model for storing Reddit OAuth tokens"""
    
    user_id = StringField(required=True, help_text="Django User ID")
    access_token = StringField(required=True, help_text="Reddit OAuth access token")
    refresh_token = StringField(help_text="Reddit OAuth refresh token")
    expires_at = DateTimeField(required=True, help_text="When the access token expires")
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)
    
    meta = {
        'collection': 'reddit_tokens',
        'indexes': [
            ('user_id',),
            ('expires_at',)
        ]
    }
    
    def __str__(self):
        return f"Reddit token for {self.user_id}"
    
    @property
    def is_expired(self):
        """Check if the token is expired"""
        return timezone.now() >= self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid and not expired"""
        return not self.is_expired and bool(self.access_token)
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class UserProfile(Document):
    """Extended user profile for Kleio-specific settings"""
    
    user_id = StringField(required=True, help_text="Django User ID")
    email_notifications = BooleanField(default=True, help_text="Whether to send email notifications")
    notification_frequency = StringField(
        max_length=20,
        choices=NotificationFrequencyChoices.get_choices(),
        default=NotificationFrequencyChoices.INSTANT[0],
        help_text="How often to send notifications"
    )
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)
    
    meta = {
        'collection': 'user_profiles',
        'indexes': [
            ('user_id',),
            ('email_notifications',)
        ]
    }
    
    def __str__(self):
        return f"Profile for {self.user_id}"
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class MonitorCursor(Document):
    """Persistent cursor for per-user per-platform scanning progress."""

    user_id = StringField(required=True, help_text="Django User ID")
    platform = StringField(choices=[c for c in PlatformChoices.get_choices() if c[0] != 'all'], required=True)
    scope = StringField(required=True, help_text="Arbitrary scope key (e.g., keywordId, source URL, page id)")
    cursor = StringField(required=True, help_text="Cursor value (e.g., last seen ID/URL/ISO date)")
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'monitor_cursors',
        'indexes': [
            ('user_id', 'platform', 'scope'),
        ],
    }

    def __str__(self):
        return f"Cursor {self.platform}:{self.scope} for {self.user_id}"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)
