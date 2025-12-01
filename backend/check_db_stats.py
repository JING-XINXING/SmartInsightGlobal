import asyncio
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check_stats():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT count(*) as total, count(sentiment_score) as analyzed FROM news"))
        row = result.fetchone()
        print(f"Total News: {row[0]}")
        print(f"Analyzed News: {row[1]}")
        
        if row[1] == 0:
            print("No news analyzed. Checking for unanalyzed news...")
            result = await db.execute(text("SELECT id, title FROM news WHERE sentiment_score IS NULL LIMIT 5"))
            rows = result.fetchall()
            for r in rows:
                print(f"Unanalyzed: {r[0]} - {r[1]}")

if __name__ == "__main__":
    asyncio.run(check_stats())
