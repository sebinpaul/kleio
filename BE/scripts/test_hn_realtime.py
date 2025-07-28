import asyncio
import aiohttp
import html

BASE_URL = "https://hacker-news.firebaseio.com/v0"
POLL_INTERVAL = 2  # seconds

async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_item(session, item_id):
    return await fetch_json(session, f"{BASE_URL}/item/{item_id}.json")

async def stream_items():
    async with aiohttp.ClientSession() as session:
        prev_max_id = await fetch_json(session, f"{BASE_URL}/maxitem.json")

        while True:
            await asyncio.sleep(POLL_INTERVAL)
            curr_max_id = await fetch_json(session, f"{BASE_URL}/maxitem.json")

            for item_id in range(prev_max_id + 1, curr_max_id + 1):
                item = await fetch_item(session, item_id)

                if not item:
                    continue

                item_type = item.get("type")

                if item_type == "story":
                    title = html.unescape(item.get("title", ""))
                    url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
                    print(f"\n📘 [STORY] by {item.get('by')} — {title}")
                    print(f"🔗 {url}")

                elif item_type == "comment":
                    text = html.unescape(item.get("text", ""))
                    parent = item.get("parent")
                    print(f"\n💬 [COMMENT] by {item.get('by')} (on item {parent})")
                    print(f"🗣️ {text}")

            prev_max_id = curr_max_id

if __name__ == "__main__":
    asyncio.run(stream_items())
