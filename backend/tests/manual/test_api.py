import httpx
import asyncio
import json

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        health = await client.get("http://localhost:8001/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        
        # Test news endpoint
        news = await client.get("http://localhost:8001/api/v1/news?limit=3")
        print("\nNews API status:", news.status_code)
        if news.status_code == 200:
            data = news.json()
            print(f"Fetched {len(data)} news articles")
            if data:
                print("\nFirst article:")
                print(json.dumps(data[0], indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_api())
