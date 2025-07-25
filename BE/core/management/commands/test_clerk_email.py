from django.core.management.base import BaseCommand
from core.services.clerk_service import clerk_user_service
from core.services.email_service import email_notification_service
from core.models import Mention, Keyword
from core.enums import Platform, MentionContentType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Clerk email integration with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clerk-user-id',
            type=str,
            help='Clerk User ID to test with',
            required=True
        )
        parser.add_argument(
            '--keyword',
            type=str,
            default='test',
            help='Test keyword to use'
        )

    def handle(self, *args, **options):
        clerk_user_id = options['clerk_user_id']
        test_keyword = options['keyword']

        self.stdout.write(f"Testing Clerk email integration for user ID: {clerk_user_id}")
        self.stdout.write(f"Using keyword: {test_keyword}")

        # Test Clerk service directly
        self.stdout.write("\n1️⃣ Testing Clerk service...")
        email = clerk_user_service.get_user_email(clerk_user_id)
        if email:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Found email via Clerk API: {email}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ No email found via Clerk API for user: {clerk_user_id}")
            )
            return

        # Test user info
        self.stdout.write("\n2️⃣ Testing user info...")
        user_info = clerk_user_service.get_user_info(clerk_user_id)
        if user_info:
            self.stdout.write(
                self.style.SUCCESS(f"✅ User info retrieved successfully")
            )
            self.stdout.write(f"   User ID: {user_info.get('id')}")
            self.stdout.write(f"   First Name: {user_info.get('first_name', 'N/A')}")
            self.stdout.write(f"   Last Name: {user_info.get('last_name', 'N/A')}")
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to get user info")
            )

        # Test email service integration
        self.stdout.write("\n3️⃣ Testing email service integration...")
        email_from_service = email_notification_service.get_user_email(clerk_user_id)
        if email_from_service:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Email service found email: {email_from_service}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Email service failed to find email")
            )
            return

        # Test email notification
        self.stdout.write("\n4️⃣ Testing email notification...")
        try:
            # Create a test keyword
            keyword = Keyword(
                keyword=test_keyword,
                platform=Platform.REDDIT.value,
                user_id=clerk_user_id,
                is_active=True
            )

            # Create a test mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=clerk_user_id,
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

            # Send test email
            success = email_notification_service.send_mention_notification(mention)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Test email sent successfully!")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Failed to send test email")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error during email test: {str(e)}")
            )

        self.stdout.write("\n🎉 Clerk email integration test completed!") 