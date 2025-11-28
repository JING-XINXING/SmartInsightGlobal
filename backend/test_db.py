import asyncio
import asyncpg

async def main():
    try:
        # Try connecting to default 'postgres' database
        conn = await asyncpg.connect(user='xinxingjing', database='postgres', host='localhost')
        print("Connected to 'postgres' database successfully!")
        await conn.close()
    except Exception as e:
        print(f"Failed to connect to 'postgres': {e}")

    try:
        # Try connecting to 'smartinsight' database
        conn = await asyncpg.connect(user='xinxingjing', database='smartinsight', host='localhost')
        print("Connected to 'smartinsight' database successfully!")
        await conn.close()
    except Exception as e:
        print(f"Failed to connect to 'smartinsight': {e}")

if __name__ == "__main__":
    asyncio.run(main())
