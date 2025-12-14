"""
地图数据 API 端点 - 简化版本
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
    sentiment_score: Optional[float] = None
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
    news_ids: List[int] = []


class MapDataResponse(BaseModel):
    """地图数据响应"""
    locations: List[NewsLocation]
    clusters: List[LocationCluster]
    total_with_location: int
    total_news: int


@router.get("/news-locations", response_model=List[NewsLocation])
async def get_news_with_locations(
    db: AsyncSession = Depends(session.get_db),
    limit: int = Query(100, ge=10, le=500),
    category: Optional[str] = Query(None)
):
    """
    获取带有地理位置的新闻列表
    """
    try:
        # 构建查询条件
        query = select(models.news.News).where(
            models.news.News.location.isnot(None)
        )

        # 添加筛选条件
        if category:
            query = query.where(models.news.News.category == category)

        # 按发布时间倒序
        query = query.order_by(models.news.News.publish_date.desc()).limit(limit)

        result = await db.execute(query)
        news_list = result.scalars().all()

        # 转换为响应格式
        locations = []
        for news in news_list:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")
            
            # 确保坐标有效
            if not lat or not lng:
                continue
            # 处理坐标可能是list的情况
            if isinstance(lat, list):
                lat = lat[0] if lat else None
            if isinstance(lng, list):
                lng = lng[0] if lng else None
            if not lat or not lng:
                continue
                
            # 获取其他字段，处理可能是list的情况
            country = loc.get("country")
            if isinstance(country, list):
                country = country[0] if country else None
            city = loc.get("city")
            if isinstance(city, list):
                city = city[0] if city else None
                
            locations.append(NewsLocation(
                id=news.id,
                title=news.title,
                source=news.source,
                publish_date=news.publish_date.isoformat() if news.publish_date else "",
                sentiment_score=news.sentiment_score,
                category=news.category,
                country=country,
                city=city,
                lat=float(lat) if lat else None,
                lng=float(lng) if lng else None
            ))

        logger.info(f"返回 {len(locations)} 条带位置的新闻")
        return locations

    except Exception as e:
        logger.error(f"Failed to get news locations: {e}")
        return []


@router.get("/clusters", response_model=List[LocationCluster])
async def get_location_clusters(
    db: AsyncSession = Depends(session.get_db),
    category: Optional[str] = Query(None)
):
    """
    获取按国家/地区聚合的新闻数据
    """
    try:
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
            
            # 跳过无效的country值
            if not country:
                continue
            # 如果country是list，取第一个元素
            if isinstance(country, list):
                country = country[0] if country else None
                if not country:
                    continue
            # 确保country是字符串
            if not isinstance(country, str):
                country = str(country)
            
            # 处理坐标
            lat = loc.get("lat", 0)
            lng = loc.get("lng", 0)
            if isinstance(lat, list):
                lat = lat[0] if lat else 0
            if isinstance(lng, list):
                lng = lng[0] if lng else 0

            if country not in country_data:
                country_data[country] = {
                    "country": country,
                    "lat": float(lat) if lat else 0,
                    "lng": float(lng) if lng else 0,
                    "count": 0,
                    "sentiment_sum": 0
                }

            country_data[country]["count"] += 1
            if news.sentiment_score is not None:
                score = news.sentiment_score
                if isinstance(score, list):
                    score = score[0] if score else 0
                country_data[country]["sentiment_sum"] += float(score) if score else 0

        # 转换为响应格式
        clusters = []
        for data in country_data.values():
            avg_sentiment = data["sentiment_sum"] / data["count"] if data["count"] > 0 else 0
            clusters.append(LocationCluster(
                country=data["country"],
                lat=data["lat"],
                lng=data["lng"],
                count=data["count"],
                avg_sentiment=round(avg_sentiment, 1)
            ))

        # 按数量排序
        clusters.sort(key=lambda x: x.count, reverse=True)

        logger.info(f"返回 {len(clusters)} 个国家/地区的聚合数据")
        return clusters

    except Exception as e:
        logger.error(f"Failed to get location clusters: {e}")
        return []


@router.get("/stats", response_model=MapDataResponse)
async def get_map_stats(
    db: AsyncSession = Depends(session.get_db),
    category: Optional[str] = Query(None)
):
    """
    获取地图统计数据和位置数据
    """
    try:
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
        query = select(models.news.News).where(
            models.news.News.location.isnot(None)
        )

        if category:
            query = query.where(models.news.News.category == category)

        locations_result = await db.execute(
            query.order_by(models.news.News.publish_date.desc()).limit(100)
        )
        news_list = locations_result.scalars().all()

        locations = []
        for news in news_list:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")
            
            # 确保坐标有效
            if not lat or not lng:
                continue
            # 处理坐标可能是list的情况
            if isinstance(lat, list):
                lat = lat[0] if lat else None
            if isinstance(lng, list):
                lng = lng[0] if lng else None
            if not lat or not lng:
                continue
                
            # 获取country，处理可能是list的情况
            country = loc.get("country")
            if isinstance(country, list):
                country = country[0] if country else None
            country_cn = loc.get("country_cn")
            if isinstance(country_cn, list):
                country_cn = country_cn[0] if country_cn else None
            city = loc.get("city")
            if isinstance(city, list):
                city = city[0] if city else None
                
            locations.append(NewsLocation(
                id=news.id,
                title=news.title,
                source=news.source,
                publish_date=news.publish_date.isoformat() if news.publish_date else "",
                sentiment_score=news.sentiment_score,
                category=news.category,
                country=country,
                country_cn=country_cn,
                city=city,
                lat=float(lat) if lat else None,
                lng=float(lng) if lng else None
            ))

        # 获取聚合数据
        clusters_query = select(models.news.News).where(
            models.news.News.location.isnot(None)
        )

        if category:
            clusters_query = clusters_query.where(models.news.News.category == category)

        clusters_result = await db.execute(clusters_query)
        all_news = clusters_result.scalars().all()

        country_data = {}
        for news in all_news:
            loc = news.location or {}
            country = loc.get("country")
            
            # 跳过无效的country值（None、空字符串、或非字符串类型）
            if not country:
                continue
            # 如果country是list，取第一个元素
            if isinstance(country, list):
                country = country[0] if country else None
                if not country:
                    continue
            # 确保country是字符串
            if not isinstance(country, str):
                country = str(country)

            if country not in country_data:
                # 处理country_cn
                country_cn = loc.get("country_cn", country)
                if isinstance(country_cn, list):
                    country_cn = country_cn[0] if country_cn else country
                    
                # 处理lat和lng
                lat = loc.get("lat", 0)
                lng = loc.get("lng", 0)
                if isinstance(lat, list):
                    lat = lat[0] if lat else 0
                if isinstance(lng, list):
                    lng = lng[0] if lng else 0
                    
                country_data[country] = {
                    "country": country,
                    "country_cn": country_cn,
                    "lat": float(lat) if lat else 0,
                    "lng": float(lng) if lng else 0,
                    "count": 0,
                    "sentiment_sum": 0,
                    "news_ids": []
                }

            country_data[country]["count"] += 1
            if news.sentiment_score is not None:
                score = news.sentiment_score
                if isinstance(score, list):
                    score = score[0] if score else 0
                country_data[country]["sentiment_sum"] += float(score) if score else 0
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

    except Exception as e:
        import traceback
        logger.error(f"Failed to get map stats: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return MapDataResponse(
            locations=[],
            clusters=[],
            total_with_location=0,
            total_news=0
        )