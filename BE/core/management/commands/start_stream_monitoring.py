from django.core.management.base import BaseCommand
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from core.models import Keyword
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start real-time Reddit stream monitoring using PRAW SubredditStream'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keywords',
            nargs='+',
            help='Specific keywords to monitor (optional)',
        )
        parser.add_argument(
            '--subreddit',
            type=str,
            help='Specific subreddit to monitor (optional)',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='User ID to monitor keywords for (optional)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Real-time Reddit Stream Monitoring...')
        )
        
        try:
            # Get keywords to monitor
            keywords = self._get_keywords_to_monitor(options)
            
            if not keywords:
                self.stdout.write(
                    self.style.WARNING('No active keywords found to monitor')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Found {keywords.count()} keywords to monitor')
            )
            
            # Display keywords being monitored
            for keyword in keywords:
                filters = keyword.platform_specific_filters or ['all']
                self.stdout.write(f"  📌 '{keyword.keyword}' with filters: {filters}")
            
            self.stdout.write(
                self.style.SUCCESS('\n🎯 Starting real-time stream monitoring...')
            )
            self.stdout.write(
                self.style.WARNING('Press Ctrl+C to stop monitoring')
            )
            
            # Start stream monitoring
            realtime_stream_monitor.start_stream_monitoring(keywords)
            
            # Keep the command running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING('\n⏹️  Stopping stream monitoring...')
                )
                realtime_stream_monitor.stop_stream_monitoring()
                self.stdout.write(
                    self.style.SUCCESS('✅ Stream monitoring stopped')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error starting stream monitoring: {e}')
            )
            logger.error(f"Stream monitoring error: {e}")
    
    def _get_keywords_to_monitor(self, options):
        """Get keywords to monitor based on options"""
        keywords = Keyword.objects.filter(is_active=True)
        
        # Filter by specific keywords
        if options['keywords']:
            keywords = keywords.filter(keyword__in=options['keywords'])
        
        # Filter by platform-specific filters
        if options['subreddit']:
            keywords = keywords.filter(platform_specific_filters__contains=options['subreddit'])
        
        # Filter by user ID
        if options['user_id']:
            keywords = keywords.filter(user_id=options['user_id'])
        
        return keywords 