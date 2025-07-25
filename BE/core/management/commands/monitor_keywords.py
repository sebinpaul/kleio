from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from core.models import Keyword, Mention
from core.services.reddit_service import RedditService
from core.services.hackernews_service import HackerNewsService
from core.enums import Platform

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor all active keywords and send notifications for new mentions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving mentions or sending notifications',
        )
        parser.add_argument(
            '--platform',
            type=str,
            choices=[Platform.REDDIT.value, Platform.HACKERNEWS.value, 'both'],
            default='both',
            help='Platform to monitor (default: both)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        platform = options['platform']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting keyword monitoring for platform: {platform}')
        )
        
        try:
            # Get all active keywords
            if platform == 'both':
                keywords = Keyword.objects.filter(is_active=True)
            else:
                keywords = Keyword.objects.filter(is_active=True, platform__in=[platform, Platform.ALL.value])
            
            if not keywords:
                self.stdout.write(
                    self.style.WARNING('No active keywords found to monitor')
                )
                return
            
            self.stdout.write(f'Found {keywords.count()} active keywords to monitor')
            
            all_mentions = []
            
            # Monitor Reddit keywords
            if platform in [Platform.REDDIT.value, 'both']:
                reddit_keywords = [k for k in keywords if k.platform in [Platform.REDDIT.value, Platform.ALL.value]]
                if reddit_keywords:
                    self.stdout.write(f'Monitoring {len(reddit_keywords)} Reddit keywords...')
                    reddit_service = RedditService()
                    reddit_mentions = reddit_service.monitor_keywords(reddit_keywords)
                    all_mentions.extend(reddit_mentions)
                    self.stdout.write(f'Found {len(reddit_mentions)} Reddit mentions')
            
            # Monitor HackerNews keywords
            if platform in [Platform.HACKERNEWS.value, 'both']:
                hn_keywords = [k for k in keywords if k.platform in [Platform.HACKERNEWS.value, Platform.ALL.value]]
                if hn_keywords:
                    self.stdout.write(f'Monitoring {len(hn_keywords)} HackerNews keywords...')
                    hn_service = HackerNewsService()
                    hn_mentions = hn_service.monitor_keywords(hn_keywords)
                    all_mentions.extend(hn_mentions)
                    self.stdout.write(f'Found {len(hn_mentions)} HackerNews mentions')
            
            if not all_mentions:
                self.stdout.write(
                    self.style.WARNING('No new mentions found')
                )
                return
            
            self.stdout.write(f'Total new mentions found: {len(all_mentions)}')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN: Would save mentions and send notifications')
                )
                for mention in all_mentions:
                    self.stdout.write(
                        f'  - {mention.keyword_id} on {mention.platform}: {mention.title or mention.content[:50]}...'
                    )
                return
            
            # Save mentions to database
            saved_mentions = []
            for mention in all_mentions:
                try:
                    mention.save()
                    saved_mentions.append(mention)
                    self.stdout.write(
                        f'  Saved mention: {mention.keyword_id} on {mention.platform}'
                    )
                except Exception as e:
                    logger.error(f"Error saving mention: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(f'  Error saving mention: {str(e)}')
                    )
            
            # Send email notifications
            from core.services.email_service import email_notification_service
            notifications_sent = 0
            
            for mention in saved_mentions:
                try:
                    success = email_notification_service.send_mention_notification(mention)
                    
                    if success:
                        notifications_sent += 1
                        self.stdout.write(
                            f'  Sent email notification for mention: {mention.keyword_id}'
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  Failed to send email notification for mention: {mention.keyword_id}')
                        )
                        
                except Exception as e:
                    logger.error(f"Error sending email notification for mention {mention.id}: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(f'  Error sending email notification: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Monitoring completed: {len(saved_mentions)} mentions saved, '
                    f'{notifications_sent} notifications sent'
                )
            )
            
        except Exception as e:
            logger.error(f"Error in keyword monitoring: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error in keyword monitoring: {str(e)}')
            ) 