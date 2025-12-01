"""
SmartInsight Global Backend Tests
测试模块初始化文件
"""

import asyncio
import pytest
import asyncio_test_utils
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from app.main import app
from app.core.config import settings
from app.db.session import get_db
from app.models.news import News, Source
from app.db.base_class import Base

# 测试数据库配置
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_smartinsight"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, Any]:
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, Any]:
    """创建测试客户端"""
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def sample_news(db_session: AsyncSession):
    """创建示例新闻数据"""
    news_data = [
        News(
            title="全球经济增长超预期",
            content="最新经济数据显示，全球主要经济体在第三季度表现强劲...",
            summary="经济复苏加速",
            source="Test News",
            url="http://example.com/news1",
            sentiment_score=75,
            keywords=["经济", "增长", "GDP"],
            category="经济"
        ),
        News(
            title="自然灾害造成严重损失",
            content="地震导致数百人遇难，经济损失严重...",
            summary="灾害损失重大",
            source="Test News",
            url="http://example.com/news2",
            sentiment_score=-80,
            keywords=["灾害", "地震", "损失"],
            category="灾难"
        ),
        News(
            title="AI技术取得重大突破",
            content="人工智能在医疗领域取得重大进展...",
            summary="AI医疗突破",
            source="Test News",
            url="http://example.com/news3",
            sentiment_score=60,
            keywords=["AI", "技术", "医疗"],
            category="科技"
        )
    ]

    for news in news_data:
        db_session.add(news)

    await db_session.commit()

    # 返回所有创建的新闻
    result = await db_session.execute(
        select(News).where(News.source == "Test News")
    )
    return result.scalars().all()

@pytest.fixture
async def sample_source(db_session: AsyncSession):
    """创建示例新闻源数据"""
    source = Source(
        name="Test RSS Feed",
        url="http://example.com/rss.xml",
        type="rss",
        is_active=True
    )

    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    return source