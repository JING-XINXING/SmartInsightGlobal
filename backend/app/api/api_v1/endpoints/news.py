from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import schemas, models
from app.db import session

router = APIRouter()

@router.get("/", response_model=List[schemas.news.News])
async def read_news(
    db: AsyncSession = Depends(session.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve news.
    """
    result = await db.execute(select(models.news.News).order_by(models.news.News.publish_date.desc()).offset(skip).limit(limit))
    news = result.scalars().all()
    return news

@router.post("/", response_model=schemas.news.News)
async def create_news(
    *,
    db: AsyncSession = Depends(session.get_db),
    news_in: schemas.news.NewsCreate,
) -> Any:
    """
    Create new news.
    """
    news = models.news.News(**news_in.dict())
    db.add(news)
    await db.commit()
    await db.refresh(news)
    return news
