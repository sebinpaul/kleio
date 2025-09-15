from enum import Enum


class Platform(Enum):
    """Platform enumeration for supported platforms"""
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    ALL = "all"  # For keywords that monitor multiple platforms


class NotificationFrequency(Enum):
    """Notification frequency enumeration"""
    INSTANT = "instant"
    HOURLY = "hourly"
    DAILY = "daily"


class CaseSensitivity(Enum):
    """Case sensitivity options for keyword matching"""
    CASE_INSENSITIVE = "case_insensitive"
    CASE_SENSITIVE = "case_sensitive"
    SMART_CASE = "smart_case"


class MatchMode(Enum):
    """Matching modes for keyword detection"""
    EXACT = "exact"
    CONTAINS = "contains"
    WORD_BOUNDARY = "word_boundary"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class ContentType(Enum):
    """Content types that can be monitored"""
    TITLES = "titles"
    BODY = "body"
    COMMENTS = "comments"


class MentionContentType(Enum):
    """Content types for mentions (more specific)"""
    POST = "post"
    COMMENT = "comment"
    TITLE = "title"
    BODY = "body"


class PlatformChoices:
    """Helper class for Django choices"""
    REDDIT = (Platform.REDDIT.value, "Reddit")
    HACKERNEWS = (Platform.HACKERNEWS.value, "Hacker News")
    TWITTER = (Platform.TWITTER.value, "Twitter")
    LINKEDIN = (Platform.LINKEDIN.value, "LinkedIn")
    YOUTUBE = (Platform.YOUTUBE.value, "YouTube")
    ALL = (Platform.ALL.value, "All")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.REDDIT,
            cls.HACKERNEWS,
            cls.TWITTER,
            cls.LINKEDIN,
            cls.YOUTUBE,
            cls.ALL,
        ]


class NotificationFrequencyChoices:
    """Helper class for Django notification frequency choices"""
    INSTANT = (NotificationFrequency.INSTANT.value, "Instant")
    HOURLY = (NotificationFrequency.HOURLY.value, "Hourly")
    DAILY = (NotificationFrequency.DAILY.value, "Daily")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.INSTANT,
            cls.HOURLY,
            cls.DAILY,
        ]


class CaseSensitivityChoices:
    """Helper class for Django case sensitivity choices"""
    CASE_INSENSITIVE = (CaseSensitivity.CASE_INSENSITIVE.value, "Case Insensitive")
    CASE_SENSITIVE = (CaseSensitivity.CASE_SENSITIVE.value, "Case Sensitive")
    SMART_CASE = (CaseSensitivity.SMART_CASE.value, "Smart Case")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.CASE_INSENSITIVE,
            cls.CASE_SENSITIVE,
            cls.SMART_CASE,
        ]


class MatchModeChoices:
    """Helper class for Django match mode choices"""
    EXACT = (MatchMode.EXACT.value, "Exact Match")
    CONTAINS = (MatchMode.CONTAINS.value, "Contains")
    WORD_BOUNDARY = (MatchMode.WORD_BOUNDARY.value, "Word Boundary")
    STARTS_WITH = (MatchMode.STARTS_WITH.value, "Starts With")
    ENDS_WITH = (MatchMode.ENDS_WITH.value, "Ends With")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.EXACT,
            cls.CONTAINS,
            cls.WORD_BOUNDARY,
            cls.STARTS_WITH,
            cls.ENDS_WITH,
        ]


class ContentTypeChoices:
    """Helper class for Django content type choices"""
    TITLES = (ContentType.TITLES.value, "Post Titles")
    BODY = (ContentType.BODY.value, "Post Body")
    COMMENTS = (ContentType.COMMENTS.value, "Comments")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.TITLES,
            cls.BODY,
            cls.COMMENTS,
        ]


class MentionContentTypeChoices:
    """Helper class for Django mention content type choices"""
    POST = (MentionContentType.POST.value, "Post")
    COMMENT = (MentionContentType.COMMENT.value, "Comment")
    TITLE = (MentionContentType.TITLE.value, "Title")
    BODY = (MentionContentType.BODY.value, "Body")

    @classmethod
    def get_choices(cls):
        """Get choices for Django model fields"""
        return [
            cls.POST,
            cls.COMMENT,
            cls.TITLE,
            cls.BODY,
        ]


# Platform-specific content field mappings
PLATFORM_CONTENT_MAPPING = {
    Platform.REDDIT.value: {
        ContentType.TITLES.value: ['title'],
        ContentType.BODY.value: ['selftext'],
        ContentType.COMMENTS.value: ['body'],
    },
    Platform.HACKERNEWS.value: {
        ContentType.TITLES.value: ['title'],
        ContentType.BODY.value: ['text'],
        ContentType.COMMENTS.value: ['text'],
    },
    Platform.TWITTER.value: {
        ContentType.TITLES.value: ['text'],
        ContentType.BODY.value: ['text'],
        ContentType.COMMENTS.value: ['text'],
    },
    Platform.LINKEDIN.value: {
        ContentType.TITLES.value: ['text'],
        ContentType.BODY.value: ['text'],
        ContentType.COMMENTS.value: ['text'],
    },
    Platform.YOUTUBE.value: {
        ContentType.TITLES.value: ['title'],
        ContentType.BODY.value: ['description'],
        ContentType.COMMENTS.value: ['text'],
    }
}

# Default content types for each platform
DEFAULT_CONTENT_TYPES = {
    Platform.REDDIT.value: [ContentType.TITLES.value, ContentType.BODY.value, ContentType.COMMENTS.value],
    Platform.HACKERNEWS.value: [ContentType.TITLES.value, ContentType.BODY.value, ContentType.COMMENTS.value],
    Platform.TWITTER.value: [ContentType.TITLES.value, ContentType.BODY.value, ContentType.COMMENTS.value],
    Platform.LINKEDIN.value: [ContentType.TITLES.value, ContentType.BODY.value, ContentType.COMMENTS.value],
    Platform.YOUTUBE.value: [ContentType.TITLES.value, ContentType.BODY.value],
    Platform.ALL.value: [ContentType.TITLES.value, ContentType.BODY.value, ContentType.COMMENTS.value],
} 