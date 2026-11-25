"""
测试配置和共享 fixtures
"""
import os

# 必须在导入应用之前关闭限流，避免用例被 120 次/分钟的默认阈值打断。
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.base import Base
from app.core.config import settings

# 测试数据库 URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_smartinsight"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    # 没有数据库时跳过，避免整组用例变成 ERROR
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except OSError:
        await engine.dispose()
        pytest.skip("PostgreSQL 未启动，跳过依赖数据库的测试")

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端。httpx 0.28 起需要显式 ASGITransport。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm_response():
    """模拟 LLM 响应"""
    return {
        "sentiment_score": 50,
        "keywords": ["test", "keyword", "example"],
        "category": "Technology",
        "location": {
            "country": "United States",
            "city": "New York"
        }
    }


@pytest.fixture
def sample_news_data():
    """示例新闻数据"""
    return {
        "title": "Test News Article",
        "content": "This is a test news article content for testing purposes.",
        "summary": "Test summary",
        "source": "Test Source",
        "url": "https://example.com/test-news",
        "publish_date": "2025-12-02T10:00:00Z"
    }


@pytest.fixture
def sample_rss_feed():
    """示例 RSS Feed 数据"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test RSS Feed</title>
            <link>https://example.com</link>
            <description>Test RSS Feed Description</description>
            <item>
                <title>Test Article 1</title>
                <link>https://example.com/article1</link>
                <description>Test article 1 description</description>
                <pubDate>Mon, 02 Dec 2025 10:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Test Article 2</title>
                <link>https://example.com/article2</link>
                <description>Test article 2 description</description>
                <pubDate>Mon, 02 Dec 2025 11:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>"""


@pytest_asyncio.fixture(scope="function")
async def sample_news(db_session):
    """创建示例新闻数据用于测试"""
    from app.models.news import News
    from datetime import datetime
    from sqlalchemy import select

    # 清理现有数据
    await db_session.execute(select(News).where(News.url.like("%example.com%")))
    await db_session.commit()

    # 创建测试数据
    sample_data = [
        News(
            title="Test News Article 1",
            content="This is a test news article about technology.",
            summary="Test summary for tech article",
            source="Test News",
            url="https://example.com/tech-news-1",
            publish_date=datetime(2025, 12, 2, 10, 0, 0),
            category="科技",
            sentiment_score=75,
            keywords=["technology", "innovation"],
            location_data={"country": "United States", "city": "San Francisco"}
        ),
        News(
            title="Test News Article 2",
            content="This is a test news article about business.",
            summary="Test summary for business article",
            source="Test News",
            url="https://example.com/business-news-1",
            publish_date=datetime(2025, 12, 2, 11, 0, 0),
            category="商业",
            sentiment_score=25,
            keywords=["business", "economy"],
            location_data={"country": "United States", "city": "New York"}
        ),
        News(
            title="Test News Article 3",
            content="This is another test news article about technology.",
            summary="Test summary for another tech article",
            source="Test News",
            url="https://example.com/tech-news-2",
            publish_date=datetime(2025, 12, 2, 12, 0, 0),
            category="科技",
            sentiment_score=50,
            keywords=["technology", "AI"],
            location_data={"country": "China", "city": "Beijing"}
        )
    ]

    # 添加到数据库
    for news in sample_data:
        db_session.add(news)

    await db_session.commit()

    return sample_data