import asyncio
from app.worker import analyze_unanalyzed_news_async

if __name__ == "__main__":
    print("Starting manual AI analysis...")
    result = asyncio.run(analyze_unanalyzed_news_async())
    print(f"Analysis completed: {result}")
