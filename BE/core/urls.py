from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health', views.health_check, name='health_check'),
    
    # Test endpoint
    path('test-keywords', views.test_keywords, name='test_keywords'),
    
    # General keywords endpoints
    path('keywords', views.get_keywords, name='get_keywords'),
    path('keywords/<str:keyword_id>', views.update_keyword, name='update_keyword'),
    path('keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_keyword'),
    
    # Platform-specific endpoints
    path('platforms/<str:platform>/keywords', views.get_keywords, name='get_platform_keywords'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>', views.update_keyword, name='update_platform_keyword'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_platform_keyword'),
    
    # Stream monitoring endpoints
    path('stream/start', views.start_stream_monitoring, name='start_stream_monitoring'),
    path('stream/stop', views.stop_stream_monitoring, name='stop_stream_monitoring'),
    path('stream/status', views.get_stream_status, name='get_stream_status'),
    
    # Auto monitoring endpoints
    path('auto-monitor/status', views.get_auto_monitor_status, name='get_auto_monitor_status'),
] 