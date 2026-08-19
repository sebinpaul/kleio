#!/usr/bin/env python
"""
Twitter monitoring service using Nitter-based scraping (no snscrape)
"""
import os
import sys
import time
import threading
# snscrape intentionally not used
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone as datetime_timezone
from django.utils import timezone
import logging
import re
from urllib.parse import quote_plus
import random

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.models import Keyword, Mention
from core.enums import Platform, ContentType
from core.services.matching_engine import GenericMatchingEngine, MatchContext
from core.services.email_service import email_notification_service
from core.services.chrome_driver import create_driver as create_chrome_driver
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


def _create_driver(headless: bool = True, user_data_dir: Optional[str] = None):
    return create_chrome_driver(
        "twitter", headless=headless, user_data_dir=user_data_dir
    )

def _build_search_url(
    instance: str,
    query: str,
) -> str:
    base = _normalize_instance_url(instance)
    since = timezone.now().astimezone(datetime_timezone.utc).date().isoformat()
    params = [
        "f=tweets",
        f"q={quote_plus(query)}",
        "e-nativeretweets=on",
        f"since={since}",
        "until=",
        "min_faves=",
    ]
    return f"{base}/search?{'&'.join(params)}"


def _parse_nitter_date(item) -> Optional[datetime]:
    """Parse the canonical UTC timestamp exposed in `.tweet-date a[title]`."""
    try:
        title = item.find_element(By.CSS_SELECTOR, ".tweet-date a").get_attribute("title")
        if not title:
            return None
        normalized = re.sub(r"\s+", " ", title.replace("·", " ").replace("UTC", "")).strip()
        parsed = datetime.strptime(normalized, "%b %d, %Y %I:%M %p")
        return parsed.replace(tzinfo=datetime_timezone.utc)
    except (ValueError, WebDriverException):
        return None


# Retweet detection removed; some instances mislabel items


