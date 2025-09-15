#!/usr/bin/env python
"""
Twitter monitoring service using Nitter-based scraping (no snscrape)
"""
import os
import sys
import time
import threading
# snscrape intentionally not used
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.utils import timezone
import logging
import re
import subprocess
from urllib.parse import quote_plus
import random

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.models import Keyword, Mention
from core.services.proxy_service import ProxyManager
from core.enums import Platform, ContentType
from core.services.matching_engine import GenericMatchingEngine
from core.services.email_service import email_notification_service
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

DEFAULT_NITTER_INSTANCES: List[str] = [
    "https://xcancel.com",
    "https://nitter.tiekoetter.com",
    "https://nitter.net"
]


def _normalize_instance_url(value: str) -> str:
    v = (value or "").strip().rstrip("/")
    if not v:
        return v
    if not v.startswith("http://") and not v.startswith("https://"):
        v = f"https://{v}"
    return v


def _unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for it in items:
        if it in seen or not it:
            continue
        seen.add(it)
        result.append(it)
    return result


def _get_chrome_version() -> Optional[int]:
    try:
        result = subprocess.run([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--version",
        ], capture_output=True, text=True)
        if result.returncode == 0:
            version = re.search(r"(\d+)", result.stdout)
            return int(version.group(1)) if version else None
    except Exception:
        pass
    return None


def _create_driver(headless: bool = True, user_data_dir: Optional[str] = None, proxy_url: Optional[str] = None) -> uc.Chrome:
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
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
    if proxy_url:
        options.add_argument(f"--proxy-server={proxy_url}")

    chrome_version = _get_chrome_version()
    try:
        if chrome_version:
            driver = uc.Chrome(options=options, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=options)
    except Exception:
        driver = uc.Chrome(options=options, version_main=None)

    driver.set_page_load_timeout(30)
    return driver


def _build_search_url(
    instance: str,
    query: str,
    include_replies: bool = False,
    include_empty_range_params: bool = True,
) -> str:
    base = _normalize_instance_url(instance)
    # Exact format requested:
    # https://<instance>/search?f=tweets&q=<query>&e-nativeretweets=on&since=&until=&near=
    params = [
        "f=tweets",
        f"q={quote_plus(query)}",
    ]
    # if include_replies:
    #     params.append("f-replies=on")
    params.append("e-nativeretweets=on")
    if include_empty_range_params:
        params.extend(["since=", "until=", "near="])
    return f"{base}/search?{'&'.join(params)}"


# Retweet detection removed; some instances mislabel items


