from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import logging
from mongoengine.queryset.visitor import Q
from .models import Keyword, Mention, UserProfile
from .validators import (
    parse_enabled,
    parse_keyword_text,
    parse_platform,
    parse_platform_filters,
    parse_string_list,
    parse_case_sensitive,
    parse_match_mode,
    parse_content_types,
    validate_keyword_id,
)

logger = logging.getLogger(__name__)


def _user_id(request) -> str:
    return request.user.clerk_id


def _as_aware(dt):
    """Normalize datetimes for comparison (DB may store naive values)."""
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _calendar_date_range(start_date, num_days: int) -> list[str]:
    """Inclusive range of ISO date strings: start_date, start_date+1, ..."""
    return [
        (start_date + timedelta(days=i)).isoformat()
        for i in range(num_days)
    ]


def _trend(current: int, prior: int) -> str:
    if current > prior:
        return 'up'
    if current < prior:
        return 'down'
    return 'flat'


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request):
    return Response({'status': 'ok'})


def _keyword_response(keyword: Keyword) -> dict:
    return {
        "id": str(keyword.id),
        "keyword": keyword.keyword,
        "userId": keyword.user_id,
        "platform": keyword.platform,
        "platformSpecificFilters": keyword.platform_specific_filters or [],
        "excludedKeywords": keyword.excluded_keywords or [],
        "excludedSubreddits": keyword.excluded_subreddits or [],
        "includedUsers": keyword.included_users or [],
        "excludedUsers": keyword.excluded_users or [],
        "includedLanguages": keyword.included_languages or [],
        "excludedLanguages": keyword.excluded_languages or [],
        "caseSensitive": keyword.case_sensitive,
        "matchMode": keyword.match_mode,
        "contentTypes": keyword.content_types or [],
        "emailNotifications": getattr(keyword, 'email_notifications', True),
        "slackNotifications": getattr(keyword, 'slack_notifications', False),
        "enabled": keyword.is_active,
        "createdAt": keyword.created_at.isoformat(),
        "updatedAt": keyword.updated_at.isoformat(),
    }


def _parse_keyword_settings(data: dict, *, platform: str | None = None) -> tuple[dict | None, Response | None]:
    settings: dict = {}

    if 'platformSpecificFilters' in data:
        values, error = parse_platform_filters(data.get('platformSpecificFilters'))
        if error:
            return None, error
        settings['platform_specific_filters'] = values

    list_fields = {
        'excludedKeywords': 'excluded_keywords',
        'excludedSubreddits': 'excluded_subreddits',
        'includedUsers': 'included_users',
        'excludedUsers': 'excluded_users',
        'includedLanguages': 'included_languages',
        'excludedLanguages': 'excluded_languages',
    }
    for request_key, model_key in list_fields.items():
        if request_key in data:
            values, error = parse_string_list(data.get(request_key), request_key)
            if error:
                return None, error
            settings[model_key] = values

    if 'caseSensitive' in data:
        case_sensitive, error = parse_case_sensitive(data.get('caseSensitive'))
        if error:
            return None, error
        settings['case_sensitive'] = case_sensitive

    if 'matchMode' in data:
        match_mode, error = parse_match_mode(data.get('matchMode'))
        if error:
            return None, error
        settings['match_mode'] = match_mode

    if 'contentTypes' in data:
        content_types, error = parse_content_types(data.get('contentTypes'), platform=platform)
        if error:
            return None, error
        settings['content_types'] = content_types

    if 'emailNotifications' in data:
        email_notifications, error = parse_enabled(data.get('emailNotifications'))
        if error:
            return None, error
        settings['email_notifications'] = email_notifications

    if 'slackNotifications' in data:
        slack_notifications, error = parse_enabled(data.get('slackNotifications'))
        if error:
            return None, error
        settings['slack_notifications'] = slack_notifications

    return settings, None


