import feedparser
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import time
from email.utils import parsedate_to_datetime
from app.core.logger import logger

class RSSCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": "SmartInsightGlobal/1.0"
        }

    async def fetch_feed(self, url: str) -> List[Dict]:
        """
        Fetch and parse RSS feed asynchronously.
        Uses httpx for async fetching and feedparser for parsing.
        """
        logger.info(f"Fetching RSS feed: {url}")
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
                content = response.text
                logger.info(f"Successfully fetched {len(content)} bytes from {url}")
            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching {url}: {e}")
                return []
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} fetching {url}: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
                return []

        # Parse content
        try:
            feed = feedparser.parse(content)
            entries = []
            
            source_name = feed.feed.get("title", "Unknown Source")
            logger.info(f"Parsing feed from source: {source_name}")

            for entry in feed.entries:
                try:
                    # Extract fields
                    # Handle date parsing
                    published = entry.get("published") or entry.get("updated")
                    dt = datetime.now()
                    if published:
                        try:
                            # Try standard parsing
                            if entry.get("published_parsed"):
                                dt = datetime.fromtimestamp(time.mktime(entry.get("published_parsed")))
                            else:
                                # Fallback
                                dt = parsedate_to_datetime(published)
                                # Remove timezone info for simplicity if needed, or keep it. 
                                # Postgres supports timezone.
                        except Exception as e:
                            logger.warning(f"Failed to parse date '{published}' for entry: {e}")

                    content_val = ""
                    if "content" in entry:
                        content_val = entry.content[0].value
                    elif "summary" in entry:
                        content_val = entry.summary

                    entries.append({
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "summary": entry.get("summary", ""),
                        "content": content_val,
                        "publish_date": dt,
                        "source": source_name
                    })
                except Exception as e:
                    logger.error(f"Error parsing entry from {url}: {e}", exc_info=True)
                    continue
            
            logger.info(f"Successfully parsed {len(entries)} entries from {url}")
            return entries
        except Exception as e:
            logger.error(f"Error parsing feed from {url}: {e}", exc_info=True)
            return []

crawler = RSSCrawler()
