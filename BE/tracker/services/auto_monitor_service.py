import time
import logging
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from .realtime_monitor import realtime_stream_monitor
from ..models import Keyword

logger = logging.getLogger(__name__)

class AutoMonitorService:
    """Automatic monitoring service that continuously monitors all active keywords"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 30  # Check for new keywords every 30 seconds
        self.last_keyword_check = None
        self.monitored_keywords = set()  # Track which keywords are being monitored
        
    def start_auto_monitoring(self):
        """Start automatic monitoring service"""
        if self.is_running:
            logger.info("Auto monitoring service is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting automatic monitoring service...")
        
        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ Automatic monitoring service started successfully")
    
    def stop_auto_monitoring(self):
        """Stop automatic monitoring service"""
        if not self.is_running:
            logger.info("Auto monitoring service is not running")
            return
        
        self.is_running = False
        logger.info("⏹️  Stopping automatic monitoring service...")
        
        # Stop stream monitoring
        realtime_stream_monitor.stop_stream_monitoring()
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("✅ Automatic monitoring service stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs continuously"""
        logger.info("🔄 Starting monitoring loop...")
        
        while self.is_running:
            try:
                # Check for active keywords
                self._check_and_update_keywords()
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_and_update_keywords(self):
        """Check for active keywords and update monitoring if needed"""
        try:
            # Get all active keywords
            active_keywords = Keyword.objects.filter(is_active=True)
            current_keyword_ids = {str(kw.id) for kw in active_keywords}
            
            # Check if we need to update monitoring
            if current_keyword_ids != self.monitored_keywords:
                logger.info(f"🔄 Keyword changes detected. Updating monitoring...")
                logger.info(f"   Previously monitoring: {len(self.monitored_keywords)} keywords")
                logger.info(f"   Now monitoring: {len(current_keyword_ids)} keywords")
                
                # Stop current monitoring
                realtime_stream_monitor.stop_stream_monitoring()
                
                # Start monitoring with updated keywords
                if active_keywords:
                    realtime_stream_monitor.start_stream_monitoring(active_keywords)
                    self.monitored_keywords = current_keyword_ids
                    logger.info(f"✅ Updated monitoring for {len(active_keywords)} keywords")
                else:
                    logger.info("ℹ️  No active keywords to monitor")
                    self.monitored_keywords = set()
                
                self.last_keyword_check = timezone.now()
            
        except Exception as e:
            logger.error(f"Error checking keywords: {e}")
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'monitored_keywords_count': len(self.monitored_keywords),
            'last_check': self.last_keyword_check.isoformat() if self.last_keyword_check else None,
            'check_interval_seconds': self.check_interval,
            'stream_monitoring_active': len(realtime_stream_monitor.monitoring_threads) > 0,
            'active_streams': list(realtime_stream_monitor.monitoring_threads.keys())
        }

# Global instance
auto_monitor_service = AutoMonitorService() 