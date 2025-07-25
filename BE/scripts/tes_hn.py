import time
import requests
from datetime import datetime
from urllib.parse import quote

# Configuration
keyword = "openai"  # your keyword
start_time = int(time.time())  # timestamp after which to search
check_interval = 10  # how often to check (in seconds)
include_comments = True  # set to False to exclude comments

def fetch_hn_updates(keyword, start_time, include_comments=True):
    keyword_encoded = quote(keyword)
    tags = "story"
    if include_comments:
        tags = "(story,comment)"

    url = (
        f"https://hn.algolia.com/api/v1/search_by_date"
        f"?query={keyword_encoded}&tags={tags}&numericFilters=created_at_i>{start_time}"
    )
    
    print(f"\n[URL] {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data.get("hits", []):
            title = item.get("title") or item.get("story_title")
            comment = item.get("comment_text")
            object_url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"
            created = datetime.utcfromtimestamp(item["created_at_i"]).strftime('%Y-%m-%d %H:%M:%S')

            print(f"\n[{created}] {title or 'Comment'}")
            if comment:
                print(f"Comment: {comment}")
            print(f"URL: {object_url}")
    except Exception as e:
        print(f"Error fetching from API: {e}")

# Run monitoring loop
print(f"Monitoring Hacker News for keyword: '{keyword}' since {datetime.utcfromtimestamp(start_time)}")
while True:
    fetch_hn_updates(keyword, start_time, include_comments)
    time.sleep(check_interval)
