"""
地图数据 API 端点
提供新闻地理位置数据，用于全球热点地图可视化
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from pydantic import BaseModel, Field
from app import models
from app.db import session
from app.core.logger import logger
from app.core.geo_heatmap import advanced_geo_heatmap_analyzer, TimeRange
from app.models.user import User

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


class HeatmapRequest(BaseModel):
    """热力图请求模型"""
    bbox: Optional[List[float]] = Field(None, description="边界框 [min_lat, min_lng, max_lat, max_lng]")
    time_range: str = Field("day", regex="^(hour|day|week|month)$", description="时间范围")
    grid_type: str = Field("global", regex="^(global|regional|city)$", description="网格类型")
    sentiment_filter: Optional[List[int]] = Field(None, description="情感分数范围 [min, max]")


class GeographicAnalysisRequest(BaseModel):
    """地理分析请求模型"""
    region: Optional[str] = Field(None, description="特定地区筛选")
    time_range: str = Field("week", regex="^(hour|day|week|month)$", description="时间范围")


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


@router.post("/heatmap/advanced")
async def generate_advanced_heatmap(
    request: HeatmapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db)
):
    """
    生成高级实时热力图

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        # 转换参数
        bbox = tuple(request.bbox) if request.bbox else None
        time_range = TimeRange(request.time_range)
        sentiment_filter = tuple(request.sentiment_filter) if request.sentiment_filter else None

        # 生成热力图
        heatmap_data = await advanced_geo_heatmap_analyzer.generate_realtime_heatmap(
            db=db,
            bbox=bbox,
            time_range=time_range,
            grid_type=request.grid_type,
            sentiment_filter=sentiment_filter
        )

        logger.info(f"Generated advanced heatmap for user {current_user.id}")
        return heatmap_data

    except Exception as e:
        logger.error(f"Failed to generate advanced heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")


@router.get("/heatmap/realtime")
async def get_realtime_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db),
    bbox: Optional[str] = Query(None, description="边界框，格式：min_lat,min_lng,max_lat,max_lng"),
    time_range: str = Query("day", regex="^(hour|day|week|month)$", description="时间范围"),
    grid_type: str = Query("global", regex="^(global|regional|city)$", description="网格类型")
):
    """
    获取实时热力图（GET方式）

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        # 解析边界框
        bbox = None
        if bbox:
            try:
                bbox_parts = [float(x) for x in bbox.split(',')]
                if len(bbox_parts) == 4:
                    bbox = tuple(bbox_parts)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid bbox format")

        time_range_enum = TimeRange(time_range)

        # 生成热力图
        heatmap_data = await advanced_geo_heatmap_analyzer.generate_realtime_heatmap(
            db=db,
            bbox=bbox,
            time_range=time_range_enum,
            grid_type=grid_type
        )

        logger.info(f"Generated realtime heatmap for user {current_user.id}")
        return heatmap_data

    except Exception as e:
        logger.error(f"Failed to generate realtime heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")


@router.post("/analysis/geographic")
async def analyze_geographic_patterns(
    request: GeographicAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db)
):
    """
    分析地理模式

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        time_range = TimeRange(request.time_range)

        # 执行地理模式分析
        patterns_data = await advanced_geo_heatmap_analyzer.analyze_geographic_patterns(
            db=db,
            region=request.region,
            time_range=time_range
        )

        logger.info(f"Analyzed geographic patterns for region '{request.region}'")
        return patterns_data

    except Exception as e:
        logger.error(f"Failed to analyze geographic patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")


