#!/usr/bin/env python3
"""
Nitter scraper and monitor using undetected-chromedriver
"""

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


SEEN_FILE = os.path.join(os.path.dirname(__file__), "nitter_seen.json")

DEFAULT_INSTANCES: List[str] = [
    "https://xcancel.com",
    "https://nitter.tiekoetter.com",
    "https://nitter.net"
]


def _load_seen_ids() -> Dict[str, float]:
    if not os.path.exists(SEEN_FILE):
        return {}
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure keys are strings and values are numbers
            return {str(k): float(v) for k, v in data.items()}
    except Exception:
        return {}


def _save_seen_ids(seen_ids: Dict[str, float]) -> None:
    tmp_path = f"{SEEN_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(seen_ids, f, indent=2, sort_keys=True)
    os.replace(tmp_path, SEEN_FILE)


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


def _create_driver(headless: bool) -> uc.Chrome:
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
        # New headless mode for recent Chrome versions
        options.add_argument("--headless=new")

    chrome_version = _get_chrome_version()
    print(f"🔍 Detected Chrome version: {chrome_version}")
    
    try:
        if chrome_version:
            driver = uc.Chrome(options=options, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"⚠️ First attempt failed: {e}")
        print("🔄 Trying with auto-detection...")
        driver = uc.Chrome(options=options, version_main=None)
    
    driver.set_page_load_timeout(30)
    return driver


def _build_search_url(
    instance: str,
    query: str,
    filter_type: str = "tweets",
    since: Optional[str] = None,
    until: Optional[str] = None,
    near: Optional[str] = None,
    exclude_retweets: bool = True,
) -> str:
    base = instance.rstrip("/")
    filter_param = ""
    if filter_type in ("tweets", "replies"):
        filter_param = f"f={filter_type}&"
    params = [
        f"{filter_param}q={quote_plus(query)}",
    ]
    if exclude_retweets:
        params.append("e-nativeretweets=on")
    if since:
        params.append(f"since={quote_plus(since)}")
    if until:
        params.append(f"until={quote_plus(until)}")
    if near:
        params.append(f"near={quote_plus(near)}")
    query_string = "&".join([p for p in params if p])
    return f"{base}/search?{query_string}"


def _extract_tweet_data(tweet_element, index: int, instance: str) -> Dict[str, str]:
    def safe_text(selector: str, default: str = "") -> str:
        try:
            elem = tweet_element.find_element(By.CSS_SELECTOR, selector)
            return elem.text.strip()
        except Exception:
            return default

    text = safe_text(".tweet-content", "")
    username = safe_text(".username", "")
    fullname = safe_text(".fullname", "")
    timestamp = safe_text(".tweet-date a", "")

    nitter_url = ""
    twitter_url = ""
    tweet_id = ""
    try:
        link_elem = tweet_element.find_element(By.CSS_SELECTOR, ".tweet-link")
        href = link_elem.get_attribute("href") or ""
        if href:
            # href looks like: /user/status/1234567890123456789#m
            nitter_url = f"{instance.rstrip('/')}{href}"
            id_match = re.search(r"/status/(\d+)", href)
            tweet_id = id_match.group(1) if id_match else ""
            if tweet_id:
                twitter_url = f"https://x.com/{username.lstrip('@')}/status/{tweet_id}"
    except Exception:
        pass

    return {
        "index": index,
        "id": tweet_id,
        "text": text,
        "username": username,
        "fullname": fullname,
        "timestamp": timestamp,
        "nitter_url": nitter_url,
        "twitter_url": twitter_url,
    }


def _is_retweet(tweet_element) -> bool:
    try:
        # Common Nitter markup for retweets; be permissive
        has_header = bool(tweet_element.find_elements(By.CSS_SELECTOR, ".retweet-header"))
        has_icon = bool(tweet_element.find_elements(By.CSS_SELECTOR, ".icon-retweet"))
        label_nodes = tweet_element.find_elements(By.XPATH, ".//*[contains(translate(text(),'RE','re'),'retweeted')]")
        has_label = bool(label_nodes)
        return has_header or has_icon or has_label
    except Exception:
        return False


