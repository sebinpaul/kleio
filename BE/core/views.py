from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
import logging
from .models import Keyword
from .validators import (
    parse_enabled,
    parse_keyword_text,
    parse_platform,
    parse_platform_filters,
    validate_keyword_id,
)

logger = logging.getLogger(__name__)


def _user_id(request) -> str:
    return request.user.clerk_id


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
        "platformSpecificFilters": keyword.platform_specific_filters,
        "enabled": keyword.is_active,
        "createdAt": keyword.created_at.isoformat(),
        "updatedAt": keyword.updated_at.isoformat(),
    }


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

        try:
            keyword = Keyword(
                user_id=user_id,
                keyword=keyword_text,
                platform=platform_value,
                platform_specific_filters=platform_filters,
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

        if 'platformSpecificFilters' in data:
            platform_filters, error = parse_platform_filters(data['platformSpecificFilters'])
            if error:
                return error
            keyword.platform_specific_filters = platform_filters

        if 'enabled' in data:
            enabled, error = parse_enabled(data['enabled'])
            if error:
                return error
            keyword.is_active = enabled

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
