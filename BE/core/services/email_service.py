import html
import os
import logging
import resend
from typing import Optional, List
from datetime import datetime, timezone as dt_timezone
from django.contrib.auth.models import User
from ..models import Mention, Keyword, UserProfile
from ..enums import Platform, MentionContentType
from .clerk_service import clerk_user_service

logger = logging.getLogger(__name__)

# Inline styles only: several mail clients drop <style> blocks entirely.
_PAGE_BG = "#f4f5f7"
_BORDER = "#e4e7ec"
_HEADING = "#101828"
_BODY = "#344054"
_MUTED = "#667085"
_ACCENT = "#4f46e5"
_FONT = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
)


class EmailNotificationService:
    """Service for sending email notifications for mentions across all platforms"""
    
    def __init__(self):
        # Assigned before the API-key guard: the rest of the class reads these
        # even when sending is disabled.
        self.app_name = "Kleio"
        self.from_email = os.environ.get("RESEND_FROM_EMAIL")
        self.app_url = (
            os.environ.get("APP_URL")
            or os.environ.get("FRONTEND_URL")
            or "https://kleio.fyi"
        ).rstrip("/")

        self.api_key = os.environ.get("RESEND_API_KEY")
        if not self.api_key:
            logger.warning("RESEND_API_KEY not found in environment variables")
            return

        resend.api_key = self.api_key

    def _from_address(self) -> str:
        """Without a display name, clients show the bare mailbox ("alerts")."""
        sender = (self.from_email or "").strip()
        if not sender:
            return f"{self.app_name} Alerts <alerts@kleio.fyi>"
        if "<" in sender:
            return sender
        return f"{self.app_name} Alerts <{sender}>"

    @staticmethod
    def _esc(value: Optional[str]) -> str:
        """Mention content is untrusted and is interpolated straight into HTML."""
        return html.escape(value or "", quote=True)

    @staticmethod
    def _truncate(value: Optional[str], limit: int) -> str:
        text = (value or "").strip()
        return text if len(text) <= limit else f"{text[:limit].rstrip()}…"

    @staticmethod
    def _format_timestamp(value: Optional[datetime]) -> str:
        """Always label the zone: timestamps are stored in UTC, readers are not."""
        if not value:
            return "Unknown date"
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_timezone.utc)
        return value.astimezone(dt_timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    
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

            if not getattr(keyword, 'email_notifications', True):
                logger.info(f"Email notifications disabled for keyword {keyword.id}")
                return True
            
            # Prepare email content
            params = {
                "from": self._from_address(),
                "to": [user_email],
                "subject": self._generate_subject(mention, keyword),
                "html": self._generate_html_content(mention, keyword),
                "text": self._plain_text(mention, keyword),
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
            params = {
                "from": self._from_address(),
                "to": [user_email],
                "subject": self._digest_subject(mentions_by_keyword),
                "html": self._generate_digest_html_content(mentions_by_keyword),
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
        return f"New {keyword.keyword} mention on {platform_name}"

    def _layout(self, preheader: str, inner_html: str) -> str:
        """Wrap content in the shared shell. Tables, for Outlook's sake."""
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:{_PAGE_BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{self._esc(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{_PAGE_BG};padding:32px 16px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;">
<tr><td style="padding:0 4px 16px;font-family:{_FONT};font-size:14px;font-weight:600;color:{_MUTED};letter-spacing:.02em;">
{self.app_name}
</td></tr>
<tr><td style="background:#ffffff;border:1px solid {_BORDER};border-radius:12px;padding:28px;">
{inner_html}
</td></tr>
<tr><td style="padding:20px 4px 0;font-family:{_FONT};font-size:12px;line-height:1.6;color:{_MUTED};">
<a href="{self.app_url}/dashboard" style="color:{_MUTED};">Manage keywords</a>
&nbsp;·&nbsp;
<a href="{self.app_url}/dashboard/settings" style="color:{_MUTED};">Notification settings</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

    def _mention_card(self, mention: Mention, keyword: Keyword) -> str:
        """One mention, rendered as a quoted block with its metadata."""
        platform_name = self._get_platform_display_name(mention.platform)
        content_type = self._get_content_type_display_name(mention.content_type)
        author = self._esc(mention.author) or "unknown"
        when = self._format_timestamp(mention.mention_date)
        body = self._esc(self._truncate(mention.content, 400)) or "<em>No text content</em>"
        title = self._esc(self._truncate(mention.title, 120))

        # Twitter titles are synthesised as "Tweet by @handle", which just repeats
        # the byline above; only show a title that carries its own information.
        title_row = ""
        if title and (mention.author or "").lower() not in title.lower():
            title_row = (
                f'<div style="font-family:{_FONT};font-size:14px;font-weight:600;'
                f'color:{_HEADING};padding-bottom:6px;">{title}</div>'
            )

        return f"""
<div style="border:1px solid {_BORDER};border-radius:10px;padding:18px;">
  <div style="font-family:{_FONT};font-size:13px;color:{_MUTED};padding-bottom:12px;">
    <strong style="color:{_BODY};">{author}</strong>
    &nbsp;·&nbsp;{platform_name}
    &nbsp;·&nbsp;{content_type}
  </div>
  {title_row}
  <div style="font-family:{_FONT};font-size:15px;line-height:1.6;color:{_BODY};
              border-left:3px solid {_BORDER};padding:2px 0 2px 14px;">
    {body}
  </div>
  <div style="font-family:{_FONT};font-size:12px;color:{_MUTED};padding-top:14px;">
    {when}
  </div>
</div>"""

    def _plain_text(self, mention: Mention, keyword: Keyword) -> str:
        """Plain-text alternative — meaningfully improves deliverability."""
        platform_name = self._get_platform_display_name(mention.platform)
        return "\n".join([
            f'New mention of "{keyword.keyword}" on {platform_name}',
            "",
            f"Author:  {mention.author or 'unknown'}",
            f"When:    {self._format_timestamp(mention.mention_date)}",
            f"Type:    {self._get_content_type_display_name(mention.content_type)}",
            "",
            self._truncate(mention.content, 400),
            "",
            f"View original: {mention.source_url}",
            f"Manage keywords: {self.app_url}/dashboard",
        ])
    
    def _generate_html_content(self, mention: Mention, keyword: Keyword) -> str:
        """Generate HTML email content for a single mention"""
        platform_name = self._get_platform_display_name(mention.platform)
        keyword_text = self._esc(keyword.keyword)

        inner = f"""
<div style="font-family:{_FONT};font-size:19px;font-weight:600;color:{_HEADING};padding-bottom:4px;">
  New mention on {platform_name}
</div>
<div style="font-family:{_FONT};font-size:14px;color:{_MUTED};padding-bottom:20px;">
  Matched your keyword <strong style="color:{_BODY};">{keyword_text}</strong>
</div>
{self._mention_card(mention, keyword)}
<div style="padding-top:22px;">
  <a href="{self._esc(mention.source_url)}" target="_blank"
     style="display:inline-block;background:{_ACCENT};color:#ffffff;font-family:{_FONT};
            font-size:14px;font-weight:600;text-decoration:none;padding:11px 22px;border-radius:8px;">
    View on {platform_name}
  </a>
</div>"""

        preheader = f"{mention.author or 'Someone'} mentioned {keyword.keyword} on {platform_name}"
        return self._layout(preheader, inner)
    
    def _digest_subject(self, mentions_by_keyword: dict) -> str:
        total = sum(len(m) for m in mentions_by_keyword.values())
        noun = "mention" if total == 1 else "mentions"
        if len(mentions_by_keyword) == 1:
            keyword = Keyword.objects(id=next(iter(mentions_by_keyword))).first()
            if keyword:
                return f"{total} new {keyword.keyword} {noun}"
        return f"{total} new {noun} across {len(mentions_by_keyword)} keywords"

    def _generate_digest_html_content(self, mentions_by_keyword: dict) -> str:
        """Generate HTML email content for digest with multiple mentions"""
        total_mentions = sum(len(mentions) for mentions in mentions_by_keyword.values())
        noun = "mention" if total_mentions == 1 else "mentions"

        sections: List[str] = []
        for keyword_id, mentions in mentions_by_keyword.items():
            keyword = Keyword.objects(id=keyword_id).first()
            if not keyword:
                continue

            cards = "".join(
                f"""
<div style="padding-top:12px;">
  {self._mention_card(mention, keyword)}
  <div style="padding-top:8px;">
    <a href="{self._esc(mention.source_url)}" target="_blank"
       style="font-family:{_FONT};font-size:13px;font-weight:600;color:{_ACCENT};text-decoration:none;">
      View original →
    </a>
  </div>
</div>"""
                for mention in mentions
            )

            sections.append(f"""
<div style="padding-top:26px;">
  <div style="font-family:{_FONT};font-size:15px;font-weight:600;color:{_HEADING};">
    {self._esc(keyword.keyword)}
  </div>
  <div style="font-family:{_FONT};font-size:13px;color:{_MUTED};">
    {len(mentions)} {'mention' if len(mentions) == 1 else 'mentions'}
  </div>
  {cards}
</div>""")

        inner = f"""
<div style="font-family:{_FONT};font-size:19px;font-weight:600;color:{_HEADING};padding-bottom:4px;">
  {total_mentions} new {noun}
</div>
<div style="font-family:{_FONT};font-size:14px;color:{_MUTED};">
  Across {len(mentions_by_keyword)} of your keywords
</div>
{''.join(sections)}
<div style="padding-top:26px;">
  <a href="{self.app_url}/dashboard" target="_blank"
     style="display:inline-block;background:{_ACCENT};color:#ffffff;font-family:{_FONT};
            font-size:14px;font-weight:600;text-decoration:none;padding:11px 22px;border-radius:8px;">
    View all mentions
  </a>
</div>"""

        return self._layout(f"{total_mentions} new {noun} across your keywords", inner)
    
    def _get_platform_display_name(self, platform: str) -> str:
        """Get display name for platform"""
        platform_names = {
            Platform.REDDIT.value: "Reddit",
            Platform.HACKERNEWS.value: "Hacker News",
            Platform.TWITTER.value: "Twitter",
            Platform.YOUTUBE.value: "YouTube",
            Platform.ALL.value: "Multiple Platforms"
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
