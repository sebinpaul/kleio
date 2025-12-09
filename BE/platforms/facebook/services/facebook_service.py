import os
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

from django.utils import timezone

from core.models import Keyword, Mention, PlatformSource
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service
from core.services.proxy_service import ProxyManager


logger = logging.getLogger(__name__)


class FacebookService:
    """Monitor public Facebook Pages via Graph API (app token).

    Notes:
    - Requires env KLEIO_FACEBOOK_APP_TOKEN (App Access Token).
    - We cannot do global text search; users must specify Page IDs/URLs in
      Keyword.platform_specific_filters (e.g., "page:cnn", "https://www.facebook.com/cnn").
    - Falls back to skipping when token missing or no pages are configured.
    """

    def __init__(self):
        self.is_monitoring: bool = False
        self.monitor_thread = None
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = 300
        self.graph_base = "https://graph.facebook.com/v19.0"
        self.app_token = os.environ.get("KLEIO_FACEBOOK_APP_TOKEN", "").strip()
        self.proxy_manager = ProxyManager()
        # Dedup and cursors
        self.seen_cache: Dict[str, float] = {}
        # Track last created_time ISO string per page-id
        self.page_last_seen: Dict[str, str] = {}

    def start_stream_monitoring(self, keywords: List[Keyword]):
        if self.is_monitoring:
            logger.info("Facebook monitoring already running")
            return
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._run_loop, args=(keywords,), daemon=True)
        self.monitor_thread.start()
        logger.info("Started Facebook monitoring")

    def stop_stream_monitoring(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped Facebook monitoring")

    def _run_loop(self, keywords: List[Keyword]):
        while self.is_monitoring:
            try:
                self._tick(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Facebook monitor loop error: {e}")
                time.sleep(60)

    def _resolve_page_id(self, sess, value: str) -> Optional[str]:
        """Accepts raw filter value like 'page:cnn' or URL; returns numeric Page ID or None."""
        v = (value or '').strip()
        if not v:
            return None
        if v.startswith('page:'):
            slug = v.split(':', 1)[1]
            # Attempt direct use; Graph will resolve if valid
            return slug
        if v.startswith('http'):
            try:
                r = sess.get(f"{self.graph_base}", params={"id": v, "access_token": self.app_token}, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    return data.get('id')
            except Exception:
                return None
        # Otherwise treat as slug
        return v

    def _tick(self, keywords: List[Keyword]):
        # Reload proxies (UI-driven) each tick
        try:
            self.proxy_manager.reload()
        except Exception:
            pass
        sess = self.proxy_manager.for_requests()
        # Allow per-user override via settings config (first keyword owner wins)
        if not self.app_token:
            for kw in keywords:
                try:
                    src = PlatformSource.objects(user_id=kw.user_id, platform=Platform.FACEBOOK.value).first()
                    if src and src.config and isinstance(src.config.get('app_token'), str):
                        self.app_token = str(src.config.get('app_token')).strip()
                        break
                except Exception:
                    pass
        if not self.app_token:
            # Public scraping fallback using mobile pages
            self._tick_public_scrape(sess, keywords)
            return
        # Graph API path
        for kw in keywords:
            if kw.platform not in [Platform.FACEBOOK.value, Platform.ALL.value]:
                continue
            # Prefer settings-backed sources
            pages = kw.platform_specific_filters or []
            try:
                src = PlatformSource.objects(user_id=kw.user_id, platform=Platform.FACEBOOK.value).first()
                if src and src.sources:
                    pages = src.sources
            except Exception:
                pass
            if not pages:
                continue
            for raw in pages:
                page_id = self._resolve_page_id(sess, raw)
                if not page_id:
                    continue
                params = {
                    "fields": "message,permalink_url,created_time,from",
                    "limit": "25",
                    "access_token": self.app_token,
                }
                last_iso = self.page_last_seen.get(page_id)
                if last_iso:
                    params["since"] = last_iso
                url = f"{self.graph_base}/{page_id}/feed"
                try:
                    resp = sess.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        if resp.status_code in (429, 503, 502):
                            self.proxy_manager.cooldown(getattr(sess, 'proxies', {}).get('http'), minutes=2, reason="fb rate")
                        continue
                    data = resp.json()
                    items = data.get('data') or []
                    # newest first; ensure deterministic order oldest→newest for processing
                    posts = list(reversed(items))
                    # update last seen to max created_time encountered
                    max_created = last_iso
                    for post in posts:
                        created = post.get('created_time')
                        permalink = post.get('permalink_url')
                        message = post.get('message') or ''
                        author = (post.get('from') or {}).get('name') or ''
                        if not permalink or not created:
                            continue
                        # Dedup by source_url and keyword
                        cache_key = f"{kw.id}_{permalink}"
                        if cache_key in self.seen_cache and time.time() - self.seen_cache[cache_key] < 3600:
                            continue
                        try:
                            existing = Mention.objects.filter(source_url=permalink, keyword_id=str(kw.id)).first()
                            if existing:
                                self.seen_cache[cache_key] = time.time()
                                continue
                        except Exception:
                            pass
                        # Match
                        matched = False
                        title = message[:120]
                        if ContentType.TITLES.value in (kw.content_types or []):
                            if self.matching_engine.match_keyword(kw, title, ContentType.TITLES.value):
                                matched = True
                        if not matched and ContentType.BODY.value in (kw.content_types or []):
                            if self.matching_engine.match_keyword(kw, message, ContentType.BODY.value):
                                matched = True
                        if matched:
                            try:
                                mention = Mention(
                                    keyword_id=str(kw.id),
                                    user_id=kw.user_id,
                                    content=message or title,
                                    title=title,
                                    author=author,
                                    source_url=permalink,
                                    platform=Platform.FACEBOOK.value,
                                    content_type=(MentionContentType.BODY.value if message else MentionContentType.TITLE.value),
                                    matched_text=kw.keyword,
                                    match_position=0,
                                    match_confidence=1.0,
                                    mention_date=datetime.fromisoformat(created.replace('Z', '+00:00')),
                                    discovered_at=timezone.now(),
                                )
                                mention.platform_item_id = permalink
                                mention.save()
                                email_notification_service.send_mention_notification(mention)
                                logger.info(f"Facebook mention saved: {permalink}")
                            except Exception as e:
                                logger.error(f"Failed to save Facebook mention: {e}")
                        self.seen_cache[cache_key] = time.time()
                        # track max created
                        try:
                            if not max_created or created > max_created:
                                max_created = created
                        except Exception:
                            max_created = created or max_created
                    if max_created:
                        self.page_last_seen[page_id] = max_created
                except Exception as e:
                    logger.warning(f"Facebook API error for page {page_id}: {e}")

    def _tick_public_scrape(self, sess, keywords: List[Keyword]):
        for kw in keywords:
            if kw.platform not in [Platform.FACEBOOK.value, Platform.ALL.value]:
                continue
            pages = kw.platform_specific_filters or []
            try:
                src = PlatformSource.objects(user_id=kw.user_id, platform=Platform.FACEBOOK.value).first()
                if src and src.sources:
                    pages = src.sources
            except Exception:
                pass
            if not pages:
                continue
            for raw in pages:
                slug = (raw or '').replace('page:', '').strip()
                if slug.startswith('http'):
                    # Try to extract last path segment as slug
                    try:
                        slug = slug.rstrip('/').split('/')[-1]
                    except Exception:
                        pass
                if not slug:
                    continue
                url = f"https://mbasic.facebook.com/{slug}/posts/"
                try:
                    resp = sess.get(url, timeout=30, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                    })
                    if resp.status_code != 200:
                        continue
                    html = resp.text or ""
                    # naive extraction of story links and snippets
                    items: List[Dict[str, str]] = []
                    pos = 0
                    seen_links = set()
                    while True:
                        i = html.find("href=\"/story.php?", pos)
                        if i == -1:
                            break
                        j = html.find('"', i + 6)
                        if j == -1:
                            break
                        href = html[i+6:j]
                        pos = j + 1
                        if href in seen_links:
                            continue
                        seen_links.add(href)
                        permalink = "https://www.facebook.com" + href
                        # crude nearby text snippet
                        snippet_start = max(0, i - 300)
                        snippet = html[snippet_start:i]
                        snippet = snippet.split('>')[-1]
                        snippet = snippet.replace('&nbsp;', ' ').replace('&amp;', '&')
                        items.append({"permalink": permalink, "message": snippet.strip()})
                    # Process oldest-first
                    for it in items[-25:]:
                        permalink = it.get('permalink')
                        message = it.get('message') or ''
                        cache_key = f"{kw.id}_{permalink}"
                        if cache_key in self.seen_cache and time.time() - self.seen_cache[cache_key] < 3600:
                            continue
                        try:
                            existing = Mention.objects.filter(source_url=permalink, keyword_id=str(kw.id)).first()
                            if existing:
                                self.seen_cache[cache_key] = time.time()
                                continue
                        except Exception:
                            pass
                        # Matching
                        matched = False
                        title = message[:120]
                        if ContentType.TITLES.value in (kw.content_types or []):
                            if self.matching_engine.match_keyword(kw, title, ContentType.TITLES.value):
                                matched = True
                        if not matched and ContentType.BODY.value in (kw.content_types or []):
                            if self.matching_engine.match_keyword(kw, message, ContentType.BODY.value):
                                matched = True
                        if matched:
                            try:
                                mention = Mention(
                                    keyword_id=str(kw.id),
                                    user_id=kw.user_id,
                                    content=message or title,
                                    title=title,
                                    author='',
                                    source_url=permalink,
                                    platform=Platform.FACEBOOK.value,
                                    content_type=(MentionContentType.BODY.value if message else MentionContentType.TITLE.value),
                                    matched_text=kw.keyword,
                                    match_position=0,
                                    match_confidence=1.0,
                                    mention_date=timezone.now(),
                                    discovered_at=timezone.now(),
                                )
                                mention.platform_item_id = permalink
                                mention.save()
                                email_notification_service.send_mention_notification(mention)
                                logger.info(f"Facebook (public) mention saved: {permalink}")
                            except Exception as e:
                                logger.error(f"Failed to save Facebook (public) mention: {e}")
                        self.seen_cache[cache_key] = time.time()
                except Exception:
                    continue


# Global instance
facebook_service = FacebookService()


