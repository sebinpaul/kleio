from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    path('health', views.health_check, name='health_check_no_slash'),
    
    # Test endpoint
    path('test-keywords/', views.test_keywords, name='test_keywords'),
    path('test-keywords', views.test_keywords, name='test_keywords_no_slash'),
    
    # General keywords endpoints
    path('keywords/', views.get_keywords, name='get_keywords'),
    path('keywords', views.get_keywords, name='get_keywords_no_slash'),
    path('keywords/<str:keyword_id>/', views.update_keyword, name='update_keyword'),
    path('keywords/<str:keyword_id>', views.update_keyword, name='update_keyword_no_slash'),
    path('keywords/<str:keyword_id>/toggle/', views.toggle_keyword, name='toggle_keyword'),
    path('keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_keyword_no_slash'),
    
    # Platform-specific endpoints
    path('platforms/<str:platform>/keywords/', views.get_keywords, name='get_platform_keywords'),
    path('platforms/<str:platform>/keywords', views.get_keywords, name='get_platform_keywords_no_slash'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>/', views.update_keyword, name='update_platform_keyword'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>', views.update_keyword, name='update_platform_keyword_no_slash'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>/toggle/', views.toggle_keyword, name='toggle_platform_keyword'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_platform_keyword_no_slash'),
    
    # Stream monitoring endpoints
    path('stream/start/', views.start_stream_monitoring, name='start_stream_monitoring'),
    path('stream/start', views.start_stream_monitoring, name='start_stream_monitoring_no_slash'),
    path('stream/stop/', views.stop_stream_monitoring, name='stop_stream_monitoring'),
    path('stream/stop', views.stop_stream_monitoring, name='stop_stream_monitoring_no_slash'),
    path('stream/status/', views.get_stream_status, name='get_stream_status'),
    path('stream/status', views.get_stream_status, name='get_stream_status_no_slash'),
    
    # Auto monitoring endpoints
    path('auto-monitor/status/', views.get_auto_monitor_status, name='get_auto_monitor_status'),
    path('auto-monitor/status', views.get_auto_monitor_status, name='get_auto_monitor_status_no_slash'),
] 