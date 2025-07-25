from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Keyword
from core.enums import Platform, ContentType
from platforms.reddit.services.realtime_monitor import realtime_stream_monitor
from core.services.matching_engine import GenericMatchingEngine
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Reddit comment monitoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keyword',
            type=str,
            help='Keyword to test with',
            default='test'
        )
        parser.add_argument(
            '--duration',
            type=int,
            help='Duration to monitor in seconds',
            default=60
        )
        parser.add_argument(
            '--create-test-keyword',
            action='store_true',
            help='Create a test keyword for monitoring'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Reddit Comment Monitoring ==='))
        
        keyword_text = options['keyword']
        duration = options['duration']
        create_test = options['create_test_keyword']
        
        # Test 1: Check existing keywords
        self.stdout.write('\n1. Checking existing keywords...')
        keywords = Keyword.objects.filter(is_active=True)
        self.stdout.write(f'Found {len(keywords)} active keywords')
        
        for keyword in keywords:
            self.stdout.write(f'  - {keyword.keyword} (Platform: {keyword.platform}, Content Types: {keyword.content_types})')
        
        # Test 2: Create test keyword if requested
        if create_test:
            self.stdout.write(f'\n2. Creating test keyword: {keyword_text}')
            try:
                test_keyword = Keyword(
                    user_id="test_user",
                    keyword=keyword_text,
                    platform=Platform.REDDIT.value,
                    content_types=[ContentType.COMMENTS.value, ContentType.TITLES.value],
                    is_active=True
                )
                test_keyword.save()
                self.stdout.write(self.style.SUCCESS(f'Created test keyword: {test_keyword.keyword}'))
                keywords = Keyword.objects.filter(is_active=True)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating test keyword: {e}'))
        
        # Test 3: Test matching engine
        self.stdout.write('\n3. Testing matching engine...')
        matching_engine = GenericMatchingEngine()
        
        test_content = f"I love {keyword_text} programming language"
        test_keyword = Keyword(
            user_id="test_user",
            keyword=keyword_text,
            platform=Platform.REDDIT.value,
            content_types=[ContentType.COMMENTS.value],
            is_active=True
        )
        
        match_result = matching_engine.match_keyword(test_keyword, test_content, ContentType.COMMENTS.value)
        should_monitor = matching_engine.should_monitor_content(test_keyword, ContentType.COMMENTS.value)
        
        self.stdout.write(f'Test content: {test_content}')
        self.stdout.write(f'Keyword: {test_keyword.keyword}')
        self.stdout.write(f'Should monitor comments: {should_monitor}')
        self.stdout.write(f'Match result: {match_result}')
        
        if match_result:
            self.stdout.write(self.style.SUCCESS('✅ Match found!'))
        else:
            self.stdout.write(self.style.WARNING('❌ No match found'))
        
        # Test 4: Start monitoring if there are keywords
        if keywords:
            self.stdout.write(f'\n4. Starting Reddit stream monitoring for {duration} seconds...')
            self.stdout.write('Press Ctrl+C to stop early')
            
            try:
                realtime_stream_monitor.start_stream_monitoring(keywords)
                
                import time
                time.sleep(duration)
                
                self.stdout.write('Stopping Reddit stream monitoring...')
                realtime_stream_monitor.stop_stream_monitoring()
                
            except KeyboardInterrupt:
                self.stdout.write('\nStopping monitoring (interrupted by user)...')
                realtime_stream_monitor.stop_stream_monitoring()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error during monitoring: {e}'))
        else:
            self.stdout.write(self.style.WARNING('No active keywords found. Use --create-test-keyword to create one.'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Testing Complete ===')) 