import asyncio
import asyncpg

async def create_db():
    try:
        conn = await asyncpg.connect(user='postgres', database='postgres', host='localhost')
        await conn.execute('CREATE DATABASE smartinsight')
        print("Database 'smartinsight' created successfully!")
        await conn.close()
    except Exception as e:
        print(f"Failed to create database: {e}")

if __name__ == "__main__":
    asyncio.run(create_db())
