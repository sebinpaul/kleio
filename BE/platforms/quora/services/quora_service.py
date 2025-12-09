import time
import logging
import threading
import random
from typing import Dict, List, Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from django.utils import timezone

from core.models import Keyword, Mention, PlatformSource
from core.enums import Platform, ContentType, MentionContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service
from core.services.proxy_service import ProxyManager


logger = logging.getLogger(__name__)


class QuoraService:
    """Public Quora monitoring via site search and topic feeds (no API)."""

    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.matching_engine = GenericMatchingEngine()
        self.proxy_manager = ProxyManager()
        self.driver: Optional[uc.Chrome] = None
        self.headless = True
        self.check_interval = 300
        # Cursors per keyword (top result URL)
        self.last_seen_top_url: Dict[str, str] = {}

    def start_stream_monitoring(self, keywords: List[Keyword]):
        if self.is_monitoring:
            logger.info("Quora monitoring already running")
            return
        self.is_monitoring = True
        self._ensure_driver()
        self.monitor_thread = threading.Thread(target=self._run_loop, args=(keywords,), daemon=True)
        self.monitor_thread.start()
        logger.info("Started Quora monitoring")

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
        logger.info("Stopped Quora monitoring")

    def _run_loop(self, keywords: List[Keyword]):
        while self.is_monitoring:
            try:
                self._tick(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Quora monitor loop error: {e}")
                time.sleep(60)

    def _tick(self, keywords: List[Keyword]):
        try:
            self.proxy_manager.reload()
        except Exception:
            pass
        for kw in keywords:
            if kw.platform not in [Platform.QUORA.value, Platform.ALL.value]:
                continue
            self._process_keyword(kw)
            # Optional topic sources from settings
            try:
                src = PlatformSource.objects(user_id=kw.user_id, platform=Platform.QUORA.value).first()
                if src and src.sources:
                    for topic_url in src.sources:
                        if isinstance(topic_url, str) and 'quora.com/topic/' in topic_url:
                            self._process_topic_feed(kw, topic_url)
            except Exception:
                pass

    def _process_keyword(self, kw: Keyword):
        query = kw.keyword.strip()
        if not query:
            return
        base = "https://www.quora.com"
        url = f"{base}/search?q={query.replace(' ', '+')}&type=question"
        try:
            # preflight
            try:
                self.driver.get(base)
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            # Collect result links with a few scrolls
            links: List[str] = []
            for _ in range(3):
                try:
                    anchors = self.driver.find_elements(By.TAG_NAME, 'a')
                    for a in anchors:
                        href = (a.get_attribute('href') or '').strip()
                        if not href:
                            continue
                        if href.startswith(base) and ('/answer/' in href or '/What-' in href or '/topic/' in href):
                            if href not in links:
                                links.append(href)
                except Exception:
                    pass
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.6, 1.2))
            if not links:
                return
            key = str(kw.id)
            last_top = self.last_seen_top_url.get(key)
            if not last_top:
                self.last_seen_top_url[key] = links[0]
                return
            new_urls: List[str] = []
            for u in links:
                if u == last_top:
                    break
                new_urls.append(u)
            for u in reversed(new_urls):
                self._process_permalink(kw, u)
            self.last_seen_top_url[key] = links[0]
        except TimeoutException:
            self._rotate_proxy()
        except WebDriverException:
            self._rotate_proxy()
        except Exception:
            return

    def _process_topic_feed(self, kw: Keyword, url: str):
        try:
            base = "https://www.quora.com"
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            links: List[str] = []
            for _ in range(2):
                try:
                    anchors = self.driver.find_elements(By.TAG_NAME, 'a')
                    for a in anchors:
                        href = (a.get_attribute('href') or '').strip()
                        if href.startswith(base) and ('/answer/' in href or '/What-' in href):
                            if href not in links:
                                links.append(href)
                except Exception:
                    pass
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(0.6, 1.2))
            for u in links[:10]:
                self._process_permalink(kw, u)
        except Exception:
            return

    def _process_permalink(self, kw: Keyword, url: str):
        try:
            self.driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            # og/meta
            title = ''
            desc = ''
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
                title = el.get_attribute('content') or ''
            except Exception:
                pass
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
                desc = el.get_attribute('content') or ''
            except Exception:
                pass
            body = desc or title
            if not body and not title:
                return
            matched = False
            if ContentType.TITLES.value in (kw.content_types or []):
                if self.matching_engine.match_keyword(kw, title, ContentType.TITLES.value):
                    matched = True
            if not matched and ContentType.BODY.value in (kw.content_types or []):
                if self.matching_engine.match_keyword(kw, body, ContentType.BODY.value):
                    matched = True
            if not matched:
                return
            # DB dedupe by URL
            try:
                existing = Mention.objects.filter(source_url=url, keyword_id=str(kw.id)).first()
                if existing:
                    return
            except Exception:
                pass
            mention = Mention(
                keyword_id=str(kw.id),
                user_id=kw.user_id,
                content=body or title,
                title=title,
                author='',
                source_url=url,
                platform=Platform.QUORA.value,
                content_type=(MentionContentType.BODY.value if body else MentionContentType.TITLE.value),
                matched_text=kw.keyword,
                match_position=0,
                match_confidence=1.0,
                mention_date=timezone.now(),
                discovered_at=timezone.now(),
            )
            mention.platform_item_id = url
            try:
                mention.save()
                email_notification_service.send_mention_notification(mention)
                logger.info(f"Quora mention saved: {url}")
            except Exception as e:
                logger.error(f"Failed to save Quora mention: {e}")
        except Exception:
            return

    def _ensure_driver(self):
        if self.driver is not None:
            return
        proxy = self.proxy_manager.for_chrome()
        self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)

    def _rotate_proxy(self):
        try:
            proxy = self.proxy_manager.for_chrome()
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = self._create_driver(headless=self.headless, proxy_url=proxy)
        except Exception:
            pass

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
quora_service = QuoraService()


