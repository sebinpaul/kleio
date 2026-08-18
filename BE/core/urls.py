from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health', views.health_check, name='health_check'),

    # General keywords endpoints
    path('keywords', views.get_keywords, name='get_keywords'),
    path('keywords/analytics', views.keyword_analytics, name='keyword_analytics'),
    path('mentions', views.list_mentions, name='list_mentions'),
    path('mentions/<str:mention_id>', views.update_mention, name='update_mention'),
    path('user/notification-settings', views.user_notification_settings, name='user_notification_settings'),
    path('billing/status', views.billing_status, name='billing_status'),
    path('billing/sync', views.billing_sync, name='billing_sync'),
    path('billing/reactivate', views.billing_reactivate, name='billing_reactivate'),
    path('billing/checkout', views.billing_checkout, name='billing_checkout'),
    path('billing/portal', views.billing_portal, name='billing_portal'),
    path('webhooks/dodo', views.dodo_webhook, name='dodo_webhook'),
    path('keywords/<str:keyword_id>', views.update_keyword, name='update_keyword'),
    path('keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_keyword'),

    # Platform-specific endpoints
    path('platforms/<str:platform>/keywords', views.get_keywords, name='get_platform_keywords'),
    path('platforms/<str:platform>/mentions', views.list_mentions, name='list_platform_mentions'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>', views.update_keyword, name='update_platform_keyword'),
    path('platforms/<str:platform>/keywords/<str:keyword_id>/toggle', views.toggle_keyword, name='toggle_platform_keyword'),
]
