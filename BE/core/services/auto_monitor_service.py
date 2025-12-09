import time
import logging
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from platforms.hackernews.services.hackernews_service import HackerNewsService
from platforms.twitter.services.twitter_service import twitter_service
from platforms.youtube.services.youtube_service import youtube_service
from platforms.facebook.services.facebook_service import facebook_service
from platforms.linkedin.services.linkedin_service import linkedin_service
from platforms.quora.services.quora_service import quora_service
from ..models import Keyword, Mention
from ..enums import Platform

logger = logging.getLogger(__name__)

class AutoMonitorService:
    """Automatic monitoring service that continuously monitors all active keywords"""
    
    def __init__(self):
        self.is_running = False
        self.monitor_thread = None
        self.check_interval = 5  # Check for new keywords every 5 seconds (optimized for HackerNews)
        self.last_keyword_check = None
        self.monitored_keywords = set()  # Track which keywords are being monitored
        self.hn_service = HackerNewsService()
        self.hn_keywords = set()  # Track HackerNews keywords separately
        self.twitter_keywords = set()  # Track Twitter keywords separately
        
    def start_auto_monitoring(self):
        """Start automatic monitoring service"""
        if self.is_running:
            logger.info("Auto monitoring service is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting automatic monitoring service...")
        
        # Initialize HackerNews monitoring
        self.hn_service.start_monitoring()
        
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
        
        # Stop HackerNews streaming
        self.hn_service.stop_real_time_streaming()
        
        # Stop Twitter streaming
        twitter_service.stop_stream_monitoring()
        # Stop YouTube streaming
        youtube_service.stop_stream_monitoring()
        # Stop Facebook/LinkedIn/Quora
        facebook_service.stop_stream_monitoring()
        linkedin_service.stop_stream_monitoring()
        quora_service.stop_stream_monitoring()
        
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
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
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
                self.hn_service.stop_real_time_streaming()
                twitter_service.stop_stream_monitoring()
                
                # Start monitoring with updated keywords
                if active_keywords:
                    # Separate keywords by platform
                    reddit_keywords = [kw for kw in active_keywords if kw.platform in [Platform.REDDIT.value, Platform.ALL.value]]
                    hn_keywords = [kw for kw in active_keywords if kw.platform in [Platform.HACKERNEWS.value, Platform.ALL.value]]
                    twitter_keywords = [kw for kw in active_keywords if kw.platform in [Platform.TWITTER.value, Platform.ALL.value]]
                    youtube_keywords = [kw for kw in active_keywords if kw.platform in [Platform.YOUTUBE.value, Platform.ALL.value]]
                    facebook_keywords = [kw for kw in active_keywords if kw.platform in [Platform.FACEBOOK.value, Platform.ALL.value]]
                    linkedin_keywords = [kw for kw in active_keywords if kw.platform in [Platform.LINKEDIN.value, Platform.ALL.value]]
                    quora_keywords = [kw for kw in active_keywords if kw.platform in [Platform.QUORA.value, Platform.ALL.value]]
                    
                    # Start Reddit monitoring
                    if reddit_keywords:
                        realtime_stream_monitor.start_stream_monitoring(reddit_keywords)
                        logger.info(f"✅ Updated Reddit monitoring for {len(reddit_keywords)} keywords")
                    
                    # Start HackerNews real-time streaming
                    if hn_keywords:
                        self.hn_service.start_real_time_streaming(hn_keywords)
                        logger.info(f"✅ Updated HackerNews streaming for {len(hn_keywords)} keywords")
                    
                    # Start Twitter monitoring
                    if twitter_keywords:
                        twitter_service.start_stream_monitoring(twitter_keywords)
                        logger.info(f"✅ Updated Twitter monitoring for {len(twitter_keywords)} keywords")
                    # Start YouTube monitoring
                    if youtube_keywords:
                        youtube_service.start_stream_monitoring(youtube_keywords)
                        logger.info(f"✅ Updated YouTube monitoring for {len(youtube_keywords)} keywords")
                    # Start Facebook monitoring
                    if facebook_keywords:
                        facebook_service.start_stream_monitoring(facebook_keywords)
                        logger.info(f"✅ Updated Facebook monitoring for {len(facebook_keywords)} keywords")
                    # Start LinkedIn monitoring
                    if linkedin_keywords:
                        linkedin_service.start_stream_monitoring(linkedin_keywords)
                        logger.info(f"✅ Updated LinkedIn monitoring for {len(linkedin_keywords)} keywords")
                    # Start Quora monitoring
                    if quora_keywords:
                        quora_service.start_stream_monitoring(quora_keywords)
                        logger.info(f"✅ Updated Quora monitoring for {len(quora_keywords)} keywords")
                    
                    self.monitored_keywords = current_keyword_ids
                else:
                    logger.info("ℹ️  No active keywords to monitor")
                    self.monitored_keywords = set()
                
                self.last_keyword_check = timezone.now()
            
        except Exception as e:
            logger.error(f"Error checking keywords: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
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
            'check_interval': self.check_interval,
            'hn_streaming': self.hn_service.is_streaming,
            'twitter_streaming': twitter_service.is_monitoring,
            'youtube_streaming': youtube_service.is_monitoring,
            'facebook_streaming': facebook_service.is_monitoring,
            'linkedin_streaming': linkedin_service.is_monitoring,
            'quora_streaming': quora_service.is_monitoring,
        }

# Global instance
auto_monitor_service = AutoMonitorService() 