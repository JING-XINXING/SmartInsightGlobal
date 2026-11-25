import asyncio
from app.worker import fetch_and_save_feeds_async

if __name__ == "__main__":
    asyncio.run(fetch_and_save_feeds_async())
    print("Done fetching and saving feeds.")