@api_view(['GET', 'POST'])
def get_keywords(request, platform=None):
    """Get all keywords for a user or create a new keyword"""
    user_id = _user_id(request)
    list_platform = platform or request.GET.get('platform')

    if list_platform is not None:
        _, error = parse_platform(list_platform)
        if error:
            return error

    if request.method == 'POST':
        data = request.data

        keyword_text, error = parse_keyword_text(data.get('keyword'))
        if error:
            return error

        platform_value, error = parse_platform(
            data.get('platform'),
            url_platform=platform,
        )
        if error:
            return error

        platform_filters, error = parse_platform_filters(data.get('platformSpecificFilters', []))
        if error:
            return error

        enabled, error = parse_enabled(data.get('enabled', True))
        if error:
            return error

        case_sensitive, error = parse_case_sensitive(data.get('caseSensitive', False))
        if error:
            return error

        match_mode, error = parse_match_mode(data.get('matchMode'))
        if error:
            return error

        content_types, error = parse_content_types(data.get('contentTypes'), platform=platform_value)
        if error:
            return error

        email_notifications, error = parse_enabled(data.get('emailNotifications', True))
        if error:
            return error

        slack_notifications, error = parse_enabled(data.get('slackNotifications', False))
        if error:
            return error

        extra_settings, error = _parse_keyword_settings(data, platform=platform_value)
        if error:
            return error

        try:
            keyword = Keyword(
                user_id=user_id,
                keyword=keyword_text,
                platform=platform_value,
                platform_specific_filters=extra_settings.get('platform_specific_filters', platform_filters),
                case_sensitive=extra_settings.get('case_sensitive', case_sensitive),
                match_mode=extra_settings.get('match_mode', match_mode),
                content_types=extra_settings.get('content_types', content_types),
                excluded_keywords=extra_settings.get('excluded_keywords', []),
                excluded_subreddits=extra_settings.get('excluded_subreddits', []),
                included_users=extra_settings.get('included_users', []),
                excluded_users=extra_settings.get('excluded_users', []),
                included_languages=extra_settings.get('included_languages', []),
                excluded_languages=extra_settings.get('excluded_languages', []),
                email_notifications=extra_settings.get('email_notifications', email_notifications),
                slack_notifications=extra_settings.get('slack_notifications', slack_notifications),
                is_active=enabled,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            keyword.save()
            return Response(_keyword_response(keyword), status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Failed to create keyword for user %s", user_id)
            return Response(
                {'error': 'An internal error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    try:
        query = {'user_id': user_id}
        if list_platform:
            query['platform'] = list_platform

        keywords = Keyword.objects(**query).order_by('-created_at')
        return Response([_keyword_response(keyword) for keyword in keywords])
    except Exception:
        logger.exception("Failed to list keywords for user %s", user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['PUT', 'DELETE'])
def update_keyword(request, keyword_id, platform=None):
    """Update or delete a keyword"""
    user_id = _user_id(request)

    error = validate_keyword_id(keyword_id)
    if error:
        return error

    if platform is not None:
        _, error = parse_platform(platform, url_platform=platform)
        if error:
            return error

    try:
        keyword = Keyword.objects(id=keyword_id, user_id=user_id).first()
        if not keyword:
            return Response({'error': 'Keyword not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            keyword.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        data = request.data

        if 'keyword' in data:
            keyword_text, error = parse_keyword_text(data['keyword'])
            if error:
                return error
            keyword.keyword = keyword_text

        if 'platform' in data:
            platform_value, error = parse_platform(
                data['platform'],
                url_platform=platform,
            )
            if error:
                return error
            keyword.platform = platform_value

        if 'enabled' in data:
            enabled, error = parse_enabled(data['enabled'])
            if error:
                return error
            keyword.is_active = enabled

        extra_settings, error = _parse_keyword_settings(data, platform=keyword.platform)
        if error:
            return error
        for field, value in extra_settings.items():
            setattr(keyword, field, value)

        keyword.updated_at = timezone.now()
        keyword.save()
        return Response(_keyword_response(keyword))
    except Exception:
        logger.exception("Failed to update/delete keyword %s for user %s", keyword_id, user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['PATCH'])
def toggle_keyword(request, keyword_id, platform=None):
    """Toggle keyword enabled status"""
    user_id = _user_id(request)

    error = validate_keyword_id(keyword_id)
    if error:
        return error

    if platform is not None:
        _, error = parse_platform(platform, url_platform=platform)
        if error:
            return error

    try:
        keyword = Keyword.objects(id=keyword_id, user_id=user_id).first()
        if not keyword:
            return Response({'error': 'Keyword not found'}, status=status.HTTP_404_NOT_FOUND)

        keyword.is_active = not keyword.is_active
        keyword.updated_at = timezone.now()
        keyword.save()
        return Response(_keyword_response(keyword))
    except Exception:
        logger.exception("Failed to toggle keyword %s for user %s", keyword_id, user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def keyword_analytics(request):
    """Aggregate mention stats per keyword for the overview dashboard."""
    user_id = _user_id(request)
    try:
        days = int(request.GET.get('days', 30))
    except (TypeError, ValueError):
        days = 30
    days = min(max(days, 7), 90)
    sparkline_days = min(days, 14)

    platform_filter = request.GET.get('platform')
    if platform_filter:
        _, error = parse_platform(platform_filter)
        if error:
            return error

    try:
        keyword_query = Keyword.objects(user_id=user_id)
        if platform_filter:
            keyword_query = keyword_query.filter(platform=platform_filter)
        keywords = list(keyword_query.order_by('-created_at'))
        keyword_ids = {str(k.id) for k in keywords}

        now = timezone.now()
        # Rolling 7-day windows (timestamp-based, week-over-week).
        last_7_since = now - timedelta(days=7)
        prev_7_since = now - timedelta(days=14)

        # Calendar-day windows for sparkline + 14d summary (matches chart buckets).
        first_sparkline_date = (now - timedelta(days=sparkline_days - 1)).date()
        sparkline_dates = _calendar_date_range(first_sparkline_date, sparkline_days)
        sparkline_date_set = set(sparkline_dates)
        prior_sparkline_dates = _calendar_date_range(
            first_sparkline_date - timedelta(days=sparkline_days),
            sparkline_days,
        )
        prior_sparkline_date_set = set(prior_sparkline_dates)

        totals = defaultdict(int)
        last_7 = defaultdict(int)
        prev_7 = defaultdict(int)
        window_counts = defaultdict(lambda: defaultdict(int))
        last_mention_at = {}
        mentions_in_window = 0
        mentions_prior_window = 0

        for mention in Mention.objects(user_id=user_id):
            kid = mention.keyword_id
            if kid not in keyword_ids:
                continue
            discovered = _as_aware(mention.discovered_at)
            if discovered is None:
                continue

            totals[kid] += 1
            day_key = discovered.date().isoformat()

            if day_key in sparkline_date_set:
                window_counts[kid][day_key] += 1
                mentions_in_window += 1
            elif day_key in prior_sparkline_date_set:
                mentions_prior_window += 1

            if discovered >= last_7_since:
                last_7[kid] += 1
            elif discovered >= prev_7_since:
                prev_7[kid] += 1

            if kid not in last_mention_at or discovered > last_mention_at[kid]:
                last_mention_at[kid] = discovered

        keyword_rows = []
        total_mentions = 0
        mentions_last_7 = 0
        mentions_prior_7 = 0
        active_keywords = 0
        keywords_added_last_7 = 0
        keywords_added_prior_7 = 0

        for keyword in keywords:
            kid = str(keyword.id)
            created = _as_aware(keyword.created_at)
            if created and created >= last_7_since:
                keywords_added_last_7 += 1
            elif created and created >= prev_7_since:
                keywords_added_prior_7 += 1

            total = totals[kid]
            total_mentions += total
            m7 = last_7[kid]
            p7 = prev_7[kid]
            mentions_last_7 += m7
            mentions_prior_7 += p7
            if keyword.is_active:
                active_keywords += 1

            timeline = [
                {'date': d, 'count': window_counts[kid].get(d, 0)}
                for d in sparkline_dates
            ]
            window_total = sum(point['count'] for point in timeline)

            keyword_rows.append({
                **_keyword_response(keyword),
                'lastMentionAt': last_mention_at[kid].isoformat() if kid in last_mention_at else None,
                'totalMentions': total,
                'mentionsLast7Days': m7,
                'mentionsPrior7Days': p7,
                'mentionsInWindow': window_total,
                'trend': _trend(m7, p7),
                'timeline': timeline,
            })

        return Response({
            'summary': {
                'totalKeywords': len(keywords),
                'activeKeywords': active_keywords,
                'totalMentions': total_mentions,
                'mentionsLast7Days': mentions_last_7,
                'mentionsPrior7Days': mentions_prior_7,
                'mentionsInWindow': mentions_in_window,
                'mentionsPriorWindow': mentions_prior_window,
                'keywordsAddedLast7Days': keywords_added_last_7,
                'keywordsAddedPrior7Days': keywords_added_prior_7,
                'windowDays': sparkline_days,
            },
            'keywords': keyword_rows,
        })
    except Exception:
        logger.exception("Failed to build keyword analytics for user %s", user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _mention_response(mention: Mention, keyword_labels: dict[str, str] | None = None) -> dict:
    labels = keyword_labels or {}
    discovered = _as_aware(mention.discovered_at)
    mention_date = _as_aware(mention.mention_date)
    return {
        'id': str(mention.id),
        'keywordId': mention.keyword_id,
        'keyword': labels.get(mention.keyword_id, ''),
        'userId': mention.user_id,
        'content': mention.content or '',
        'title': mention.title or '',
        'author': mention.author or '',
        'sourceUrl': mention.source_url,
        'platform': mention.platform,
        'subreddit': mention.subreddit or '',
        'contentType': mention.content_type,
        'matchedText': mention.matched_text or '',
        'mentionDate': mention_date.isoformat() if mention_date else None,
        'discoveredAt': discovered.isoformat() if discovered else None,
        'platformScore': mention.platform_score,
        'platformCommentsCount': mention.platform_comments_count,
        'detectedLanguage': getattr(mention, 'detected_language', '') or '',
        'isRead': bool(getattr(mention, 'is_read', False)),
        'isArchived': bool(getattr(mention, 'is_archived', False)),
    }


@api_view(['GET'])
def list_mentions(request, platform=None):
    """List discovered mentions for the authenticated user."""
    user_id = _user_id(request)

    list_platform = platform or request.GET.get('platform')
    if list_platform is not None:
        _, error = parse_platform(list_platform)
        if error:
            return error

    keyword_id = request.GET.get('keywordId') or request.GET.get('keyword_id')
    if keyword_id:
        error = validate_keyword_id(keyword_id)
        if error:
            return error

    status_filter = (request.GET.get('status') or 'active').lower()
    if status_filter not in {'active', 'unread', 'archived', 'all'}:
        return Response({'error': 'Invalid status filter'}, status=status.HTTP_400_BAD_REQUEST)

    search_query = (request.GET.get('q') or '').strip()

    try:
        limit = int(request.GET.get('limit', 50))
    except (TypeError, ValueError):
        limit = 50
    limit = min(max(limit, 1), 100)

    try:
        offset = int(request.GET.get('offset', 0))
    except (TypeError, ValueError):
        offset = 0
    offset = max(offset, 0)

    try:
        query = {'user_id': user_id}
        if list_platform:
            query['platform'] = list_platform
        if keyword_id:
            query['keyword_id'] = keyword_id
        if status_filter == 'archived':
            query['is_archived'] = True
        elif status_filter != 'all':
            query['is_archived'] = False
            if status_filter == 'unread':
                query['is_read'] = False

        mentions_qs = Mention.objects(**query)
        if search_query:
            mentions_qs = mentions_qs.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )
        mentions_qs = mentions_qs.order_by('-discovered_at')
        total = mentions_qs.count()
        mentions = list(mentions_qs.skip(offset).limit(limit))

        keyword_ids = {m.keyword_id for m in mentions}
        keyword_labels = {}
        if keyword_ids:
            keyword_labels = {
                str(k.id): k.keyword
                for k in Keyword.objects(id__in=list(keyword_ids), user_id=user_id)
            }

        return Response({
            'mentions': [_mention_response(m, keyword_labels) for m in mentions],
            'total': total,
            'limit': limit,
            'offset': offset,
        })
    except Exception:
        logger.exception("Failed to list mentions for user %s", user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['PATCH'])
def update_mention(request, mention_id):
    """Mark a mention read or archived."""
    user_id = _user_id(request)

    error = validate_keyword_id(mention_id)
    if error:
        return error

    try:
        mention = Mention.objects(id=mention_id, user_id=user_id).first()
        if not mention:
            return Response({'error': 'Mention not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if 'isRead' in data:
            is_read, error = parse_enabled(data.get('isRead'))
            if error:
                return error
            mention.is_read = is_read

        if 'isArchived' in data:
            is_archived, error = parse_enabled(data.get('isArchived'))
            if error:
                return error
            mention.is_archived = is_archived
            if is_archived:
                mention.is_read = True

        mention.save()
        keyword = Keyword.objects(id=mention.keyword_id, user_id=user_id).first()
        labels = {mention.keyword_id: keyword.keyword} if keyword else {}
        return Response(_mention_response(mention, labels))
    except Exception:
        logger.exception("Failed to update mention %s for user %s", mention_id, user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET', 'PATCH'])
def user_notification_settings(request):
    """Global notification preferences for the authenticated user."""
    user_id = _user_id(request)

    try:
        profile = UserProfile.objects(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)

        if request.method == 'GET':
            return Response({
                'emailNotifications': profile.email_notifications,
                'notificationFrequency': profile.notification_frequency,
            })

        data = request.data
        if 'emailNotifications' in data:
            email_notifications, error = parse_enabled(data.get('emailNotifications'))
            if error:
                return error
            profile.email_notifications = email_notifications

        profile.save()
        return Response({
            'emailNotifications': profile.email_notifications,
            'notificationFrequency': profile.notification_frequency,
        })
    except Exception:
        logger.exception("Failed to update notification settings for user %s", user_id)
        return Response(
            {'error': 'An internal error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
