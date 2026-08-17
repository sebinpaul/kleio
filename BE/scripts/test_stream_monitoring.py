#!/usr/bin/env python
"""Stream r/all submissions + comments and match keyword djangoSeb."""
import os
import sys
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import django

django.setup()

from platforms.reddit.services.reddit_service import RedditService

KEYWORD = "djangoSeb"
DURATION_SECS = 120


def main():
    reddit = RedditService().get_reddit_instance()
    needle = KEYWORD.lower()
    stop_at = time.time() + DURATION_SECS
    lock = threading.Lock()
    counts = {"submissions": 0, "comments": 0, "hits": 0}

    print(f"Streaming r/all submissions + comments for {DURATION_SECS}s")
    print(f"Matching keyword: '{KEYWORD}' (title, body, comments)")
    print("-" * 60)

    def watch_submissions():
        try:
            for submission in reddit.subreddit("all").stream.submissions(skip_existing=True):
                if time.time() >= stop_at:
                    break
                title = submission.title or ""
                body = submission.selftext or ""
                text = f"{title}\n{body}"
                with lock:
                    counts["submissions"] += 1
                    n = counts["submissions"]
                if needle in text.lower():
                    with lock:
                        counts["hits"] += 1
                    print(f"🎯 HIT submission [{n}] r/{submission.subreddit.display_name}: {title[:100]}")
                    print(f"   https://reddit.com{submission.permalink}")
                    print(flush=True)
                else:
                    print(f"[sub {n}] r/{submission.subreddit.display_name}: {title[:80]}", flush=True)
        except Exception as e:
            print(f"❌ submissions stream error: {e}", flush=True)

    def watch_comments():
        try:
            for comment in reddit.subreddit("all").stream.comments(skip_existing=True):
                if time.time() >= stop_at:
                    break
                body = comment.body or ""
                with lock:
                    counts["comments"] += 1
                    n = counts["comments"]
                if needle in body.lower():
                    with lock:
                        counts["hits"] += 1
                    preview = body[:100].replace("\n", " ")
                    print(f"🎯 HIT comment [{n}] r/{comment.subreddit.display_name}: {preview}")
                    print(f"   https://reddit.com{comment.permalink}")
                    print(flush=True)
                else:
                    preview = body[:80].replace("\n", " ")
                    print(f"[cmt {n}] r/{comment.subreddit.display_name}: {preview}", flush=True)
        except Exception as e:
            print(f"❌ comments stream error: {e}", flush=True)

    threads = [
        threading.Thread(target=watch_submissions, daemon=True),
        threading.Thread(target=watch_comments, daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=DURATION_SECS + 30)

    print("-" * 60)
    print(
        f"Done. Submissions: {counts['submissions']} | "
        f"Comments: {counts['comments']} | "
        f"'{KEYWORD}' hits: {counts['hits']}"
    )


if __name__ == "__main__":
    main()