@router.get("/hotspots")
async def get_current_hotspots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db),
    limit: int = Query(20, ge=5, le=100, description="热点数量限制"),
    min_intensity: float = Query(0.1, ge=0.0, le=1.0, description="最小强度阈值"),
    time_range: str = Query("day", regex="^(hour|day|week|month)$", description="时间范围")
):
    """
    获取当前热点区域

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        time_range_enum = TimeRange(time_range)

        # 生成热力图以获取热点
        heatmap_data = await advanced_geo_heatmap_analyzer.generate_realtime_heatmap(
            db=db,
            time_range=time_range_enum,
            grid_type="regional"
        )

        # 过滤热点
        hotspots = [
            spot for spot in heatmap_data.get("hotspots", [])
            if spot.get("intensity", 0) >= min_intensity
        ][:limit]

        return {
            "hotspots": hotspots,
            "metadata": heatmap_data.get("metadata", {}),
            "total_found": len(hotspots)
        }

    except Exception as e:
        logger.error(f"Failed to get hotspots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotspots: {str(e)}")


@router.get("/regions/sentiment")
async def get_regional_sentiment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db),
    time_range: str = Query("week", regex="^(hour|day|week|month)$", description="时间范围")
):
    """
    获取各地区情感分布

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        time_range_enum = TimeRange(time_range)

        # 分析地理模式以获取情感数据
        patterns_data = await advanced_geo_heatmap_analyzer.analyze_geographic_patterns(
            db=db,
            time_range=time_range_enum
        )

        sentiment_patterns = patterns_data.get("patterns", {}).get("sentiment_patterns", {})

        # 格式化响应
        regional_sentiments = []
        for region, avg_sentiment in sentiment_patterns.get("regional_sentiments", {}).items():
            regional_sentiments.append({
                "region": region,
                "avg_sentiment": round(avg_sentiment, 2),
                "sentiment_label": "positive" if avg_sentiment > 10 else "negative" if avg_sentiment < -10 else "neutral"
            })

        # 按情感分数排序
        regional_sentiments.sort(key=lambda x: x["avg_sentiment"], reverse=True)

        return {
            "regional_sentiments": regional_sentiments,
            "most_positive": sentiment_patterns.get("most_positive_region"),
            "most_negative": sentiment_patterns.get("most_negative_region"),
            "time_range": time_range,
            "total_regions": len(regional_sentiments)
        }

    except Exception as e:
        logger.error(f"Failed to get regional sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get regional sentiment: {str(e)}")


@router.get("/clustering/events")
async def get_event_clustering(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db),
    min_cluster_size: int = Query(3, ge=2, le=20, description="最小聚类大小"),
    time_range: str = Query("day", regex="^(hour|day|week|month)$", description="时间范围")
):
    """
    获取事件聚类分析

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        time_range_enum = TimeRange(time_range)

        # 分析地理模式以获取聚类信息
        patterns_data = await advanced_geo_heatmap_analyzer.analyze_geographic_patterns(
            db=db,
            time_range=time_range_enum
        )

        cluster_patterns = patterns_data.get("patterns", {}).get("geographic_clusters", {})
        correlation_patterns = patterns_data.get("patterns", {}).get("event_correlations", {})

        # 过滤小型聚类
        clusters = [
            cluster for cluster in cluster_patterns.get("clusters", [])
            if cluster.get("news_count", 0) >= min_cluster_size
        ]

        return {
            "clusters": clusters,
            "cluster_count": len(clusters),
            "correlations": correlation_patterns.get("top_correlations", []),
            "correlations_count": correlation_patterns.get("correlations_count", 0),
            "time_range": time_range,
            "min_cluster_size": min_cluster_size
        }

    except Exception as e:
        logger.error(f"Failed to get event clustering: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get event clustering: {str(e)}")


@router.get("/statistics/advanced")
async def get_advanced_map_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(session.get_db),
    time_range: str = Query("week", regex="^(hour|day|week|month)$", description="时间范围")
):
    """
    获取高级地图统计数据

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        time_range_enum = TimeRange(time_range)

        # 生成热力图以获取统计数据
        heatmap_data = await advanced_geo_heatmap_analyzer.generate_realtime_heatmap(
            db=db,
            time_range=time_range_enum,
            grid_type="global"
        )

        # 分析地理模式
        patterns_data = await advanced_geo_heatmap_analyzer.analyze_geographic_patterns(
            db=db,
            time_range=time_range_enum
        )

        statistics = heatmap_data.get("statistics", {})
        temporal_patterns = patterns_data.get("patterns", {}).get("temporal_patterns", {})

        return {
            "basic_statistics": statistics,
            "temporal_patterns": temporal_patterns,
            "heatmap_metadata": heatmap_data.get("metadata", {}),
            "time_series": heatmap_data.get("time_series", [])[-24:],  # 最近24个数据点
            "analysis_time_range": time_range
        }

    except Exception as e:
        logger.error(f"Failed to get advanced statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get advanced statistics: {str(e)}")