def scrape_nitter(
    query: str = "",
    instance: str = "https://nitter.net",
    headless: bool = True,
    filter_type: str = "tweets",
    limit: int = 20,
    driver: Optional[uc.Chrome] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    near: Optional[str] = None,
    exclude_retweets: bool = True,
    suppress_exceptions: bool = True,
) -> List[Dict[str, str]]:
    """
    Scrape results from a Nitter search page.

    Args:
        query: Search query string
        instance: Nitter instance base URL
        headless: Whether to run Chrome headless
        filter_type: 'tweets' | 'replies'
        limit: Maximum number of items to return per page
        driver: Optional shared driver; if None a new one is created and closed
    """

    if not query:
        raise ValueError("query must be provided")

    url = _build_search_url(
        instance,
        query,
        filter_type=filter_type,
        since=since,
        until=until,
        near=near,
        exclude_retweets=exclude_retweets,
    )
    print(f"🌐 Navigating to: {url}")

    local_driver = driver or _create_driver(headless=headless)
    created_local_driver = driver is None

    try:
        local_driver.get(url)
        print("📄 Page loaded, waiting for results...")

        WebDriverWait(local_driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".timeline-item"))
        )
        
        print(f"📄 Page title: {local_driver.title}")
        print(f"🔗 Current URL: {local_driver.current_url}")
        
        items = local_driver.find_elements(By.CSS_SELECTOR, ".timeline-item")
        print(f"🐦 Found {len(items)} items")
        
        if not items:
            return []
        
        results: List[Dict[str, str]] = []
        for i, el in enumerate(items[: max(1, int(limit))], 1):
            try:
                results.append(_extract_tweet_data(el, i, instance))
            except Exception as e:
                print(f"❌ Error processing item {i}: {e}")
                continue
        
        print(f"✅ Extracted {len(results)} items")
        return results
        
    except Exception as e:
        if suppress_exceptions:
            print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return []
        raise
    finally:
        if created_local_driver:
            local_driver.quit()
            print("🧹 Browser closed")


