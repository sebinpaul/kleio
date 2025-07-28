from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Called when Django starts"""
        import os
        
        # Only start auto-monitoring if not running management commands
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        try:
            # Import and start auto monitoring service
            from .services.auto_monitor_service import auto_monitor_service
            
            # Start automatic monitoring
            auto_monitor_service.start_auto_monitoring()
            logger.info("🚀 Auto monitoring service started from Django app config")
            
        except Exception as e:
            logger.error(f"Failed to start auto monitoring service: {e}")
