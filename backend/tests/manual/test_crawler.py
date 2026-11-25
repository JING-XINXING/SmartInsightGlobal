import asyncio
from app.core.crawler import crawler

async def main():
    # Test with a known RSS feed
    url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    entries = await crawler.fetch_feed(url)
    
    print(f"Fetched {len(entries)} entries.")
    if entries:
        print("First entry:")
        print(entries[0])

if __name__ == "__main__":
    asyncio.run(main())