def monitor_nitter(
    keywords: List[str],
    instances: Optional[List[str]] = None,
    headless: bool = True,
    mode: str = "tweets",
    interval_seconds: int = 60,
    limit: int = 30,
    since: Optional[str] = None,
    until: Optional[str] = None,
    near: Optional[str] = None,
    exclude_retweets: bool = True,
) -> None:
    """
    Poll a Nitter instance for new posts matching keywords.
    """
    if not keywords:
        print("⚠️ No keywords provided")
        return

    seen_ids = _load_seen_ids()
    print(f"🗂️ Loaded {len(seen_ids)} previously seen IDs from {SEEN_FILE}")

    # Prepare instance pool
    if not instances:
        instances = DEFAULT_INSTANCES.copy()
    normalized = _unique_preserve_order([_normalize_instance_url(i) for i in instances])
    print(f"🌐 Instances: {normalized}")

    driver = _create_driver(headless=headless)
    try:
        while True:
            cycle_start = datetime.utcnow().isoformat()
            print(f"\n⏱️ Cycle start: {cycle_start} | mode={mode} | keywords={keywords}")

            filter_types: List[str]
            if mode == "all":
                filter_types = ["tweets", "replies"]
            elif mode in ("tweets", "replies"):
                filter_types = [mode]
            else:
                filter_types = ["tweets"]

            new_count = 0
            for keyword in keywords:
                for ftype in filter_types:
                    items: List[Dict[str, str]] = []
                    # Round-robin across instances until success
                    for inst in normalized:
                        try:
                            items = scrape_nitter(
                                query=keyword,
                                instance=inst,
                                headless=headless,
                                filter_type=ftype,
                                limit=limit,
                                driver=driver,
                                since=since,
                                until=until,
                                near=near,
                                exclude_retweets=exclude_retweets,
                                suppress_exceptions=False,
                            )
                            break
                        except Exception as e:
                            print(f"⚠️ Instance failed: {inst} ({e})")
                            continue
                    # Print both URLs for all items found this cycle
                    if items:
                        print(f"\n🔗 URLs ({keyword} / {ftype} @ {inst})")
                        for uitem in items:
                            print(f"    Nitter:  {uitem.get('nitter_url', '')}")
                            print(f"    Twitter: {uitem.get('twitter_url', '')}")
                    for item in items:
                        item_id = item.get("id") or item.get("nitter_url")
                        if not item_id:
                            continue
                        if item_id in seen_ids:
                            continue
                        seen_ids[item_id] = time.time()
                        new_count += 1
                        print(
                            f"🆕 [{ftype}] {item.get('username','')} | {item.get('timestamp','')}\n"
                            f"    {item.get('text','')[:200].replace('\n',' ')}\n"
                            f"    {item.get('twitter_url') or item.get('nitter_url')}"
                        )

            if new_count:
                _save_seen_ids(seen_ids)
                print(f"💾 Saved seen set ({len(seen_ids)} IDs)")
            else:
                print("😴 No new items this cycle")

            print(f"🛌 Sleeping {interval_seconds}s...")
            time.sleep(max(5, int(interval_seconds)))
        
    finally:
        try:
            driver.quit()
            print("🧹 Browser closed")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Monitor Nitter for keywords")
    parser.add_argument(
        "--keyword",
        "-k",
        action="append",
        help="Keyword to search for (can be provided multiple times)",
    )
    parser.add_argument(
        "--keywords",
        help="Comma-separated keywords (alternative to --keyword)",
    )
    parser.add_argument(
        "--instance",
        help="Deprecated: single Nitter instance base URL (use --instances)",
    )
    parser.add_argument(
        "--instances",
        help="Comma-separated list of Nitter instances (falls back to defaults if omitted)",
    )
    parser.add_argument(
        "--mode",
        choices=["tweets", "replies", "all"],
        default="tweets",
        help="Which items to search",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Max items to parse per search page",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scrape for provided keywords and exit",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Chrome with a visible window",
    )
    parser.add_argument("--since", help="Lower bound date (e.g., 2025-08-01)")
    parser.add_argument("--until", help="Upper bound date (e.g., 2025-08-06)")
    parser.add_argument("--near", help="Location string (if the instance supports it)")
    parser.add_argument(
        "--include-retweets",
        action="store_true",
        help="Include retweets (disabled by default)",
    )

    args = parser.parse_args()

    keywords: List[str] = []
    if args.keyword:
        keywords.extend([k for k in args.keyword if k])
    if args.keywords:
        keywords.extend([k.strip() for k in args.keywords.split(",") if k.strip()])
    if not keywords:
        print("❌ You must provide at least one --keyword or --keywords")
        raise SystemExit(2)

    headless = not args.no_headless
    exclude_retweets = not args.include_retweets

    if args.once:
        print("🚀 One-off scrape mode")
        driver = _create_driver(headless=headless)
        # Build instance list for round robin in one-off mode as well
        if args.instances:
            instance_list = [
                _normalize_instance_url(x) for x in args.instances.split(",") if x.strip()
            ]
        elif args.instance:
            instance_list = [_normalize_instance_url(args.instance)]
        else:
            instance_list = DEFAULT_INSTANCES.copy()
        instance_list = _unique_preserve_order(instance_list)
        try:
            for kw in keywords:
                for ftype in ([args.mode] if args.mode != "all" else ["tweets", "replies"]):
                    items: List[Dict[str, str]] = []
                    for inst in instance_list:
                        try:
                            items = scrape_nitter(
                                query=kw,
                                instance=inst,
                                headless=headless,
                                filter_type=ftype,
                                limit=args.limit,
                                driver=driver,
                                since=args.since,
                                until=args.until,
                                near=args.near,
                                exclude_retweets=exclude_retweets,
                                suppress_exceptions=False,
                            )
                            break
                        except Exception as e:
                            print(f"⚠️ Instance failed: {inst} ({e})")
                            continue
                    print(f"\n=== {kw} ({ftype}) → {len(items)} items ===")
                    for item in items:
                        print(
                            f"- {item.get('username','')} | {item.get('timestamp','')} | "
                            f"{(item.get('text','') or '').replace('\n',' ')[:120]}"
                        )
        finally:
            try:
                driver.quit()
                print("🧹 Browser closed")
            except Exception:
                pass
    else:
        print("🚀 Monitoring mode")
        monitor_nitter(
            keywords=keywords,
            instances=_unique_preserve_order(
                [
                    _normalize_instance_url(x)
                    for x in (
                        (args.instances.split(",") if args.instances else [])
                        or ([args.instance] if args.instance else [])
                    )
                    if x
                ]
            ) or DEFAULT_INSTANCES.copy(),
            headless=headless,
            mode=args.mode,
            interval_seconds=args.interval,
            limit=args.limit,
            since=args.since,
            until=args.until,
            near=args.near,
            exclude_retweets=exclude_retweets,
        )


if __name__ == "__main__":
    main()