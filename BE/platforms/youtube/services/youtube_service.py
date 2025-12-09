import time
import logging
import threading
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus
from datetime import datetime

import random
import aiohttp
import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from django.utils import timezone

from core.models import Keyword, Mention, MonitorCursor
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service
from core.services.proxy_service import ProxyManager

logger = logging.getLogger(__name__)


DEFAULT_INVIDIOUS_INSTANCES: List[str] = [
    "https://inv.nadeko.net",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://invidious.f5.si",
]

def _normalize_instance_url(value: str) -> str:
    v = (value or "").strip().rstrip("/")
    if not v:
        return v
    if not v.startswith("http://") and not v.startswith("https://"):
        v = f"https://{v}"
    return v


class YouTubeService:
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = 300
        self.instances = list(DEFAULT_INVIDIOUS_INSTANCES)
        self.instance_cooldowns: Dict[str, float] = {}
        self.proxy_manager = ProxyManager()
        # TTL caches
        self.detail_cache: Dict[str, Tuple[float, Dict]] = {}
        self.detail_ttl_sec = 1800  # 30 min
        self.seen_cache: Dict[str, float] = {}
        # Selenium driver (align tech stack with Nitter)
        self.driver = None
        self.headless = True
        # New item tracking
        self.last_seen_top_id: Dict[str, str] = {}
        self.started_at_ts: float = time.time()

    def _get_cursor(self, user_id: str, scope: str) -> Optional[str]:
        try:
            item = MonitorCursor.objects(user_id=user_id, platform=Platform.YOUTUBE.value, scope=scope).first()
            return item.cursor if item else None
        except Exception:
            return None

    def _set_cursor(self, user_id: str, scope: str, cursor_val: str) -> None:
        try:
            item = MonitorCursor.objects(user_id=user_id, platform=Platform.YOUTUBE.value, scope=scope).first()
            if not item:
                item = MonitorCursor(user_id=user_id, platform=Platform.YOUTUBE.value, scope=scope, cursor=cursor_val)
            else:
                item.cursor = cursor_val
            item.save()
        except Exception:
            pass

    def start_stream_monitoring(self, keywords: List[Keyword]):
        if self.is_monitoring:
            logger.info("YouTube monitoring already running")
            return
        self.is_monitoring = True
        # Reset start marker and per-keyword heads
        self.started_at_ts = time.time()
        self.last_seen_top_id.clear()
        self._ensure_driver()
        self.monitor_thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(keywords,),
            daemon=True,
        )
        self.monitor_thread.start()
        logger.info(f"Started YouTube monitoring for {len(keywords)} keywords")

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
        logger.info("Stopped YouTube monitoring")

    def _run_monitoring_loop(self, keywords: List[Keyword]):
        while self.is_monitoring:
            try:
                self._check_for_new_videos(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"YouTube monitor loop error: {e}")
                time.sleep(60)

    def _check_for_new_videos(self, keywords: List[Keyword]):
        # Pick up any new proxies added via UI/API
        try:
            self.proxy_manager.reload()
        except Exception:
            pass
        for keyword in keywords:
            if keyword.platform not in [Platform.YOUTUBE.value, Platform.ALL.value]:
                continue
            try:
                # Collect across pages within last hour; stop early at last seen head
                keyword_key = str(keyword.id)
                # Load persisted cursor if memory missing
                last_top = self.last_seen_top_id.get(keyword_key) or self._get_cursor(keyword.user_id, keyword_key)
                videos = self._search_invidious(keyword.keyword, limit=50, max_pages=5, stop_at_id=last_top)
                # Determine head/tail for incremental scanning per keyword
                ordered_ids = [it.get('videoId') for it in videos if it.get('videoId')]
                if not ordered_ids:
                    continue
                last_top = self.last_seen_top_id.get(keyword_key)
                # On first run after start/restart: set marker and skip backlog
                if not last_top:
                    self.last_seen_top_id[keyword_key] = ordered_ids[0]
                    continue
                # If head unchanged, nothing new
                if ordered_ids[0] == last_top:
                    continue
                # Collect new IDs above the last seen head
                new_ids: List[str] = []
                for vid in ordered_ids:
                    if vid == last_top:
                        break
                    new_ids.append(vid)
                # Process oldest first for stable ordering
                for vid in reversed(new_ids):
                    cache_key = f"{keyword.id}_{vid}"
                    if cache_key in self.seen_cache and time.time() - self.seen_cache[cache_key] < 3600:
                        continue
                    # Avoid DB duplicates across restarts
                    canonical_url = f"https://www.youtube.com/watch?v={vid}"
                    try:
                        existing = Mention.objects.filter(source_url=canonical_url, keyword_id=str(keyword.id)).first()
                        if existing:
                            self.seen_cache[cache_key] = time.time()
                            continue
                    except Exception:
                        pass
                    detail, inst_used = self._get_video_detail(vid)
                    if not detail:
                        continue
                    title = detail.get('title') or ''
                    description = detail.get('description') or ''
                    author = detail.get('author') or ''
                    source_url = canonical_url
                    # Match
                    matched = False
                    if ContentType.TITLES.value in (keyword.content_types or []):
                        if self.matching_engine.match_keyword(keyword, title, ContentType.TITLES.value):
                            matched = True
                    if not matched and ContentType.BODY.value in (keyword.content_types or []):
                        if self.matching_engine.match_keyword(keyword, description, ContentType.BODY.value):
                            matched = True
                    if matched:
                        mention = Mention(
                            keyword_id=str(keyword.id),
                            user_id=keyword.user_id,
                            content=description or title,
                            title=title,
                            author=author,
                            source_url=source_url,
                            platform=Platform.YOUTUBE.value,
                            content_type=(MentionContentType.BODY.value if description else MentionContentType.TITLE.value),
                            matched_text=keyword.keyword,
                            match_position=0,
                            match_confidence=1.0,
                            mention_date=datetime.fromtimestamp(detail.get('published') or time.time()),
                            discovered_at=timezone.now(),
                        )
                        mention.platform_item_id = vid
                        try:
                            mention.save()
                            email_notification_service.send_mention_notification(mention)
                            logger.info(f"YouTube mention saved: {vid} - {title[:50]}...")
                        except Exception as e:
                            logger.error(f"Failed to save YouTube mention: {e}")
                    self.seen_cache[cache_key] = time.time()
                # Update head marker after processing
                self.last_seen_top_id[keyword_key] = ordered_ids[0]
                self._set_cursor(keyword.user_id, keyword_key, ordered_ids[0])
            except Exception as e:
                logger.error(f"YouTube keyword check failed for '{keyword.keyword}': {e}")

    def _search_invidious(self, q: str, limit: int = 12, max_pages: int = 5, stop_at_id: Optional[str] = None) -> List[Dict]:
        for inst in self.instances:
            now = time.time()
            if now < self.instance_cooldowns.get(inst, 0):
                continue
            inst_norm = _normalize_instance_url(inst)
            try:
                # Preflight like Nitter flow
                try:
                    self.driver.get(inst_norm)
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    pass
                ids: List[str] = []
                for page in range(1, max_pages + 1):
                    url = (
                        f"{inst_norm}/search?q={quote_plus(q)}&page={page}&date=hour&type=video&duration=none&sort=date"
                    )
                    self.driver.get(url)
                    time.sleep(random.uniform(1.0, 2.0))
                    title = (self.driver.title or '').lower()
                    src = self.driver.page_source or ''
                    if 'too many requests' in title or 'captcha' in title or "i'm a teapot" in src.lower():
                        self._cooldown_instance(inst_norm, minutes=10)
                        if self._retry_instance_once(inst_norm, url):
                            src = self.driver.page_source or ''
                        else:
                            break
                    # Parse IDs using Selenium, mirroring Nitter approach (no bs4)
                    page_ids: List[str] = []
                    try:
                        link_elems = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='/watch?v='], a[href^='/watch/']")
                        for el in link_elems:
                            href = el.get_attribute('href') or ''
                            if '/watch?v=' in href:
                                vid = href.split('watch?v=')[-1].split('&')[0]
                            elif '/watch/' in href:
                                vid = href.split('/watch/')[-1].split('?')[0]
                            else:
                                vid = ''
                            if vid and vid not in page_ids:
                                page_ids.append(vid)
                        if not page_ids:
                            anchors = self.driver.find_elements(By.TAG_NAME, 'a')
                            for a in anchors:
                                href = a.get_attribute('href') or ''
                                if '/watch?v=' in href:
                                    vid = href.split('watch?v=')[-1].split('&')[0]
                                elif '/watch/' in href:
                                    vid = href.split('/watch/')[-1].split('?')[0]
                                else:
                                    vid = ''
                                if vid and vid not in page_ids:
                                    page_ids.append(vid)
                    except Exception:
                        pass
                    # Merge preserving order and stop when marker reached
                    for vid in page_ids:
                        if vid not in ids:
                            ids.append(vid)
                        if stop_at_id and vid == stop_at_id:
                            break
                    if stop_at_id and stop_at_id in ids:
                        break
                    if len(ids) >= limit:
                        break
                    if not page_ids:
                        break
                if ids:
                    return [{
                        'videoId': vid,
                        'title': '',
                        'author': ''
                    } for vid in ids[:limit]]
            except TimeoutException:
                self._cooldown_instance(inst_norm, minutes=2)
                self._rotate_proxy_and_restart()
                continue
            except WebDriverException as e:
                self._cooldown_instance(inst_norm, minutes=2)
                self._rotate_proxy_and_restart()
                continue
            except Exception:
                self._cooldown_instance(inst_norm, minutes=1)
                continue
        return []

    def _get_video_detail(self, video_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        # TTL cache
        now = time.time()
        if video_id in self.detail_cache:
            ts, data = self.detail_cache[video_id]
            if now - ts < self.detail_ttl_sec:
                # We don't store instance in cache; return data and None
                return data, None
        # Try Invidious instances using Selenium (HTML watch page)
        for inst in self.instances:
            if now < self.instance_cooldowns.get(inst, 0):
                continue
            inst_norm = _normalize_instance_url(inst)
            watch_url = f"{inst_norm}/watch?v={video_id}"
            try:
                # Preflight
                try:
                    self.driver.get(inst_norm)
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    pass
                self.driver.get(watch_url)
                time.sleep(random.uniform(1.0, 2.0))
                title_txt = (self.driver.title or '').lower()
                src = self.driver.page_source or ''
                if 'too many requests' in title_txt or 'captcha' in title_txt or "i'm a teapot" in src.lower():
                    self._cooldown_instance(inst_norm, minutes=10)
                    if not self._retry_instance_once(inst_norm, watch_url):
                        continue
                    src = self.driver.page_source or ''
                # Extract fields using Selenium (no bs4), similar to Nitter approach
                title = None
                desc = None
                author = None
                # OG title/description
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
                    title = el.get_attribute('content') or None
                except Exception:
                    pass
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']")
                    desc = el.get_attribute('content') or None
                except Exception:
                    pass
                # Fallbacks
                if not title:
                    try:
                        title = (self.driver.title or '').strip() or None
                    except Exception:
                        pass
                if not desc:
                    try:
                        el = self.driver.find_element(By.ID, 'description')
                        desc = (el.text or '').strip() or None
                    except Exception:
                        try:
                            el = self.driver.find_element(By.CSS_SELECTOR, 'div.description')
                            desc = (el.text or '').strip() or None
                        except Exception:
                            pass
                # Author
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, "meta[itemprop='author']")
                    author = el.get_attribute('content') or None
                except Exception:
                    pass
                if not author:
                    try:
                        # fallback to the first channel link heuristically
                        link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='/channel/'], a[href*='/@']")
                        author = (link.text or '').strip() or None
                    except Exception:
                        pass
                mapped = {
                    'videoId': video_id,
                    'title': title or '',
                    'author': author or '',
                    'description': desc or '',
                    'published': time.time(),
                }
                if mapped['title'] or mapped['description']:
                    self.detail_cache[video_id] = (now, mapped)
                    return mapped, inst_norm
            except TimeoutException:
                self._cooldown_instance(inst_norm, minutes=2)
                self._rotate_proxy_and_restart()
                continue
            except WebDriverException as e:
                self._cooldown_instance(inst_norm, minutes=2)
                self._rotate_proxy_and_restart()
                continue
            except Exception:
                self._cooldown_instance(inst_norm, minutes=1)
                continue
        return None, None

    def _ensure_driver(self):
        if self.driver is not None:
            return
        proxy = self.proxy_manager.for_chrome()
        self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)
        if proxy:
            logger.info(f"YouTube using proxy: {proxy}")

    def _restart_with_proxy(self, proxy: Optional[str]):
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)
            if proxy:
                logger.info(f"YouTube switched to proxy: {proxy}")
            else:
                logger.info("YouTube switched to direct connection")
        except Exception as e:
            logger.warning(f"Failed to restart YouTube driver: {e}")

    def _rotate_proxy_and_restart(self):
        try:
            proxy = self.proxy_manager.for_chrome()
            self._restart_with_proxy(proxy)
        except Exception as e:
            logger.warning(f"Failed to rotate YouTube proxy: {e}")

    def _cooldown_instance(self, instance: str, minutes: int = 2) -> None:
        try:
            normalized = _normalize_instance_url(instance)
            self.instance_cooldowns[normalized] = time.time() + minutes * 60
        except Exception:
            pass

    def _retry_instance_once(self, inst: str, url: str) -> bool:
        # Try rotated proxy
        try:
            proxy = self.proxy_manager.for_chrome()
            self._restart_with_proxy(proxy)
            base_url = _normalize_instance_url(inst)
            try:
                self.driver.get(base_url)
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            title = (self.driver.title or '').lower()
            src = self.driver.page_source or ''
            if 'too many requests' not in title and 'captcha' not in title and "i'm a teapot" not in src.lower():
                return True
        except Exception:
            pass
        # Try direct
        try:
            self._restart_with_proxy(None)
            base_url = _normalize_instance_url(inst)
            try:
                self.driver.get(base_url)
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            title = (self.driver.title or '').lower()
            src = self.driver.page_source or ''
            if 'too many requests' not in title and 'captcha' not in title and "i'm a teapot" not in src.lower():
                return True
        except Exception:
            pass
        return False

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

# Global instance (optional)
youtube_service = YouTubeService()