class TwitterService:
    """Twitter monitoring service using Nitter scraping"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.tweet_cache = {}  # Cache to avoid duplicates
        self.matching_engine = GenericMatchingEngine()
        self.check_interval = 30  # Check every 30 seconds
        # Nitter configuration
        self.nitter_driver = None
        self.nitter_instances = list(DEFAULT_NITTER_INSTANCES)
        self.instance_cooldowns: Dict[str, float] = {}
        # Headless default
        self.headless = True
        self.proxy_manager = ProxyManager()
        
    def start_monitoring(self):
        """Initialize monitoring start time"""
        self.last_check_time = timezone.now()
        logger.info("Twitter monitoring initialized")
    
    def start_stream_monitoring(self, keywords: List[Keyword]):
        """Start real-time Twitter monitoring"""
        if self.is_monitoring:
            logger.info("Twitter monitoring already running")
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(keywords,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started Twitter streaming for {len(keywords)} keywords")
    
    def stop_stream_monitoring(self):
        """Stop Twitter monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        try:
            if self.nitter_driver:
                self.nitter_driver.quit()
                self.nitter_driver = None
        except Exception:
            pass
        logger.info("Stopped Twitter streaming")
    
    def _run_monitoring_loop(self, keywords: List[Keyword]):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_for_new_tweets(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in Twitter monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
            # small pause between cycles to avoid hammering instances
            time.sleep(1)
    
    def _check_for_new_tweets(self, keywords: List[Keyword]):
        """Check for new tweets matching keywords"""
        try:
            current_time = timezone.now()
            
            for keyword in keywords:
                if not self._should_monitor_keyword(keyword):
                    continue
                
                # Nitter-only search
                logger.debug(f"Searching (Nitter) for keyword: {keyword.keyword}")
                try:
                    tweets = self._search_tweets_via_nitter(keyword, limit=20)
                except Exception as e:
                    logger.error(f"Nitter search error: {e}")
                    tweets = []
                
                for tweet in tweets:
                    if self._is_new_tweet(tweet, keyword):
                        self._process_tweet_for_keyword(tweet, keyword)
                        
        except Exception as e:
            logger.error(f"Error checking for new tweets: {e}")
    
    # snscrape-based search removed

    def _ensure_nitter_driver(self):
        if self.nitter_driver is None:
            # Headless by default
            proxy = self.proxy_manager.for_chrome()
            self.nitter_driver = _create_driver(headless=self.headless, user_data_dir=None, proxy_url=proxy)
            if proxy:
                logger.info(f"Using proxy: {proxy}")

    def _select_proxy(self) -> Optional[str]:
        try:
            if not self.proxies:
                return None
            # skip proxies in cooldown
            attempts = 0
            while attempts < len(self.proxies):
                proxy = self.proxies[self.proxy_index % len(self.proxies)]
                self.proxy_index += 1
                until_ts = self.proxy_cooldowns.get(proxy, 0)
                if time.time() >= until_ts:
                    return proxy
                attempts += 1
            return None
        except Exception:
            return None

    def _rotate_proxy_and_restart(self):
        try:
            proxy = self.proxy_manager.for_chrome()
            try:
                if self.nitter_driver:
                    self.nitter_driver.quit()
            except Exception:
                pass
            self.nitter_driver = _create_driver(headless=self.headless, user_data_dir=None, proxy_url=proxy)
            if proxy:
                logger.info(f"Switched to proxy: {proxy}")
        except Exception as e:
            logger.warning(f"Failed to rotate proxy: {e}")

    def _cooldown_instance(self, instance: str, minutes: int = 2) -> None:
        try:
            normalized = _normalize_instance_url(instance)
            self.instance_cooldowns[normalized] = time.time() + minutes * 60
        except Exception:
            pass

    # Removed debug HTML saving to avoid file creation

    def _search_tweets_via_nitter(self, keyword: Keyword, limit: int = 20) -> List[Dict]:
        """Search using Nitter instances as a fallback.
        Maps results to the same structure used by snscrape branch.
        """
        results: List[Dict] = []
        self._ensure_nitter_driver()

        # Determine whether to include replies in query string
        wants_replies = ContentType.COMMENTS.value in (keyword.content_types or [])
        for inst in self.nitter_instances:
                # skip instances in cooldown for 2 minutes
                now = time.time()
                until_ts = self.instance_cooldowns.get(inst, 0)
                if now < until_ts:
                    continue
                url = _build_search_url(inst, keyword.keyword, include_replies=wants_replies, include_empty_range_params=True)
                try:
                    # Preflight: visit instance root to allow cookies/JS to set state
                    base_url = _normalize_instance_url(inst)
                    try:
                        self.nitter_driver.get(base_url)
                        time.sleep(random.uniform(1.0, 2.0))
                    except Exception:
                        pass
                    logger.info(f"Fetching URL: {url}")
                    self.nitter_driver.get(url)
                    time.sleep(random.uniform(1.0, 2.0))
                    # Detect anti-bot page early
                    page_title = self.nitter_driver.title or ""
                    page_source = self.nitter_driver.page_source or ""
                    if ("Verifying your request" in page_title) or ("/check/" in page_source):
                        logger.warning(f"Anti-bot page detected on {inst}; retrying with new proxy/direct before cooldown")
                        # Retry once with a rotated proxy
                        if self._retry_instance_once(inst, url):
                            # Successful retry; proceed to parse items
                            pass
                        else:
                            self._cooldown_instance(inst, minutes=10)
                            continue
                    WebDriverWait(self.nitter_driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".timeline-item"))
                    )
                    items = self.nitter_driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
                    if not items:
                        # No items found
                        pass
                    for el in items[: max(1, int(limit))]:
                        time.sleep(random.uniform(0.5, 1.5))
                        # Do not skip items; some instances mislabel retweets
                        # Extract fields
                        def safe_text(selector: str) -> str:
                            try:
                                return el.find_element(By.CSS_SELECTOR, selector).text.strip()
                            except Exception:
                                return ""

                        text = safe_text(".tweet-content")
                        username = safe_text(".username").lstrip("@")
                        tweet_id = ""
                        twitter_url = ""
                        nitter_url = ""
                        try:
                            link_elem = el.find_element(By.CSS_SELECTOR, ".tweet-link")
                            href = link_elem.get_attribute("href") or ""
                            if href:
                                nitter_url = f"{_normalize_instance_url(inst)}{href}"
                                id_match = re.search(r"/status/(\d+)", href)
                                tweet_id = id_match.group(1) if id_match else ""
                                if tweet_id and username:
                                    twitter_url = f"https://x.com/{username}/status/{tweet_id}"
                        except Exception:
                            pass

                        if not (tweet_id or nitter_url):
                            continue

                        results.append({
                            'id': str(tweet_id or nitter_url),
                            'content': text,
                            'author': username,
                            'author_id': None,
                            'date': timezone.now(),
                            'url': twitter_url or nitter_url,
                            'nitter_url': nitter_url,
                            'reply_count': 0,
                            'retweet_count': 0,
                            'like_count': 0,
                            'is_reply': False,  # tweets page primarily; replies still may appear threaded
                            'parent_tweet_id': None,
                            'hashtags': [],
                            'mentions': [],
                        })
                    if results:
                        return results[:limit]
                except TimeoutException as e:
                    logger.warning(f"Nitter instance timed out: {inst} (TimeoutException) on URL {url}")
                    self._cooldown_instance(inst, minutes=2)
                    self._rotate_proxy_and_restart()
                    continue
                except WebDriverException as e:
                    logger.warning(f"Nitter instance WebDriver error: {inst} ({e.__class__.__name__}: {e}) on URL {url}")
                    self._cooldown_instance(inst, minutes=2)
                    self._rotate_proxy_and_restart()
                    continue
                except Exception as e:
                    logger.warning(f"Nitter instance failed: {inst} ({e}) on URL {url}")
                    self._cooldown_instance(inst, minutes=1)
                    continue
        # Fallback: if nothing found and cooldowns may have skipped all instances, try a second pass ignoring cooldowns
        if not results and self.nitter_instances:
            for inst in self.nitter_instances:
                url = _build_search_url(inst, keyword.keyword, include_replies=wants_replies, include_empty_range_params=True)
                try:
                    self._rotate_proxy_and_restart()
                    logger.info(f"Retrying (ignore cooldown) URL: {url}")
                    self.nitter_driver.get(url)
                    time.sleep(random.uniform(1.0, 2.0))
                    WebDriverWait(self.nitter_driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".timeline-item"))
                    )
                    items = self.nitter_driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
                    for el in items[: max(1, int(limit))]:
                        def safe_text(selector: str) -> str:
                            try:
                                return el.find_element(By.CSS_SELECTOR, selector).text.strip()
                            except Exception:
                                return ""
                        text = safe_text(".tweet-content")
                        username = safe_text(".username").lstrip("@")
                        tweet_id = ""
                        twitter_url = ""
                        nitter_url = ""
                        try:
                            link_elem = el.find_element(By.CSS_SELECTOR, ".tweet-link")
                            href = link_elem.get_attribute("href") or ""
                            if href:
                                nitter_url = f"{_normalize_instance_url(inst)}{href}"
                                id_match = re.search(r"/status/(\d+)", href)
                                tweet_id = id_match.group(1) if id_match else ""
                                if tweet_id and username:
                                    twitter_url = f"https://x.com/{username}/status/{tweet_id}"
                        except Exception:
                            pass
                        if not (tweet_id or nitter_url):
                            continue
                        results.append({
                            'id': str(tweet_id or nitter_url),
                            'content': text,
                            'author': username,
                            'author_id': None,
                            'date': timezone.now(),
                            'url': twitter_url or nitter_url,
                            'nitter_url': nitter_url,
                            'reply_count': 0,
                            'retweet_count': 0,
                            'like_count': 0,
                            'is_reply': False,
                            'parent_tweet_id': None,
                            'hashtags': [],
                            'mentions': [],
                        })
                    if results:
                        break
                except Exception:
                    continue
        return results[:limit]

    def _restart_with_proxy(self, proxy: Optional[str]):
        try:
            if self.nitter_driver:
                try:
                    self.nitter_driver.quit()
                except Exception:
                    pass
            self.nitter_driver = _create_driver(headless=self.headless, user_data_dir=None, proxy_url=proxy)
            if proxy:
                logger.info(f"Switched to proxy: {proxy}")
            else:
                logger.info("Switched to direct connection (no proxy)")
        except Exception as e:
            logger.warning(f"Failed to restart driver with proxy {proxy}: {e}")

    def _retry_instance_once(self, inst: str, url: str) -> bool:
        """Rotate proxy and try once; if still blocked, try direct once. Returns True if page no longer shows anti-bot."""
        # Try with rotated proxy
        try:
            proxy = self._select_proxy()
            self._restart_with_proxy(proxy)
            base_url = _normalize_instance_url(inst)
            try:
                self.nitter_driver.get(base_url)
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass
            self.nitter_driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            title = self.nitter_driver.title or ""
            src = self.nitter_driver.page_source or ""
            if ("Verifying your request" not in title) and ("/check/" not in src):
                return True
        except Exception:
            pass
        # Try direct (no proxy)
        try:
            self._restart_with_proxy(None)
            base_url = _normalize_instance_url(inst)
            try:
                self.nitter_driver.get(base_url)
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass
            self.nitter_driver.get(url)
            time.sleep(random.uniform(1.0, 2.0))
            title = self.nitter_driver.title or ""
            src = self.nitter_driver.page_source or ""
            if ("Verifying your request" not in title) and ("/check/" not in src):
                return True
        except Exception:
            pass
        return False
    
    # Removed legacy time window logic (only relevant to snscrape)
    
    def _is_new_tweet(self, tweet: Dict, keyword: Keyword) -> bool:
        """Check if tweet is new and should be processed"""
        tweet_id = tweet['id']
        keyword_id = str(keyword.id)
        
        # Check cache
        cache_key = f"{keyword_id}_{tweet_id}"
        if cache_key in self.tweet_cache:
            return False
        
        # Add to cache
        self.tweet_cache[cache_key] = time.time()
        
        # Clean old cache entries (older than 1 hour)
        current_time = time.time()
        self.tweet_cache = {k: v for k, v in self.tweet_cache.items() 
                           if current_time - v < 3600}
        
        return True
    
    def _should_monitor_keyword(self, keyword: Keyword) -> bool:
        """Check if keyword should be monitored for Twitter"""
        return (keyword.platform in [Platform.TWITTER.value, Platform.ALL.value] and
                keyword.is_active)
    
    def _process_tweet_for_keyword(self, tweet: Dict, keyword: Keyword):
        """Process a tweet and check for keyword matches"""
        try:
            # Check content types based on keyword settings
            content_types_to_check = keyword.content_types or [ContentType.BODY.value]
            
            for content_type in content_types_to_check:
                if content_type == ContentType.BODY.value:
                    # Main tweet content
                    self._check_tweet_content(tweet, keyword, ContentType.BODY.value)
                    
                elif content_type == ContentType.COMMENTS.value:
                    # Only process if it's a reply
                    if tweet.get('is_reply'):
                        self._check_tweet_content(tweet, keyword, ContentType.COMMENTS.value)
                        
                elif content_type == ContentType.TITLES.value:
                    # Skip TITLES for Twitter (not applicable)
                    logger.debug(f"Skipping TITLES content type for Twitter tweet {tweet['id']}")
                    
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.get('id')}: {e}")
    
    def _check_tweet_content(self, tweet: Dict, keyword: Keyword, content_type: str):
        """Check if tweet content matches keyword"""
        content = tweet.get('content', '')
        
        # Check if keyword should monitor this content type
        if not self.matching_engine.should_monitor_content(keyword, content_type):
            return
        
        # Perform keyword matching
        match_result = self.matching_engine.match_keyword(keyword, content, content_type)
        
        if match_result:
            # Create mention
            mention = self._create_mention_from_tweet(tweet, keyword, match_result, content_type)
            if mention:
                self._save_mention(mention, keyword)
                logger.info(f"🎯 New Twitter mention! Keyword: '{keyword.keyword}' - {content[:50]}...")
    
    def _create_mention_from_tweet(self, tweet: Dict, keyword: Keyword, match_result, content_type: str) -> Optional[Mention]:
        """Create a Mention object from a Twitter tweet"""
        try:
            # Check for duplicates
            existing_mention = Mention.objects.filter(
                source_url=tweet['url'],
                keyword_id=str(keyword.id)
            ).first()
            
            if existing_mention:
                return None
            
            # Create new mention
            mention = Mention(
                keyword_id=str(keyword.id),
                user_id=keyword.user_id,
                content=tweet['content'],
                title=f"Tweet by @{tweet['author']}",
                author=tweet['author'],
                source_url=tweet['url'],
                platform=Platform.TWITTER.value,
                subreddit='twitter',  # Using subreddit field for platform location
                content_type=content_type,
                matched_text=match_result.matched_text,
                match_position=match_result.position,
                match_confidence=match_result.confidence,
                mention_date=tweet['date'],
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = tweet['id']
            mention.platform_score = tweet.get('like_count', 0)
            mention.platform_comments_count = tweet.get('reply_count', 0)
            
            return mention
            
        except Exception as e:
            logger.error(f"Error creating mention from tweet: {str(e)}")
            return None
    
    def _save_mention(self, mention: Mention, keyword: Keyword):
        """Save mention and send notification"""
        try:
            mention.save()
            logger.info(f"💾 Saved Twitter mention: {mention.keyword_id} - {mention.title[:50]}...")
            
            # Send email notification
            success = email_notification_service.send_mention_notification(mention)
            if success:
                logger.info(f"📧 Email notification sent for mention {mention.id}")
            else:
                logger.error(f"Failed to send email notification for mention {mention.id}")
                
        except Exception as e:
            logger.error(f"Error saving mention: {e}")
    
    def reset_monitoring(self):
        """Reset monitoring state (useful for testing)"""
        self.last_check_time = None
        self.tweet_cache.clear()
        logger.info("Reset Twitter monitoring - will start fresh on next run")

# Global instance
twitter_service = TwitterService() 