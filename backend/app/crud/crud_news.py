from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.news import News
from app.schemas.news import NewsCreate

async def get_news_by_url(db: AsyncSession, url: str):
    result = await db.execute(select(News).filter(News.url == url))
    return result.scalars().first()

async def create_news(db: AsyncSession, news_in: NewsCreate):
    db_obj = News(
        title=news_in.title,
        content=news_in.content,
        source=news_in.source,
        url=news_in.url,
        publish_date=news_in.publish_date,
        summary=news_in.summary if hasattr(news_in, 'summary') else None
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def create_news_if_not_exists(db: AsyncSession, news_in: NewsCreate):
    existing = await get_news_by_url(db, news_in.url)
    if existing:
        return existing
    return await create_news(db, news_in)

async def get_multi_news(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(News).order_by(News.publish_date.desc()).offset(skip).limit(limit))
    return result.scalars().all()
