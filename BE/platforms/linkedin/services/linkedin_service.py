import time
import os
import logging
import threading
import random
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from django.utils import timezone
from datetime import datetime

from core.models import Keyword, Mention, PlatformSource, MonitorCursor
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service
from core.services.proxy_service import ProxyManager


logger = logging.getLogger(__name__)


def _norm_source(value: str) -> Optional[str]:
    if not value:
        return None
    v = value.strip()
    if v.startswith('http'):
        return v.rstrip('/')
    if v.lower().startswith('hashtag:'):
        tag = v.split(':', 1)[1].strip('# ')
        return f"https://www.linkedin.com/feed/hashtag/{tag}/"
    if v.lower().startswith('company:'):
        slug = v.split(':', 1)[1]
        return f"https://www.linkedin.com/company/{slug}/posts/"
    if v.lower().startswith('profile:'):
        handle = v.split(':', 1)[1]
        return f"https://www.linkedin.com/in/{handle}/recent-activity/all/"
    return None


class LinkedInService:
    """Best-effort public LinkedIn monitoring (no auth).

    Strategy: user-provided public sources (hashtag/company/profile URLs). We fetch
    the source page, collect recent post permalinks, and open each to extract og:title
    and og:description for matching. Many pages are login-gated; we detect gates and
    back off for those sources.
    """

    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.matching_engine = GenericMatchingEngine()
        self.proxy_manager = ProxyManager()
        self.driver: Optional[uc.Chrome] = None
        self.headless = True
        # Poll interval (default 120s)
        self.check_interval = int(os.environ.get("KLEIO_LINKEDIN_CHECK_INTERVAL_SEC", "120"))
        # Cursors and cooldowns
        self.source_last_seen: Dict[str, str] = {}
        self.source_cooldown_until: Dict[str, float] = {}
        # Auth config
        self.auth_enabled = (os.environ.get("KLEIO_LINKEDIN_AUTH_ENABLED", "").lower() == "true")
        self.li_at_cookie = os.environ.get("KLEIO_LINKEDIN_LI_AT", "").strip()
        self.li_user = os.environ.get("KLEIO_LI_USER", "").strip()
        self.li_pass = os.environ.get("KLEIO_LI_PASS", "").strip()
        self.li_totp_secret = os.environ.get("KLEIO_LI_TOTP_SECRET", "").strip()
        self.fixed_proxy = os.environ.get("KLEIO_LINKEDIN_PROXY", "").strip() or None

    def _get_cursor(self, user_id: str, scope: str) -> Optional[str]:
        try:
            item = MonitorCursor.objects(user_id=user_id, platform=Platform.LINKEDIN.value, scope=scope).first()
            return item.cursor if item else None
        except Exception:
            return None

    def _set_cursor(self, user_id: str, scope: str, cursor_val: str) -> None:
        try:
            item = MonitorCursor.objects(user_id=user_id, platform=Platform.LINKEDIN.value, scope=scope).first()
            if not item:
                item = MonitorCursor(user_id=user_id, platform=Platform.LINKEDIN.value, scope=scope, cursor=cursor_val)
            else:
                item.cursor = cursor_val
            item.save()
        except Exception:
            pass

    def start_stream_monitoring(self, keywords: List[Keyword]):
        if self.is_monitoring:
            logger.info("LinkedIn monitoring already running")
            return
        self.is_monitoring = True
        self._ensure_driver()
        if self.auth_enabled:
            try:
                self._ensure_authenticated()
            except Exception as e:
                logger.warning(f"LinkedIn auth init failed: {e}")
        self.monitor_thread = threading.Thread(target=self._run_loop, args=(keywords,), daemon=True)
        self.monitor_thread.start()
        logger.info("Started LinkedIn monitoring")

    def stop_stream_monitoring(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception:
            pass
        logger.info("Stopped LinkedIn monitoring")

    def _run_loop(self, keywords: List[Keyword]):
        while self.is_monitoring:
            try:
                self._tick(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"LinkedIn monitor loop error: {e}")
                time.sleep(60)

    def _tick(self, keywords: List[Keyword]):
        try:
            self.proxy_manager.reload()
        except Exception:
            pass
        for kw in keywords:
            if kw.platform not in [Platform.LINKEDIN.value, Platform.ALL.value]:
                continue
            # Optional: authenticated recent-post search
            if self.auth_enabled:
                try:
                    self._process_recent_posts_search(kw)
                except Exception:
                    pass
            sources = kw.platform_specific_filters or []
            try:
                src = PlatformSource.objects(user_id=kw.user_id, platform=Platform.LINKEDIN.value).first()
                if src and src.sources:
                    sources = src.sources
            except Exception:
                pass
            for raw in sources:
                url = _norm_source(raw)
                if not url:
                    continue
                now = time.time()
                if now < self.source_cooldown_until.get(url, 0):
                    continue
                try:
                    # preflight host
                    base = '/'.join(url.split('/')[:3])
                    try:
                        self.driver.get(base)
                        time.sleep(random.uniform(1.0, 2.0))
                    except Exception:
                        pass
                    self.driver.get(url)
                    time.sleep(random.uniform(1.0, 2.0))
                    title_lc = (self.driver.title or '').lower()
                    src = self.driver.page_source or ''
                    if 'sign in' in title_lc or 'join' in title_lc or 'sign up' in title_lc or 'you’re signed out' in title_lc or 'you\'re signed out' in title_lc:
                        # gate detected
                        self.source_cooldown_until[url] = time.time() + 6 * 3600
                        continue
                    permalinks: List[str] = []
                    try:
                        anchors = self.driver.find_elements(By.TAG_NAME, 'a')
                        for a in anchors:
                            href = (a.get_attribute('href') or '').strip()
                            if not href:
                                continue
                            if 'linkedin.com/feed/update' in href or '/posts/' in href or '/activity/' in href:
                                if href not in permalinks:
                                    permalinks.append(href)
                    except Exception:
                        pass
                    if not permalinks:
                        continue
                    # Determine new head-tail
                    last_head = self.source_last_seen.get(url) or self._get_cursor(kw.user_id, f"{kw.id}:{url}")
                    if not last_head:
                        self.source_last_seen[url] = permalinks[0]
                        self._set_cursor(kw.user_id, f"{kw.id}:{url}", permalinks[0])
                        continue
                    new_links: List[str] = []
                    for link in permalinks:
                        if link == last_head:
                            break
                        new_links.append(link)
                    for link in reversed(new_links):
                        self._process_permalink(kw, link)
                    # update head
                    self.source_last_seen[url] = permalinks[0]
                    self._set_cursor(kw.user_id, f"{kw.id}:{url}", permalinks[0])
                except TimeoutException:
                    self._rotate_proxy()
                    continue
                except WebDriverException:
                    self._rotate_proxy()
                    continue
                except Exception:
                    # brief backoff
                    self.source_cooldown_until[url] = time.time() + 3600
                    continue

    def _process_permalink(self, kw: Keyword, url: str):
        try:
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            # og tags
            title = ''
            desc = ''
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
                title = el.get_attribute('content') or ''
            except Exception:
                pass
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']")
                desc = el.get_attribute('content') or ''
            except Exception:
                pass
            content = desc or title
            if not content:
                return
            matched = False
            if ContentType.TITLES.value in (kw.content_types or []):
                if self.matching_engine.match_keyword(kw, title, ContentType.TITLES.value):
                    matched = True
            if not matched and ContentType.BODY.value in (kw.content_types or []):
                if self.matching_engine.match_keyword(kw, content, ContentType.BODY.value):
                    matched = True
            if not matched:
                return
            # dedupe
            from_url = url
            cache_key = f"{kw.id}_{from_url}"
            # light in-memory window
            # DB dedupe
            try:
                existing = Mention.objects.filter(source_url=from_url, keyword_id=str(kw.id)).first()
                if existing:
                    return
            except Exception:
                pass
            mention = Mention(
                keyword_id=str(kw.id),
                user_id=kw.user_id,
                content=content,
                title=title,
                author='',
                source_url=from_url,
                platform=Platform.LINKEDIN.value,
                content_type=(MentionContentType.BODY.value if desc else MentionContentType.TITLE.value),
                matched_text=kw.keyword,
                match_position=0,
                match_confidence=1.0,
                mention_date=timezone.now(),
                discovered_at=timezone.now(),
            )
            mention.platform_item_id = from_url
            try:
                mention.save()
                email_notification_service.send_mention_notification(mention)
                logger.info(f"LinkedIn mention saved: {from_url}")
            except Exception as e:
                logger.error(f"Failed to save LinkedIn mention: {e}")
        except Exception:
            return

    def _ensure_driver(self):
        if self.driver is not None:
            return
        proxy = self.fixed_proxy or self.proxy_manager.for_chrome()
        self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)

    def _rotate_proxy(self):
        try:
            proxy = self.fixed_proxy or self.proxy_manager.for_chrome()
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)
        except Exception:
            pass

    def _process_recent_posts_search(self, kw: Keyword):
        """Authenticated search for recent posts for the given keyword."""
        if not (kw.keyword or "").strip():
            return
        # If we lost auth, try to re-establish
        if not self._is_authenticated():
            self._ensure_authenticated()
            if not self._is_authenticated():
                return
        q = (kw.keyword or "").strip()
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={quote_plus(q)}&sortBy=%5B%22date_posted%22%5D"
        try:
            self.driver.get(search_url)
            time.sleep(random.uniform(1.0, 2.0))
            links: List[str] = []
            for _ in range(5):
                try:
                    anchors = self.driver.find_elements(By.CSS_SELECTOR, "a.app-aware-link[href*='/feed/update/'], a.app-aware-link[href*='/posts/']")
                    for a in anchors:
                        href = (a.get_attribute('href') or '').strip()
                        if not href:
                            continue
                        if ('/feed/update/urn:li:activity:' in href or '/posts/' in href) and href not in links:
                            links.append(href)
                except Exception:
                    pass
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.8, 1.5))
            if not links:
                return
            scope = f"{kw.id}:search:{q}"
            last_top = self._get_cursor(kw.user_id, scope)
            if not last_top:
                self._set_cursor(kw.user_id, scope, links[0])
                return
            new_links: List[str] = []
            for u in links:
                if u == last_top:
                    break
                new_links.append(u)
            for u in reversed(new_links):
                self._process_permalink(kw, u)
            self._set_cursor(kw.user_id, scope, links[0])
        except TimeoutException:
            self._rotate_proxy()
        except WebDriverException:
            self._rotate_proxy()
        except Exception:
            return

    def _is_authenticated(self) -> bool:
        try:
            title = (self.driver.title or "").lower()
            cur = (self.driver.current_url or "").lower()
            # heuristic: if on feed or profile navigation elements present
            if "feed" in cur or "linkedin" in title:
                return True
        except Exception:
            pass
        return False

    def _ensure_authenticated(self):
        """Authenticate using li_at cookie, else attempt username/password + TOTP."""
        try:
            self.driver.get("https://www.linkedin.com/")
            time.sleep(random.uniform(0.8, 1.2))
        except Exception:
            pass
        # Cookie path
        if self.li_at_cookie:
            try:
                self.driver.add_cookie({
                    "name": "li_at",
                    "value": self.li_at_cookie,
                    "domain": ".linkedin.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                })
                self.driver.refresh()
                time.sleep(random.uniform(1.0, 1.5))
                if self._is_authenticated():
                    return
            except Exception:
                pass
        # Credential path with optional TOTP
        if self.li_user and self.li_pass:
            try:
                self.driver.get("https://www.linkedin.com/login")
                time.sleep(random.uniform(1.0, 1.5))
                try:
                    el = self.driver.find_element(By.ID, "username")
                    el.clear(); el.send_keys(self.li_user)
                    el = self.driver.find_element(By.ID, "password")
                    el.clear(); el.send_keys(self.li_pass)
                    btns = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
                    if btns:
                        btns[0].click()
                        time.sleep(random.uniform(1.2, 2.0))
                except Exception:
                    pass
                # TOTP if challenged
                if self.li_totp_secret:
                    try:
                        import pyotp  # lazy import
                        code = pyotp.TOTP(self.li_totp_secret).now()
                        candidates = [
                            "input[name='pin']",
                            "input[name='otp']",
                            "input[autocomplete='one-time-code']",
                            "input[type='tel']",
                        ]
                        filled = False
                        for sel in candidates:
                            fields = self.driver.find_elements(By.CSS_SELECTOR, sel)
                            if fields:
                                fields[0].clear(); fields[0].send_keys(code)
                                filled = True
                                break
                        if filled:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button")
                            if buttons:
                                buttons[0].click()
                            time.sleep(random.uniform(1.2, 2.0))
                    except Exception:
                        pass
            except Exception:
                return

    @staticmethod
    def _create_driver(headless: bool = True, proxy_url: Optional[str] = None) -> uc.Chrome:
        options = uc.ChromeOptions()
        options.headless = headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        if headless:
            options.add_argument("--headless=new")
        if proxy_url:
            options.add_argument(f"--proxy-server={proxy_url}")
        try:
            driver = uc.Chrome(options=options)
        except Exception:
            driver = uc.Chrome(options=options, version_main=None)
        driver.set_page_load_timeout(30)
        return driver


# Global instance
linkedin_service = LinkedInService()