class TwitterService:
    """Twitter monitoring service using Nitter scraping"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.tweet_cache = {}  # Cache to avoid duplicates
        self.matching_engine = GenericMatchingEngine()
        self._cycle_mentions = 0
        self.check_interval = 120  # Check every 2 minutes
        # Nitter configuration
        self.nitter_driver = None
        self.nitter_instances = list(DEFAULT_NITTER_INSTANCES)
        self.instance_cooldowns: Dict[str, float] = {}
        # Headless default
        self.headless = True
        
    def start_monitoring(self):
        """Initialize monitoring start time"""
        self.last_check_time = timezone.now()
        logger.debug("platform=twitter monitoring initialized")
    
    def start_stream_monitoring(self, keywords: List[Keyword]):
        """Start real-time Twitter monitoring"""
        if self.is_monitoring:
            logger.debug("platform=twitter monitoring already running")
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._run_monitoring_loop,
            args=(keywords,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("platform=twitter monitoring started keywords=%s", len(keywords))
    
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
        logger.info("platform=twitter monitoring stopped")
    
    def _run_monitoring_loop(self, keywords: List[Keyword]):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_for_new_tweets(keywords)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error("platform=twitter monitoring loop failed: %s", e)
                time.sleep(60)  # Wait longer on error
            # small pause between cycles to avoid hammering instances
            time.sleep(1)
    
    def _check_for_new_tweets(self, keywords: List[Keyword]):
        """Check for new tweets matching keywords"""
        try:
            started = time.time()
            self._cycle_mentions = 0
            tweets_seen = 0
            
            for keyword in keywords:
                if not self._should_monitor_keyword(keyword):
                    continue
                
                # Nitter-only search
                logger.debug("platform=twitter searching keyword='%s'", keyword.keyword)
                try:
                    tweets = self._search_tweets_via_nitter(keyword, limit=20)
                except Exception as e:
                    logger.error("platform=twitter search failed keyword='%s': %s", keyword.keyword, e)
                    tweets = []
                
                for tweet in tweets:
                    if self._is_new_tweet(tweet, keyword):
                        tweets_seen += 1
                        self._process_tweet_for_keyword(tweet, keyword)
            
            logger.info(
                "platform=twitter poll completed tweets=%s mentions=%s duration_ms=%.0f",
                tweets_seen, self._cycle_mentions, (time.time() - started) * 1000,
            )
                        
        except Exception as e:
            logger.error("platform=twitter poll failed: %s", e)
    
    # snscrape-based search removed

    def _ensure_nitter_driver(self):
        if self.nitter_driver is None:
            self.nitter_driver = _create_driver(headless=self.headless, user_data_dir=None)

    def _restart_driver(self):
        try:
            if self.nitter_driver:
                try:
                    self.nitter_driver.quit()
                except Exception:
                    pass
            self.nitter_driver = _create_driver(headless=self.headless, user_data_dir=None)
        except Exception as e:
            logger.warning("platform=twitter driver restart failed: %s", e)

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

        wants_replies = ContentType.COMMENTS.value in (keyword.content_types or [])
        wants_posts = ContentType.BODY.value in (keyword.content_types or [])
        cutoff = timezone.now() - timedelta(hours=24)
        timeline_loaded = False
        for inst in self.nitter_instances:
                # skip instances in cooldown for 2 minutes
                now = time.time()
                until_ts = self.instance_cooldowns.get(inst, 0)
                if now < until_ts:
                    continue
                url = _build_search_url(inst, keyword.keyword)
                try:
                    # Preflight: visit instance root to allow cookies/JS to set state
                    base_url = _normalize_instance_url(inst)
                    try:
                        self.nitter_driver.get(base_url)
                        time.sleep(random.uniform(1.0, 2.0))
                    except Exception:
                        pass
                    logger.debug("platform=twitter fetching url=%s", url)
                    self.nitter_driver.get(url)
                    time.sleep(random.uniform(1.0, 2.0))
                    # Detect anti-bot page early
                    page_title = self.nitter_driver.title or ""
                    page_source = self.nitter_driver.page_source or ""
                    if ("Verifying your request" in page_title) or ("/check/" in page_source):
                        logger.warning("platform=twitter anti-bot page on %s; retrying before cooldown", inst)
                        # Retry once after restarting the browser
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
                    timeline_loaded = True
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
                        tweet_date = _parse_nitter_date(el)
                        if tweet_date is None or tweet_date < cutoff:
                            continue
                        is_reply = bool(el.find_elements(By.CSS_SELECTOR, ".replying-to"))
                        if (is_reply and not wants_replies) or (not is_reply and not wants_posts):
                            continue
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
                            'date': tweet_date,
                            'url': twitter_url or nitter_url,
                            'nitter_url': nitter_url,
                            'reply_count': 0,
                            'retweet_count': 0,
                            'like_count': 0,
                            'is_reply': is_reply,
                            'parent_tweet_id': None,
                            'hashtags': [],
                            'mentions': [],
                        })
                    if results:
                        return results[:limit]
                except TimeoutException:
                    logger.warning("platform=twitter instance timed out %s url=%s", inst, url)
                    self._cooldown_instance(inst, minutes=2)
                    self._restart_driver()
                    continue
                except WebDriverException as e:
                    logger.warning("platform=twitter instance webdriver error %s (%s) url=%s", inst, e.__class__.__name__, url)
                    self._cooldown_instance(inst, minutes=2)
                    self._restart_driver()
                    continue
                except Exception as e:
                    logger.warning("platform=twitter instance failed %s (%s) url=%s", inst, e, url)
                    self._cooldown_instance(inst, minutes=1)
                    continue
        # Fallback: if nothing found and cooldowns may have skipped all instances, try a second pass ignoring cooldowns
        if not results and not timeline_loaded and self.nitter_instances:
            for inst in self.nitter_instances:
                url = _build_search_url(inst, keyword.keyword)
                try:
                    self._restart_driver()
                    logger.debug("platform=twitter retrying (ignore cooldown) url=%s", url)
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
                        tweet_date = _parse_nitter_date(el)
                        if tweet_date is None or tweet_date < cutoff:
                            continue
                        is_reply = bool(el.find_elements(By.CSS_SELECTOR, ".replying-to"))
                        if (is_reply and not wants_replies) or (not is_reply and not wants_posts):
                            continue
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
                            'date': tweet_date,
                            'url': twitter_url or nitter_url,
                            'nitter_url': nitter_url,
                            'reply_count': 0,
                            'retweet_count': 0,
                            'like_count': 0,
                            'is_reply': is_reply,
                            'parent_tweet_id': None,
                            'hashtags': [],
                            'mentions': [],
                        })
                    if results:
                        break
                except Exception:
                    continue
        return results[:limit]

    def _retry_instance_once(self, inst: str, url: str) -> bool:
        try:
            self._restart_driver()
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
            content_types_to_check = keyword.content_types or [ContentType.BODY.value]

            if tweet.get('is_reply'):
                if ContentType.COMMENTS.value in content_types_to_check:
                    self._check_tweet_content(tweet, keyword, ContentType.COMMENTS.value)
                return

            if ContentType.BODY.value in content_types_to_check:
                self._check_tweet_content(tweet, keyword, ContentType.BODY.value)
        except Exception as e:
            logger.error("platform=twitter processing id=%s failed: %s", tweet.get('id'), e)
    
    def _check_tweet_content(self, tweet: Dict, keyword: Keyword, content_type: str):
        """Check if tweet content matches keyword"""
        content = tweet.get('content', '')
        
        context = MatchContext(
            author=tweet.get('author', ''),
            source_label=tweet.get('author', ''),
        )
        match_result = self.matching_engine.should_create_mention(
            keyword, content, content_type, context
        )
        
        if match_result:
            # Create mention
            mention = self._create_mention_from_tweet(tweet, keyword, match_result, content_type)
            if mention:
                self._save_mention(mention, keyword, content_type)
    
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
                detected_language=getattr(match_result, 'detected_language', '') or '',
                mention_date=tweet['date'],
                discovered_at=timezone.now()
            )
            
            # Add platform-specific fields
            mention.platform_item_id = tweet['id']
            mention.platform_score = tweet.get('like_count', 0)
            mention.platform_comments_count = tweet.get('reply_count', 0)
            
            return mention
            
        except Exception as e:
            logger.error("platform=twitter mention build failed: %s", e)
            return None
    
    def _save_mention(self, mention: Mention, keyword: Keyword, content_type: str = ""):
        """Save mention and send notification"""
        try:
            mention.save()
            self._cycle_mentions += 1
            logger.info(
                "platform=twitter mention created keyword='%s' type=%s id=%s",
                keyword.keyword, content_type or mention.content_type, mention.id,
            )
            
            # Send email notification
            success = email_notification_service.send_mention_notification(mention)
            if not success:
                logger.error("platform=twitter email failed mention=%s", mention.id)
                
        except Exception as e:
            logger.error("platform=twitter mention save failed: %s", e)
    
    def reset_monitoring(self):
        """Reset monitoring state (useful for testing)"""
        self.last_check_time = None
        self.tweet_cache.clear()
        logger.debug("platform=twitter monitoring reset")

# Global instance
twitter_service = TwitterService() 