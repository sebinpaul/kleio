from django.core.management.base import BaseCommand
from core.services.email_service import email_notification_service
from core.models import Mention, Keyword
from core.enums import Platform, MentionContentType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email notifications with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Django User ID to send test notification to',
            required=True
        )
        parser.add_argument(
            '--keyword',
            type=str,
            default='test',
            help='Test keyword to use'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        test_keyword = options['keyword']

        self.stdout.write(f"Testing email notifications for user ID: {user_id}")
        self.stdout.write(f"Using keyword: {test_keyword}")

        # Get user email
        user_email = email_notification_service.get_user_email(user_id)
        if not user_email:
            self.stdout.write(
                self.style.ERROR(f"❌ No email found for user ID: {user_id}")
            )
            return

        self.stdout.write(f"User email: {user_email}")

        # Create a test keyword
        keyword = Keyword(
            keyword=test_keyword,
            platform=Platform.REDDIT.value,
            user_id=user_id,
            active=True
        )

        # Create a test mention
        mention = Mention(
            keyword_id=str(keyword.id),
            user_id=user_id,
            content="This is a test mention content that contains the keyword for testing purposes.",
            title="Test Post Title",
            author="test_user",
            source_url="https://reddit.com/r/test/comments/test123",
            platform=Platform.REDDIT.value,
            subreddit="test",
            content_type=MentionContentType.POST.value,
            matched_text=test_keyword,
            match_position=0,
            match_confidence=1.0,
            mention_date=datetime.now()
        )

        # Test single mention notification
        self.stdout.write("Sending single mention notification...")
        success = email_notification_service.send_mention_notification(mention)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("✅ Single mention email sent successfully!")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ Failed to send single mention email")
            )

        # Test digest notification
        self.stdout.write("Sending digest notification...")
        mentions = [mention]  # Create multiple mentions for digest
        success = email_notification_service.send_digest_notification(
            user_id, mentions=mentions
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("✅ Digest email sent successfully!")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ Failed to send digest email")
            )

        self.stdout.write("Email notification test completed!") 