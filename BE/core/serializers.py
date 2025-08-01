from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Keyword, Mention, RedditToken, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.Serializer):
    """Serializer for UserProfile model"""
    
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField()
    email_notifications = serializers.BooleanField(default=True)
    notification_frequency = serializers.ChoiceField(
        choices=[('instant', 'Instant'), ('hourly', 'Hourly'), ('daily', 'Daily')],
        default='instant'
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class KeywordSerializer(serializers.Serializer):
    """Serializer for Keyword model"""
    
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    keyword = serializers.CharField(max_length=255, required=True)
    platform = serializers.ChoiceField(
        choices=[('reddit', 'Reddit'), ('hackernews', 'Hacker News'), ('both', 'Both')],
        default='both'
    )
    subreddit = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    mention_count = serializers.SerializerMethodField()
    
    def get_mention_count(self, obj):
        """Get the count of mentions for this keyword"""
        return Mention.objects.filter(keyword_id=str(obj.id)).count()
    
    def create(self, validated_data):
        """Create a new keyword"""
        validated_data['user_id'] = self.context['request'].user.id
        return Keyword.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing keyword"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class KeywordCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating keywords"""
    
    keyword = serializers.CharField(max_length=255, required=True)
    platform = serializers.ChoiceField(
        choices=[('reddit', 'Reddit'), ('hackernews', 'Hacker News'), ('both', 'Both')],
        default='both'
    )
    subreddit = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    
    def create(self, validated_data):
        """Create a new keyword"""
        validated_data['user_id'] = self.context['request'].user.id
        return Keyword.objects.create(**validated_data)


class MentionSerializer(serializers.Serializer):
    """Serializer for Mention model"""
    
    id = serializers.CharField(read_only=True)
    keyword_id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    content = serializers.CharField()
    title = serializers.CharField(max_length=500, required=False, allow_blank=True)
    author = serializers.CharField(max_length=100, required=False, allow_blank=True)
    source_url = serializers.URLField()
    platform = serializers.ChoiceField(choices=[('reddit', 'Reddit'), ('hackernews', 'Hacker News')])
    subreddit = serializers.CharField(max_length=100, required=False, allow_blank=True)
    mention_date = serializers.DateTimeField(required=False)
    discovered_at = serializers.DateTimeField(read_only=True)
    email_sent = serializers.BooleanField(read_only=True)
    email_sent_at = serializers.DateTimeField(read_only=True)


class RedditTokenSerializer(serializers.Serializer):
    """Serializer for RedditToken model"""
    
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    access_token = serializers.CharField(write_only=True)
    refresh_token = serializers.CharField(required=False, allow_blank=True, write_only=True)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)


class EmailTestSerializer(serializers.Serializer):
    """Serializer for testing email functionality"""
    
    user_id = serializers.CharField(max_length=100)
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()


class RedditSearchRequestSerializer(serializers.Serializer):
    """Serializer for Reddit search requests"""
    
    query = serializers.CharField(max_length=255)
    subreddit = serializers.CharField(max_length=100, required=False, allow_blank=True)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=25)
    sort = serializers.ChoiceField(
        choices=['relevance', 'hot', 'top', 'new', 'comments'],
        default='relevance'
    )
    time_filter = serializers.ChoiceField(
        choices=['hour', 'day', 'week', 'month', 'year', 'all'],
        default='day'
    )


class HackerNewsSearchRequestSerializer(serializers.Serializer):
    """Serializer for HackerNews search requests"""
    
    query = serializers.CharField(max_length=255)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=25)


class InstantNotificationSerializer(serializers.Serializer):
    """Serializer for instant notification requests"""
    
    user_id = serializers.CharField(max_length=100)
    keyword = serializers.CharField(max_length=255)
    source_url = serializers.URLField()
    platform = serializers.ChoiceField(choices=['reddit', 'hackernews'])
    content = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    author = serializers.CharField(required=False, allow_blank=True)
