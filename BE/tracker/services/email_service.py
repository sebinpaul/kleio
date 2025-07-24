import os
import logging
import resend
from typing import Optional, List
from datetime import datetime
from django.contrib.auth.models import User
from ..models import Mention, Keyword, UserProfile
from ..enums import Platform, MentionContentType
from .clerk_service import clerk_user_service

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service for sending email notifications for mentions across all platforms"""
    
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY")
        if not self.api_key:
            logger.warning("RESEND_API_KEY not found in environment variables")
            return
        
        resend.api_key = self.api_key
        self.from_email = os.environ.get("RESEND_FROM_EMAIL")
        self.app_name = "Kleio"
        self.app_url = os.environ.get("APP_URL", "https://kleio.app")
    
    def get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email from Clerk API with fallback to Django User model"""
        try:
            # Try Clerk API first (for Clerk user IDs)
            email = clerk_user_service.get_user_email(user_id)
            if email:
                logger.info(f"Found email via Clerk API for user {user_id}: {email}")
                return email
            
            # Fallback to Django User model (for numeric IDs)
            try:
                user = User.objects.get(id=user_id)
                email = user.email
                if email:
                    logger.info(f"Found email via Django User model for user {user_id}: {email}")
                    return email
            except User.DoesNotExist:
                logger.warning(f"User not found in Django User model with ID: {user_id}")
            
            logger.error(f"No email found for user {user_id} via Clerk API or Django User model")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user email for ID {user_id}: {e}")
            return None
    
    def should_send_notification(self, user_id: str) -> bool:
        """Check if user has email notifications enabled"""
        try:
            # Check user profile settings
            profile = UserProfile.objects(user_id=user_id).first()
            if profile:
                return profile.email_notifications
            # Default to True if no profile exists
            return True
        except Exception as e:
            logger.error(f"Error checking notification settings for user {user_id}: {e}")
            return True  # Default to True on error
    
    def send_mention_notification(self, mention: Mention, user_email: str = None) -> bool:
        """Send email notification for a new mention"""
        try:
            if not self.api_key:
                logger.error("Cannot send email: RESEND_API_KEY not configured")
                return False
            
            # Get user email if not provided
            if not user_email:
                user_email = self.get_user_email(mention.user_id)
                if not user_email:
                    logger.error(f"No email found for user {mention.user_id}")
                    return False
            
            # Check if user has notifications enabled
            if not self.should_send_notification(mention.user_id):
                logger.info(f"Email notifications disabled for user {mention.user_id}")
                return True  # Return True as this is not an error
            
            # Get keyword details
            keyword = Keyword.objects(id=mention.keyword_id).first()
            if not keyword:
                logger.error(f"Keyword not found for mention: {mention.id}")
                return False
            
            # Prepare email content
            subject = self._generate_subject(mention, keyword)
            html_content = self._generate_html_content(mention, keyword)
            print("from : ", self.from_email)
            # Send email
            params = {
                "from": self.from_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }
            
            email_response = resend.Emails.send(params)
            logger.info(f"Email notification sent successfully: {email_response.get('id')}")
            
            # Mark mention as email sent
            mention.email_sent = True
            mention.email_sent_at = datetime.now()
            mention.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def send_digest_notification(self, user_id: str, user_email: str = None, mentions: List[Mention] = None) -> bool:
        """Send digest email with multiple mentions"""
        try:
            if not self.api_key:
                logger.error("Cannot send email: RESEND_API_KEY not configured")
                return False
            
            # Get user email if not provided
            if not user_email:
                user_email = self.get_user_email(user_id)
                if not user_email:
                    logger.error(f"No email found for user {user_id}")
                    return False
            
            # Check if user has notifications enabled
            if not self.should_send_notification(user_id):
                logger.info(f"Email notifications disabled for user {user_id}")
                return True  # Return True as this is not an error
            
            if not mentions:
                logger.info("No mentions to send in digest")
                return True
            
            # Group mentions by keyword
            mentions_by_keyword = {}
            for mention in mentions:
                keyword_id = mention.keyword_id
                if keyword_id not in mentions_by_keyword:
                    mentions_by_keyword[keyword_id] = []
                mentions_by_keyword[keyword_id].append(mention)
            
            # Prepare email content
            subject = f"📧 {self.app_name} - {len(mentions)} new mentions found"
            html_content = self._generate_digest_html_content(mentions_by_keyword)
            
            # Send email
            params = {
                "from": self.from_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }
            
            email_response = resend.Emails.send(params)
            logger.info(f"Digest email sent successfully: {email_response.get('id')}")
            
            # Mark all mentions as email sent
            for mention in mentions:
                mention.email_sent = True
                mention.email_sent_at = datetime.now()
                mention.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending digest email: {str(e)}")
            return False
    
    def _generate_subject(self, mention: Mention, keyword: Keyword) -> str:
        """Generate email subject line"""
        platform_name = self._get_platform_display_name(mention.platform)
        content_type = self._get_content_type_display_name(mention.content_type)
        
        return f"🎯 New mention of '{keyword.keyword}' on {platform_name} ({content_type})"
    
    def _generate_html_content(self, mention: Mention, keyword: Keyword) -> str:
        """Generate HTML email content for a single mention"""
        platform_name = self._get_platform_display_name(mention.platform)
        content_type = self._get_content_type_display_name(mention.content_type)
        mention_date = mention.mention_date.strftime("%B %d, %Y at %I:%M %p")
        
        # Truncate content for email
        content_preview = mention.content[:200] + "..." if len(mention.content) > 200 else mention.content
        title_preview = mention.title[:100] + "..." if len(mention.title) > 100 else mention.title
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Mention Found</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .keyword {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2196f3; }}
                .mention-card {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .platform-badge {{ display: inline-block; background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                .content-type-badge {{ display: inline-block; background: #4ecdc4; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-left: 8px; }}
                .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .meta {{ color: #666; font-size: 14px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 New Mention Found!</h1>
                    <p>Your keyword was mentioned on {platform_name}</p>
                </div>
                
                <div class="content">
                    <div class="keyword">
                        <strong>Keyword:</strong> {keyword.keyword}
                    </div>
                    
                    <div class="mention-card">
                        <div class="meta">
                            <span class="platform-badge">{platform_name}</span>
                            <span class="content-type-badge">{content_type}</span>
                            <br>
                            <strong>Author:</strong> {mention.author}
                            <br>
                            <strong>Date:</strong> {mention_date}
                        </div>
                        
                        <h3>{title_preview}</h3>
                        <p>{content_preview}</p>
                        
                        <a href="{mention.source_url}" class="btn" target="_blank">View Original</a>
                    </div>
                    
                    <div class="footer">
                        <p>You're receiving this because you're monitoring "{keyword.keyword}" on {platform_name}.</p>
                        <p><a href="{self.app_url}/dashboard">Manage your keywords</a> | <a href="{self.app_url}/settings">Email preferences</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_digest_html_content(self, mentions_by_keyword: dict) -> str:
        """Generate HTML email content for digest with multiple mentions"""
        total_mentions = sum(len(mentions) for mentions in mentions_by_keyword.values())
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Mention Digest</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .keyword-section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .mention-item {{ border-left: 3px solid #667eea; padding: 15px; margin: 10px 0; background: #f8f9fa; }}
                .platform-badge {{ display: inline-block; background: #ff6b6b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Mention Digest</h1>
                    <p>{total_mentions} new mentions found across your keywords</p>
                </div>
                
                <div class="content">
        """
        
        for keyword_id, mentions in mentions_by_keyword.items():
            keyword = Keyword.objects(id=keyword_id).first()
            if not keyword:
                continue
            
            html += f"""
                    <div class="keyword-section">
                        <h3>Keyword: {keyword.keyword}</h3>
                        <p>{len(mentions)} mention(s) found</p>
            """
            
            for mention in mentions:
                platform_name = self._get_platform_display_name(mention.platform)
                content_type = self._get_content_type_display_name(mention.content_type)
                mention_date = mention.mention_date.strftime("%B %d, %Y at %I:%M %p")
                content_preview = mention.content[:150] + "..." if len(mention.content) > 150 else mention.content
                
                html += f"""
                        <div class="mention-item">
                            <div>
                                <span class="platform-badge">{platform_name}</span>
                                <strong>{mention.author}</strong> • {mention_date}
                            </div>
                            <p><strong>{content_type}:</strong> {content_preview}</p>
                            <a href="{mention.source_url}" target="_blank">View Original</a>
                        </div>
                """
            
            html += """
                    </div>
            """
        
        html += f"""
                    <div class="footer">
                        <a href="{self.app_url}/dashboard" class="btn">View All Mentions</a>
                        <p><a href="{self.app_url}/settings">Manage email preferences</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_platform_display_name(self, platform: str) -> str:
        """Get display name for platform"""
        platform_names = {
            Platform.REDDIT.value: "Reddit",
            Platform.HACKERNEWS.value: "Hacker News",
            Platform.TWITTER.value: "Twitter",
            Platform.LINKEDIN.value: "LinkedIn",
            Platform.ALL.value: "Multiple Platforms"  # Changed from Platform.BOTH.value
        }
        return platform_names.get(platform, platform.title())
    
    def _get_content_type_display_name(self, content_type: str) -> str:
        """Get display name for content type"""
        content_type_names = {
            MentionContentType.POST.value: "Post",
            MentionContentType.COMMENT.value: "Comment",
            MentionContentType.TITLE.value: "Title",
            MentionContentType.BODY.value: "Body"
        }
        return content_type_names.get(content_type, content_type.title())

# Global instance
email_notification_service = EmailNotificationService()
