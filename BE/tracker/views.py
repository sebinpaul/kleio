from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.http import JsonResponse
from django.utils import timezone
from .models import Keyword
import json

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def get_keywords(request, platform=None):
    """Get all keywords for a user or create a new keyword"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return Response({'error': 'X-User-ID header is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use platform from URL parameter or query parameter
    platform = platform or request.GET.get('platform')
    
    if request.method == 'POST':
        # Handle POST request (create keyword)
        data = request.data
        
        # Use platform from URL parameter or request data
        platform = platform or data.get('platform', 'reddit')
        
        # Validate required fields
        if not data.get('keyword'):
            return Response({'error': 'keyword is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new keyword
        try:
            keyword = Keyword(
                user_id=user_id,
                keyword=data.get('keyword'),
                platform=platform,
                subreddit=data.get('subreddit', ''),
                is_active=data.get('enabled', True),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            keyword.save()
            
            # Return the created keyword
            return Response({
                "id": str(keyword.id),
                "keyword": keyword.keyword,
                "userId": keyword.user_id,
                "platform": keyword.platform,
                "enabled": keyword.is_active,
                "createdAt": keyword.created_at.isoformat(),
                "updatedAt": keyword.updated_at.isoformat()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    else:
        # Handle GET request (get keywords)
        try:
            # Build query
            query = {'user_id': user_id}
            if platform:
                query['platform'] = platform
            
            # Get keywords from database
            keywords = Keyword.objects(**query).order_by('-created_at')
            
            # Convert to response format
            keywords_list = []
            for keyword in keywords:
                keywords_list.append({
                    "id": str(keyword.id),
                    "keyword": keyword.keyword,
                    "userId": keyword.user_id,
                    "platform": keyword.platform,
                    "enabled": keyword.is_active,
                    "createdAt": keyword.created_at.isoformat(),
                    "updatedAt": keyword.updated_at.isoformat()
                })
            
            return Response(keywords_list)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([AllowAny])
def update_keyword(request, keyword_id, platform=None):
    """Update or delete a keyword"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return Response({'error': 'X-User-ID header is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find the keyword
        keyword = Keyword.objects(id=keyword_id, user_id=user_id).first()
        if not keyword:
            return Response({'error': 'Keyword not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'DELETE':
            # Handle DELETE request
            keyword.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        else:
            # Handle PUT request (update keyword)
            data = request.data
            
            # Update fields
            if 'keyword' in data:
                keyword.keyword = data['keyword']
            if 'platform' in data:
                keyword.platform = data['platform']
            if 'subreddit' in data:
                keyword.subreddit = data['subreddit']
            if 'enabled' in data:
                keyword.is_active = data['enabled']
            
            keyword.updated_at = timezone.now()
            keyword.save()
            
            # Return the updated keyword
            return Response({
                "id": str(keyword.id),
                "keyword": keyword.keyword,
                "userId": keyword.user_id,
                "platform": keyword.platform,
                "enabled": keyword.is_active,
                "createdAt": keyword.created_at.isoformat(),
                "updatedAt": keyword.updated_at.isoformat()
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([AllowAny])
def toggle_keyword(request, keyword_id, platform=None):
    """Toggle keyword enabled status"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return Response({'error': 'X-User-ID header is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find the keyword
        keyword = Keyword.objects(id=keyword_id, user_id=user_id).first()
        if not keyword:
            return Response({'error': 'Keyword not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Toggle the status
        keyword.is_active = not keyword.is_active
        keyword.updated_at = timezone.now()
        keyword.save()
        
        # Return the updated keyword
        return Response({
            "id": str(keyword.id),
            "keyword": keyword.keyword,
            "userId": keyword.user_id,
            "platform": keyword.platform,
            "enabled": keyword.is_active,
            "createdAt": keyword.created_at.isoformat(),
            "updatedAt": keyword.updated_at.isoformat()
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 