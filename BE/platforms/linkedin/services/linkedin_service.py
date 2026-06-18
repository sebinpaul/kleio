import os
import time
import logging
import threading
import random
from typing import Dict, List, Optional

from django.utils import timezone

from core.models import Keyword, Mention, MonitorCursor
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service


logger = logging.getLogger(__name__)


class LinkedInService:
    """LinkedIn monitoring via Voyager API (authenticated HTTP, no browser).

    Uses the linkedin-api library for authentication and the Voyager
    ``search`` endpoint with ``resultType->CONTENT, sortBy->DATE_POSTED``
    to discover recent posts matching each keyword.

    Required env vars:
        KLEIO_LI_USER  – LinkedIn email
        KLEIO_LI_PASS  – LinkedIn password

    Optional env vars:
        KLEIO_LINKEDIN_LI_AT               – li_at cookie (skip credential login)
        KLEIO_LINKEDIN_CHECK_INTERVAL_SEC   – poll interval in seconds (default 300)
    """

    _CONTENT_FILTERS = "List(resultType->CONTENT,sortBy->DATE_POSTED)"
    _RESULTS_PER_SEARCH = 20
    _INTER_KEYWORD_DELAY = (3, 8)

    def __init__(self):
        self.is_monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = int(
            os.environ.get("KLEIO_LINKEDIN_CHECK_INTERVAL_SEC", "300")
        )
        self._li_user = os.environ.get("KLEIO_LI_USER", "").strip()
        self._li_pass = os.environ.get("KLEIO_LI_PASS", "").strip()
        self._li_at = os.environ.get("KLEIO_LINKEDIN_LI_AT", "").strip()
        self._api = None

    # ── Authentication ──────────────────────────────────────────────

    def _authenticate(self) -> bool:
        try:
            from linkedin_api import Linkedin
        except ImportError:
            logger.error("linkedin-api package is not installed (pip install linkedin-api)")
            return False

        # Cookie-based auth (preferred — avoids login challenge risk)
        if self._li_at:
            try:
                self._api = Linkedin("", "", authenticate=False)
                self._api.client._set_session_cookies({"li_at": self._li_at})
                logger.info("LinkedIn authenticated via li_at cookie")
                return True
            except Exception as e:
                logger.warning(f"LinkedIn cookie auth failed: {e}")
                self._api = None

        # Credential-based auth
        if self._li_user and self._li_pass:
            try:
                self._api = Linkedin(self._li_user, self._li_pass)
                logger.info("LinkedIn authenticated via credentials")
                return True
            except Exception as e:
                logger.error(f"LinkedIn credential auth failed: {e}")
                self._api = None
                return False

        logger.warning(
            "LinkedIn not configured — set KLEIO_LI_USER/KLEIO_LI_PASS or KLEIO_LINKEDIN_LI_AT"
        )
        return False

    # ── Lifecycle ───────────────────────────────────────────────────

    def start_stream_monitoring(self, keywords: List[Keyword]):
        if self.is_monitoring:
            logger.info("LinkedIn monitoring already running")
            return
        self.is_monitoring = True
        if not self._api and not self._authenticate():
            logger.warning("LinkedIn monitoring started without auth — will retry each cycle")
        self.monitor_thread = threading.Thread(
            target=self._run_loop, args=(keywords,), daemon=True
        )
        self.monitor_thread.start()
        logger.info("Started LinkedIn monitoring")

    def stop_stream_monitoring(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self._api = None
        logger.info("Stopped LinkedIn monitoring")

    # ── Main loop ───────────────────────────────────────────────────

    def _run_loop(self, keywords: List[Keyword]):
        while self.is_monitoring:
            try:
                if not self._api:
                    self._authenticate()
                if self._api:
                    self._tick(keywords)
                else:
                    logger.warning("LinkedIn auth unavailable — skipping cycle")
                time.sleep(self.check_interval + random.uniform(0, 30))
            except Exception as e:
                logger.error(f"LinkedIn monitor loop error: {e}")
                time.sleep(60)

    def _tick(self, keywords: List[Keyword]):
        for kw in keywords:
            if not self.is_monitoring:
                break
            if kw.platform not in [Platform.LINKEDIN.value, Platform.ALL.value]:
                continue
            try:
                self._search_keyword(kw)
            except Exception as e:
                logger.error(f"LinkedIn search error for '{kw.keyword}': {e}")
                if self._is_auth_error(e):
                    logger.warning("LinkedIn auth expired — will re-authenticate next cycle")
                    self._api = None
                    break
            time.sleep(random.uniform(*self._INTER_KEYWORD_DELAY))

    # ── Search & process ────────────────────────────────────────────

    def _search_keyword(self, kw: Keyword):
        query = (kw.keyword or "").strip()
        if not query:
            return

        results = self._api.search(
            {
                "keywords": query,
                "filters": self._CONTENT_FILTERS,
            },
            limit=self._RESULTS_PER_SEARCH,
        )
        if not results:
            return

        scope = f"search:{kw.id}"
        last_urn = self._get_cursor(kw.user_id, scope)
        new_top_urn: Optional[str] = None

        for entity in results:
            urn = entity.get("entityUrn") or entity.get("trackingUrn") or ""
            if not urn:
                continue
            if new_top_urn is None:
                new_top_urn = urn
            if urn == last_urn:
                break
            self._process_entity(kw, entity)

        if new_top_urn and new_top_urn != last_urn:
            self._set_cursor(kw.user_id, scope, new_top_urn)

    def _process_entity(self, kw: Keyword, entity: Dict):
        text = self._extract_text(entity, "summary") or self._extract_text(entity, "title")
        title = self._extract_text(entity, "title") or ""
        author = self._extract_text(entity, "primarySubtitle") or self._extract_text(entity, "subtitle") or ""
        url = entity.get("navigationUrl", "")
        urn = entity.get("entityUrn") or entity.get("trackingUrn") or ""

        if not text:
            return

        if not url and urn:
            url = self._urn_to_url(urn)
        if not url:
            return

        # Keyword matching
        matched = False
        if ContentType.TITLES.value in (kw.content_types or []):
            if self.matching_engine.match_keyword(kw, title or text, ContentType.TITLES.value):
                matched = True
        if not matched and ContentType.BODY.value in (kw.content_types or []):
            if self.matching_engine.match_keyword(kw, text, ContentType.BODY.value):
                matched = True
        if not matched:
            return

        # Dedupe
        try:
            if Mention.objects.filter(source_url=url, keyword_id=str(kw.id)).first():
                return
        except Exception:
            pass

        mention = Mention(
            keyword_id=str(kw.id),
            user_id=kw.user_id,
            content=text,
            title=title[:500] if title else text[:500],
            author=author[:100],
            source_url=url,
            platform=Platform.LINKEDIN.value,
            content_type=MentionContentType.POST.value,
            matched_text=kw.keyword,
            match_position=0,
            match_confidence=1.0,
            mention_date=timezone.now(),
            discovered_at=timezone.now(),
        )
        mention.platform_item_id = urn
        try:
            mention.save()
            email_notification_service.send_mention_notification(mention)
            logger.info(f"LinkedIn mention saved: {url}")
        except Exception as e:
            logger.error(f"Failed to save LinkedIn mention: {e}")

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(entity: Dict, field: str) -> str:
        value = entity.get(field)
        if isinstance(value, dict):
            return (value.get("text") or "").strip()
        if isinstance(value, str):
            return value.strip()
        return ""

    @staticmethod
    def _urn_to_url(urn: str) -> str:
        if "activity:" in urn:
            activity_id = urn.split("activity:")[-1]
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
        if "ugcPost:" in urn:
            post_id = urn.split("ugcPost:")[-1]
            return f"https://www.linkedin.com/feed/update/urn:li:ugcPost:{post_id}"
        return ""

    @staticmethod
    def _is_auth_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(tok in msg for tok in ("401", "unauthorized", "challenge", "login"))

    def _get_cursor(self, user_id: str, scope: str) -> Optional[str]:
        try:
            item = MonitorCursor.objects(
                user_id=user_id, platform=Platform.LINKEDIN.value, scope=scope
            ).first()
            return item.cursor if item else None
        except Exception:
            return None

    def _set_cursor(self, user_id: str, scope: str, cursor_val: str):
        try:
            item = MonitorCursor.objects(
                user_id=user_id, platform=Platform.LINKEDIN.value, scope=scope
            ).first()
            if not item:
                item = MonitorCursor(
                    user_id=user_id,
                    platform=Platform.LINKEDIN.value,
                    scope=scope,
                    cursor=cursor_val,
                )
            else:
                item.cursor = cursor_val
            item.save()
        except Exception:
            pass


linkedin_service = LinkedInService()
