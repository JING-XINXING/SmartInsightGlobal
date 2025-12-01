"""
地图数据 API 端点
提供新闻地理位置数据，用于全球热点地图可视化
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from pydantic import BaseModel
from app import models
from app.db import session
from app.core.logger import logger

router = APIRouter()


class NewsLocation(BaseModel):
    """新闻位置数据模型"""
    id: int
    title: str
    source: str
    publish_date: str
    sentiment_score: Optional[int] = None
    category: Optional[str] = None
    country: Optional[str] = None
    country_cn: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LocationCluster(BaseModel):
    """位置聚合数据"""
    country: str
    country_cn: str
    lat: float
    lng: float
    count: int
    avg_sentiment: float
    news_ids: List[int]


class MapDataResponse(BaseModel):
    """地图数据响应"""
    locations: List[NewsLocation]
    clusters: List[LocationCluster]
    total_with_location: int
    total_news: int


@router.get("/news-locations", response_model=List[NewsLocation])
async def get_news_with_locations(
    db: AsyncSession = Depends(session.get_db),
    limit: int = Query(100, ge=10, le=500, description="返回数量"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    min_sentiment: Optional[int] = Query(None, ge=-100, le=100, description="最低情感分数"),
    max_sentiment: Optional[int] = Query(None, ge=-100, le=100, description="最高情感分数"),
) -> Any:
    """
    获取带有地理位置的新闻列表
    用于地图上显示新闻热点
    """
    # 构建查询条件
    query = select(models.news.News).where(
        models.news.News.location.isnot(None)
    )
    
    # 添加筛选条件
    if category:
        query = query.where(models.news.News.category == category)
    
    if min_sentiment is not None:
        query = query.where(models.news.News.sentiment_score >= min_sentiment)
    
    if max_sentiment is not None:
        query = query.where(models.news.News.sentiment_score <= max_sentiment)
    
    # 按发布时间倒序
    query = query.order_by(models.news.News.publish_date.desc()).limit(limit)
    
    result = await db.execute(query)
    news_list = result.scalars().all()
    
    # 转换为响应格式
    locations = []
    for news in news_list:
        loc = news.location or {}
        if loc.get("lat") and loc.get("lng"):
            locations.append(NewsLocation(
                id=news.id,
                title=news.title,
                source=news.source,
                publish_date=news.publish_date.isoformat() if news.publish_date else "",
                sentiment_score=news.sentiment_score,
                category=news.category,
                country=loc.get("country"),
                country_cn=loc.get("country_cn"),
                city=loc.get("city"),
                lat=loc.get("lat"),
                lng=loc.get("lng")
            ))
    
    logger.info(f"返回 {len(locations)} 条带位置的新闻")
    return locations


@router.get("/clusters", response_model=List[LocationCluster])
async def get_location_clusters(
    db: AsyncSession = Depends(session.get_db),
    category: Optional[str] = Query(None, description="按分类筛选"),
) -> Any:
    """
    获取按国家/地区聚合的新闻数据
    用于热力图或聚合显示
    """
    # 查询所有带位置的新闻
    query = select(models.news.News).where(
        models.news.News.location.isnot(None)
    )
    
    if category:
        query = query.where(models.news.News.category == category)
    
    result = await db.execute(query)
    news_list = result.scalars().all()
    
    # 按国家聚合
    country_data = {}
    for news in news_list:
        loc = news.location or {}
        country = loc.get("country")
        if not country:
            continue
        
        if country not in country_data:
            country_data[country] = {
                "country": country,
                "country_cn": loc.get("country_cn", country),
                "lat": loc.get("lat", 0),
                "lng": loc.get("lng", 0),
                "count": 0,
                "sentiment_sum": 0,
                "news_ids": []
            }
        
        country_data[country]["count"] += 1
        if news.sentiment_score is not None:
            country_data[country]["sentiment_sum"] += news.sentiment_score
        country_data[country]["news_ids"].append(news.id)
    
    # 转换为响应格式
    clusters = []
    for data in country_data.values():
        avg_sentiment = data["sentiment_sum"] / data["count"] if data["count"] > 0 else 0
        clusters.append(LocationCluster(
            country=data["country"],
            country_cn=data["country_cn"],
            lat=data["lat"],
            lng=data["lng"],
            count=data["count"],
            avg_sentiment=round(avg_sentiment, 1),
            news_ids=data["news_ids"][:20]  # 只返回前20个ID
        ))
    
    # 按数量排序
    clusters.sort(key=lambda x: x.count, reverse=True)
    
    logger.info(f"返回 {len(clusters)} 个国家/地区的聚合数据")
    return clusters


@router.get("/stats", response_model=MapDataResponse)
async def get_map_stats(
    db: AsyncSession = Depends(session.get_db),
) -> Any:
    """
    获取地图统计数据
    """
    # 获取总新闻数
    total_result = await db.execute(
        select(func.count(models.news.News.id))
    )
    total_news = total_result.scalar() or 0
    
    # 获取有位置的新闻数
    with_location_result = await db.execute(
        select(func.count(models.news.News.id)).where(
            models.news.News.location.isnot(None)
        )
    )
    total_with_location = with_location_result.scalar() or 0
    
    # 获取最新的位置数据
    locations_result = await db.execute(
        select(models.news.News)
        .where(models.news.News.location.isnot(None))
        .order_by(models.news.News.publish_date.desc())
        .limit(50)
    )
    news_list = locations_result.scalars().all()
    
    locations = []
    for news in news_list:
        loc = news.location or {}
        if loc.get("lat") and loc.get("lng"):
            locations.append(NewsLocation(
                id=news.id,
                title=news.title,
                source=news.source,
                publish_date=news.publish_date.isoformat() if news.publish_date else "",
                sentiment_score=news.sentiment_score,
                category=news.category,
                country=loc.get("country"),
                country_cn=loc.get("country_cn"),
                city=loc.get("city"),
                lat=loc.get("lat"),
                lng=loc.get("lng")
            ))
    
    # 获取聚合数据
    clusters_query = select(models.news.News).where(
        models.news.News.location.isnot(None)
    )
    clusters_result = await db.execute(clusters_query)
    all_news = clusters_result.scalars().all()
    
    country_data = {}
    for news in all_news:
        loc = news.location or {}
        country = loc.get("country")
        if not country:
            continue
        
        if country not in country_data:
            country_data[country] = {
                "country": country,
                "country_cn": loc.get("country_cn", country),
                "lat": loc.get("lat", 0),
                "lng": loc.get("lng", 0),
                "count": 0,
                "sentiment_sum": 0,
                "news_ids": []
            }
        
        country_data[country]["count"] += 1
        if news.sentiment_score is not None:
            country_data[country]["sentiment_sum"] += news.sentiment_score
        country_data[country]["news_ids"].append(news.id)
    
    clusters = []
    for data in country_data.values():
        avg_sentiment = data["sentiment_sum"] / data["count"] if data["count"] > 0 else 0
        clusters.append(LocationCluster(
            country=data["country"],
            country_cn=data["country_cn"],
            lat=data["lat"],
            lng=data["lng"],
            count=data["count"],
            avg_sentiment=round(avg_sentiment, 1),
            news_ids=data["news_ids"][:20]
        ))
    
    clusters.sort(key=lambda x: x.count, reverse=True)
    
    return MapDataResponse(
        locations=locations,
        clusters=clusters,
        total_with_location=total_with_location,
        total_news=total_news
    )

