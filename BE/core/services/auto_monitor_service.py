import time
import logging
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from platforms.hackernews.services.hackernews_service import HackerNewsService
from ..models import Keyword, Mention
from ..enums import Platform

logger = logging.getLogger(__name__)

class AutoMonitorService:
    """Automatic monitoring service that continuously monitors all active keywords"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 300  # Check for new keywords every 5 minutes (optimized)
        self.last_keyword_check = None
        self.monitored_keywords = set()  # Track which keywords are being monitored
        self.hn_service = HackerNewsService()
        
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
                
                # Perform periodic monitoring for all platforms
                self._perform_periodic_monitoring()
                
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
    
    def _perform_periodic_monitoring(self):
        """Perform periodic monitoring for platforms that don't support real-time streaming"""
        try:
            # Get keywords for platforms that need periodic monitoring
            hn_keywords = Keyword.objects.filter(
                is_active=True,
                platform__in=[Platform.HACKERNEWS.value, Platform.ALL.value]
            )
            
            if hn_keywords:
                logger.info(f"🔍 Performing periodic HackerNews monitoring for {len(hn_keywords)} keywords")
                
                # Monitor HackerNews keywords
                hn_mentions = self.hn_service.monitor_keywords(hn_keywords)
                
                if hn_mentions:
                    logger.info(f"🎯 Found {len(hn_mentions)} new HackerNews mentions")
                    
                    # Save mentions and send notifications
                    for mention in hn_mentions:
                        try:
                            mention.save()
                            logger.info(f"💾 Saved HN mention: {mention.keyword_id} - {mention.title[:50]}...")
                            
                            # Send email notification
                            self._send_email_notification(mention)
                            
                        except Exception as e:
                            logger.error(f"Error saving HN mention: {e}")
                else:
                    logger.info("ℹ️  No new HackerNews mentions found")
            
        except Exception as e:
            logger.error(f"Error in periodic monitoring: {e}")
    
    def _send_email_notification(self, mention: Mention):
        """Send email notification for a mention"""
        try:
            from .email_service import email_notification_service
            email_notification_service.send_mention_notification(mention)
            logger.info(f"📧 Email notification sent for mention: {mention.keyword_id}")
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'monitored_keywords_count': len(self.monitored_keywords),
            'last_check': self.last_keyword_check,
            'check_interval': self.check_interval
        }

# Global instance
auto_monitor_service = AutoMonitorService() 