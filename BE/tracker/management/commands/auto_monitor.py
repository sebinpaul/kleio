from django.core.management.base import BaseCommand
from tracker.services.auto_monitor_service import auto_monitor_service
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Control automatic monitoring service for all active keywords'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status'],
            help='Action to perform: start, stop, or status'
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Watch the service status continuously'
        )

    def handle(self, *args, **options):
        action = options['action']
        watch = options['watch']
        
        if action == 'start':
            self._start_monitoring()
        elif action == 'stop':
            self._stop_monitoring()
        elif action == 'status':
            self._show_status(watch)
    
    def _start_monitoring(self):
        """Start automatic monitoring"""
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting automatic monitoring service...')
        )
        
        try:
            auto_monitor_service.start_auto_monitoring()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Automatic monitoring service started successfully!')
            )
            self.stdout.write(
                self.style.WARNING('   The service will automatically monitor all active keywords')
            )
            self.stdout.write(
                self.style.WARNING('   New keywords will be automatically picked up')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to start monitoring: {e}')
            )
    
    def _stop_monitoring(self):
        """Stop automatic monitoring"""
        self.stdout.write(
            self.style.WARNING('⏹️  Stopping automatic monitoring service...')
        )
        
        try:
            auto_monitor_service.stop_auto_monitoring()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Automatic monitoring service stopped')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to stop monitoring: {e}')
            )
    
    def _show_status(self, watch=False):
        """Show monitoring status"""
        try:
            status = auto_monitor_service.get_status()
            
            self.stdout.write(
                self.style.SUCCESS('📊 Automatic Monitoring Service Status')
            )
            self.stdout.write('=' * 50)
            
            # Service status
            if status['is_running']:
                self.stdout.write(
                    self.style.SUCCESS(f"🟢 Service Status: RUNNING")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"🔴 Service Status: STOPPED")
                )
            
            # Monitoring details
            self.stdout.write(f"📌 Monitored Keywords: {status['monitored_keywords_count']}")
            self.stdout.write(f"⏱️  Check Interval: {status['check_interval_seconds']} seconds")
            
            if status['last_check']:
                self.stdout.write(f"🕒 Last Check: {status['last_check']}")
            
            # Stream monitoring status
            if status['stream_monitoring_active']:
                self.stdout.write(
                    self.style.SUCCESS(f"🟢 Stream Monitoring: ACTIVE")
                )
                self.stdout.write(f"📡 Active Streams: {', '.join(status['active_streams'])}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"🟡 Stream Monitoring: INACTIVE")
                )
            
            # Watch mode
            if watch and status['is_running']:
                self.stdout.write('\n👀 Watching for changes (Press Ctrl+C to stop)...')
                try:
                    while True:
                        time.sleep(5)
                        new_status = auto_monitor_service.get_status()
                        
                        # Clear previous lines
                        self.stdout.write('\033[F' * 10)
                        
                        # Show updated status
                        self.stdout.write(
                            self.style.SUCCESS('📊 Automatic Monitoring Service Status (Live)')
                        )
                        self.stdout.write('=' * 50)
                        self.stdout.write(f"🟢 Service Status: RUNNING")
                        self.stdout.write(f"📌 Monitored Keywords: {new_status['monitored_keywords_count']}")
                        self.stdout.write(f"🕒 Last Check: {new_status['last_check']}")
                        
                        if new_status['stream_monitoring_active']:
                            self.stdout.write(f"🟢 Stream Monitoring: ACTIVE")
                            self.stdout.write(f"📡 Active Streams: {', '.join(new_status['active_streams'])}")
                        else:
                            self.stdout.write(f"🟡 Stream Monitoring: INACTIVE")
                        
                        self.stdout.write('\n👀 Watching for changes (Press Ctrl+C to stop)...')
                        
                except KeyboardInterrupt:
                    self.stdout.write('\n👋 Stopped watching')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting status: {e}')
            ) 