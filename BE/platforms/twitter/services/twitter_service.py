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

# Add the BE directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.models import Keyword, Mention
from core.enums import Platform, ContentType
from core.services.matching_engine import GenericMatchingEngine, MatchContext
from core.services.email_service import email_notification_service
from core.services.chrome_driver import create_driver as create_chrome_driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

DEFAULT_NITTER_INSTANCES: List[str] = [
    "https://nitter.net",
    "https://xcancel.com",
    "https://nitter.tiekoetter.com",
]

# Hard floor between any Nitter navigations (including between keywords/instances).
NITTER_MIN_REQUEST_INTERVAL_SECS = 60
CF_CHALLENGE_TIMEOUT_SECS = 45
TIMELINE_READY_TIMEOUT_SECS = 12

_RATE_LIMIT_MARKERS = (
    "rate limit",
    "rate-limited",
    "ratelimited",
    "too many requests",
    "429",
    "instance has been rate limited",
)
_EMPTY_MARKERS = (
    "no items found",
    "no results",
    "nothing to show",
)
_CHALLENGE_MARKERS = (
    "verifying your request",
    "/check/",
    "just a moment",
    "cf-browser-verification",
)


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
    """Build a Nitter search URL. Recency is enforced in-process (24h cutoff)."""
    base = _normalize_instance_url(instance)
    params = [
        "f=tweets",
        f"q={quote_plus(query)}",
        "e-nativeretweets=on",
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


def _page_text_blob(driver) -> str:
    title = (driver.title or "").lower()
    try:
        body = (driver.find_element(By.TAG_NAME, "body").text or "").lower()
    except Exception:
        body = ""
    source = (driver.page_source or "").lower()
    return f"{title}\n{body}\n{source}"


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
        # Cycle sleep is secondary; NITTER_MIN_REQUEST_INTERVAL_SECS paces navigations.
        self.check_interval = 60
        # Nitter configuration
        self.nitter_driver = None
        self.nitter_instances = list(DEFAULT_NITTER_INSTANCES)
        self.instance_cooldowns: Dict[str, float] = {}
        self._last_nitter_request_at = 0.0
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
    
    def _check_for_new_tweets(self, keywords: List[Keyword]):
        """Check for new tweets matching keywords"""
        try:
            started = time.time()
            self._cycle_mentions = 0
            tweets_seen = 0
            
            for keyword in keywords:
                if not self.is_monitoring:
                    break
                if not self._should_monitor_keyword(keyword):
                    continue
                
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

    def _throttle_nitter_request(self) -> None:
        """Ensure at least NITTER_MIN_REQUEST_INTERVAL_SECS between any Nitter navigations."""
        elapsed = time.time() - self._last_nitter_request_at
        remaining = NITTER_MIN_REQUEST_INTERVAL_SECS - elapsed
        if remaining > 0:
            logger.debug("platform=twitter throttling %.0fs before next request", remaining)
            # Sleep in small chunks so stop_stream_monitoring can end promptly.
            deadline = time.time() + remaining
            while self.is_monitoring and time.time() < deadline:
                time.sleep(min(1.0, deadline - time.time()))

    def _nitter_get(self, url: str) -> None:
        """Navigate to a Nitter URL, enforcing the global min request interval."""
        if not self.is_monitoring:
            return
        self._throttle_nitter_request()
        if not self.is_monitoring:
            return
        self._ensure_nitter_driver()
        logger.debug("platform=twitter fetching url=%s", url)
        self.nitter_driver.get(url)
        self._last_nitter_request_at = time.time()

    def _wait_out_challenge(self, timeout: float = CF_CHALLENGE_TIMEOUT_SECS) -> bool:
        """Wait until Cloudflare/Nitter challenge clears. Returns False on timeout."""
        deadline = time.time() + timeout
        challenged = False
        while time.time() < deadline and self.is_monitoring:
            blob = _page_text_blob(self.nitter_driver)
            if any(marker in blob for marker in _CHALLENGE_MARKERS):
                challenged = True
                time.sleep(1.0)
                continue
            if challenged:
                logger.info("platform=twitter challenge cleared")
            return True
        return False

    def _classify_nitter_page(self) -> str:
        """Return one of: timeline | empty | rate_limited | challenge | unknown."""
        blob = _page_text_blob(self.nitter_driver)
        if any(marker in blob for marker in _CHALLENGE_MARKERS):
            return "challenge"
        if any(marker in blob for marker in _RATE_LIMIT_MARKERS):
            return "rate_limited"
        items = self.nitter_driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
        if items:
            return "timeline"
        if any(marker in blob for marker in _EMPTY_MARKERS):
            return "empty"
        # A loaded search page with a timeline container but no items is empty.
        if self.nitter_driver.find_elements(By.CSS_SELECTOR, ".timeline, #timeline, .timeline-container"):
            return "empty"
        return "unknown"

    def _wait_for_search_ready(self, timeout: float = TIMELINE_READY_TIMEOUT_SECS) -> str:
        """Wait briefly for a classifiable search page, then return its status."""
        deadline = time.time() + timeout
        last_status = "unknown"
        while time.time() < deadline and self.is_monitoring:
            last_status = self._classify_nitter_page()
            if last_status != "unknown":
                return last_status
            time.sleep(0.5)
        return last_status

    def _parse_timeline_items(
        self,
        inst: str,
        *,
        wants_replies: bool,
        wants_posts: bool,
        cutoff: datetime,
        limit: int,
    ) -> List[Dict]:
        results: List[Dict] = []
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
        return results

    def _search_tweets_via_nitter(self, keyword: Keyword, limit: int = 20) -> List[Dict]:
        """Search Nitter instances for a keyword. One navigated URL = one throttled request."""
        results: List[Dict] = []
        self._ensure_nitter_driver()

        wants_replies = ContentType.COMMENTS.value in (keyword.content_types or [])
        wants_posts = ContentType.BODY.value in (keyword.content_types or [])
        cutoff = timezone.now() - timedelta(hours=24)

        for inst in self.nitter_instances:
            if not self.is_monitoring:
                break
            normalized = _normalize_instance_url(inst)
            until_ts = self.instance_cooldowns.get(normalized, 0)
            if time.time() < until_ts:
                continue

            url = _build_search_url(inst, keyword.keyword)
            try:
                self._nitter_get(url)
                if not self.is_monitoring:
                    break

                if not self._wait_out_challenge():
                    logger.warning("platform=twitter challenge not cleared on %s", inst)
                    self._cooldown_instance(inst, minutes=10)
                    continue

                status = self._wait_for_search_ready()
                if status == "challenge":
                    logger.warning("platform=twitter still challenged on %s", inst)
                    self._cooldown_instance(inst, minutes=10)
                    continue
                if status == "rate_limited":
                    logger.warning("platform=twitter rate limited on %s", inst)
                    self._cooldown_instance(inst, minutes=15)
                    continue
                if status == "empty":
                    logger.debug("platform=twitter empty results on %s keyword='%s'", inst, keyword.keyword)
                    # Valid empty page — no cooldown, try next instance.
                    continue
                if status == "unknown":
                    logger.warning("platform=twitter unreadable page on %s", inst)
                    self._cooldown_instance(inst, minutes=2)
                    self._restart_driver()
                    continue

                results = self._parse_timeline_items(
                    inst,
                    wants_replies=wants_replies,
                    wants_posts=wants_posts,
                    cutoff=cutoff,
                    limit=limit,
                )
                if results:
                    return results[:limit]
                logger.debug(
                    "platform=twitter timeline loaded but no matching tweets on %s keyword='%s'",
                    inst, keyword.keyword,
                )
            except TimeoutException:
                logger.warning("platform=twitter instance timed out %s url=%s", inst, url)
                self._cooldown_instance(inst, minutes=2)
                self._restart_driver()
                continue
            except WebDriverException as e:
                logger.warning(
                    "platform=twitter instance webdriver error %s (%s) url=%s",
                    inst, e.__class__.__name__, url,
                )
                self._cooldown_instance(inst, minutes=2)
                self._restart_driver()
                continue
            except Exception as e:
                logger.warning("platform=twitter instance failed %s (%s) url=%s", inst, e, url)
                self._cooldown_instance(inst, minutes=1)
                continue

        return results[:limit]
    
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