from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.http import JsonResponse
from django.utils import timezone
from .models import Keyword
from .services.realtime_monitor import realtime_stream_monitor
from .services.auto_monitor_service import auto_monitor_service
from .enums import Platform
import json
import threading

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})

@api_view(['GET'])
def test_keywords(request):
    """Test endpoint to check if keywords can be queried without user authentication"""
    try:
        print("DEBUG: Testing keywords query without user filter")
        # Get all keywords (for testing only)
        keywords = Keyword.objects.all()
        count = keywords.count()
        print(f"DEBUG: Total keywords in database: {count}")
        
        return Response({
            'status': 'ok',
            'total_keywords': count,
            'message': 'Database connection and query working'
        })
    except Exception as e:
        print(f"DEBUG: Test keywords error: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return Response({
            'error': str(e),
            'error_type': str(type(e))
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def get_keywords(request, platform=None):
    """Get all keywords for a user or create a new keyword"""
    # Debug: Print request information
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    print(f"DEBUG: Request path: {request.path}")
    
    user_id = request.headers.get('X-User-ID')
    print(f"DEBUG: User ID from header: {user_id}")
    
    if not user_id:
        return Response({
            'error': 'X-User-ID header is required',
            'debug_info': {
                'available_headers': list(request.headers.keys()),
                'request_method': request.method,
                'request_path': request.path
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Use platform from URL parameter or query parameter
    platform = platform or request.GET.get('platform')
    
    if request.method == 'POST':
        # Handle POST request (create keyword)
        data = request.data
        
        # Use platform from URL parameter or request data
        platform = platform or data.get('platform', Platform.REDDIT.value)
        
        # Validate required fields
        if not data.get('keyword'):
            return Response({'error': 'keyword is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new keyword
        try:
            # Handle platform-specific filters
            platform_filters = data.get('platformSpecificFilters', [])
            if isinstance(platform_filters, str):
                # If it's a string, split by comma
                platform_filters = [f.strip() for f in platform_filters.split(',') if f.strip()]
            
            keyword = Keyword(
                user_id=user_id,
                keyword=data.get('keyword'),
                platform=platform,
                platform_specific_filters=platform_filters,
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
                "platformSpecificFilters": keyword.platform_specific_filters,
                "enabled": keyword.is_active,
                "createdAt": keyword.created_at.isoformat(),
                "updatedAt": keyword.updated_at.isoformat()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"DEBUG: POST error: {str(e)}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Response({
                'error': str(e),
                'error_type': str(type(e)),
                'debug_info': 'Check server logs for more details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    else:
        # Handle GET request (get keywords)
        try:
            print(f"DEBUG: Building query for user_id: {user_id}")
            # Build query
            query = {'user_id': user_id}
            if platform:
                query['platform'] = platform
            
            print(f"DEBUG: Final query: {query}")
            
            # Get keywords from database
            keywords = Keyword.objects(**query).order_by('-created_at')
            print(f"DEBUG: Found {keywords.count()} keywords")
            
            # Convert to response format
            keywords_list = []
            for keyword in keywords:
                keywords_list.append({
                    "id": str(keyword.id),
                    "keyword": keyword.keyword,
                    "userId": keyword.user_id,
                    "platform": keyword.platform,
                    "platformSpecificFilters": keyword.platform_specific_filters,
                    "enabled": keyword.is_active,
                    "createdAt": keyword.created_at.isoformat(),
                    "updatedAt": keyword.updated_at.isoformat()
                })
            
            print(f"DEBUG: Returning {len(keywords_list)} keywords")
            return Response(keywords_list)
            
        except Exception as e:
            print(f"DEBUG: GET error: {str(e)}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Response({
                'error': str(e),
                'error_type': str(type(e)),
                'debug_info': 'Check server logs for more details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            if 'platformSpecificFilters' in data:
                platform_filters = data['platformSpecificFilters']
                if isinstance(platform_filters, str):
                    # If it's a string, split by comma
                    platform_filters = [f.strip() for f in platform_filters.split(',') if f.strip()]
                keyword.platform_specific_filters = platform_filters
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
                "platformSpecificFilters": keyword.platform_specific_filters,
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
            "platformSpecificFilters": keyword.platform_specific_filters,
            "enabled": keyword.is_active,
            "createdAt": keyword.created_at.isoformat(),
            "updatedAt": keyword.updated_at.isoformat()
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['POST'])
@permission_classes([AllowAny])
def start_stream_monitoring(request):
    """Start real-time stream monitoring for a user's keywords"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return Response({'error': 'X-User-ID header is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get user's active keywords
        keywords = Keyword.objects.filter(user_id=user_id, is_active=True)
        
        if not keywords:
            return Response({
                'error': 'No active keywords found for user',
                'user_id': user_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Start stream monitoring in a separate thread
        def start_monitoring():
            realtime_stream_monitor.start_stream_monitoring(keywords)
        
        monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
        monitoring_thread.start()
        
        return Response({
            'status': 'success',
            'message': 'Real-time stream monitoring started',
            'keywords_count': keywords.count(),
            'keywords': [
                {
                    'id': str(kw.id),
                    'keyword': kw.keyword,
                    'platform': kw.platform,
                    'platformSpecificFilters': kw.platform_specific_filters
                }
                for kw in keywords
            ]
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def stop_stream_monitoring(request):
    """Stop real-time stream monitoring"""
    try:
        realtime_stream_monitor.stop_stream_monitoring()
        
        return Response({
            'status': 'success',
            'message': 'Real-time stream monitoring stopped'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_stream_status(request):
    """Get current stream monitoring status"""
    try:
        is_monitoring = len(realtime_stream_monitor.monitoring_threads) > 0
        
        return Response({
            'is_monitoring': is_monitoring,
            'active_threads': len(realtime_stream_monitor.monitoring_threads),
            'monitored_subreddits': list(realtime_stream_monitor.monitoring_threads.keys())
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

@api_view(['GET'])
@permission_classes([AllowAny])
def get_auto_monitor_status(request):
    """Get automatic monitoring service status"""
    try:
        status = auto_monitor_service.get_status()
        
        return Response({
            'auto_monitoring': status,
            'message': 'Automatic monitoring service status'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 