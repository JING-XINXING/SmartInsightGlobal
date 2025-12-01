"""
事件时间轴 API 端点
基于关键词聚类关联相关新闻，生成事件时间轴
"""
from typing import Any, List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from pydantic import BaseModel
from app import models
from app.db import session
from app.core.logger import logger

router = APIRouter()


class TimelineNews(BaseModel):
    """时间轴新闻项"""
    id: int
    title: str
    source: str
    publish_date: str
    sentiment_score: Optional[int] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None


class EventCluster(BaseModel):
    """事件聚类"""
    event_id: str
    title: str  # 事件标题（取自第一条或最热门新闻）
    keywords: List[str]  # 共同关键词
    category: Optional[str] = None
    news_count: int
    avg_sentiment: float
    start_date: str
    end_date: str
    news: List[TimelineNews]


class TimelineResponse(BaseModel):
    """时间轴响应"""
    events: List[EventCluster]
    total_events: int
    date_range: Dict[str, str]


def calculate_keyword_similarity(kw1: List[str], kw2: List[str]) -> float:
    """
    计算两组关键词的相似度 (Jaccard 系数)
    """
    if not kw1 or not kw2:
        return 0.0
    set1 = set(k.lower() for k in kw1)
    set2 = set(k.lower() for k in kw2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def cluster_news_by_keywords(news_list: List, similarity_threshold: float = 0.3) -> List[List]:
    """
    基于关键词相似度对新闻进行聚类
    使用简单的贪心聚类算法
    """
    if not news_list:
        return []
    
    clusters = []
    used = set()
    
    # 按发布时间排序
    sorted_news = sorted(news_list, key=lambda x: x.publish_date or datetime.min, reverse=True)
    
    for news in sorted_news:
        if news.id in used:
            continue
        
        # 创建新聚类
        cluster = [news]
        used.add(news.id)
        news_keywords = news.keywords or []
        
        # 查找相关新闻
        for other in sorted_news:
            if other.id in used:
                continue
            
            other_keywords = other.keywords or []
            
            # 计算相似度
            similarity = calculate_keyword_similarity(news_keywords, other_keywords)
            
            # 同类别加权
            if news.category and other.category and news.category == other.category:
                similarity += 0.2
            
            # 时间窗口内（7天）加权
            if news.publish_date and other.publish_date:
                time_diff = abs((news.publish_date - other.publish_date).days)
                if time_diff <= 7:
                    similarity += 0.1
            
            if similarity >= similarity_threshold:
                cluster.append(other)
                used.add(other.id)
        
        if len(cluster) >= 2:  # 至少2条新闻才算一个事件
            clusters.append(cluster)
    
    return clusters


@router.get("/timeline", response_model=TimelineResponse)
async def get_event_timeline(
    db: AsyncSession = Depends(session.get_db),
    days: int = Query(7, ge=1, le=30, description="时间范围（天）"),
    min_cluster_size: int = Query(2, ge=2, le=10, description="最小聚类大小"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    limit: int = Query(20, ge=5, le=50, description="返回事件数量"),
) -> Any:
    """
    获取事件时间轴
    
    基于关键词相似度聚类新闻，生成事件发展脉络
    """
    # 计算时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 查询有关键词的新闻
    query = select(models.news.News).where(
        and_(
            models.news.News.keywords.isnot(None),
            models.news.News.publish_date >= start_date,
            models.news.News.publish_date <= end_date
        )
    )
    
    if category:
        query = query.where(models.news.News.category == category)
    
    query = query.order_by(models.news.News.publish_date.desc()).limit(500)
    
    result = await db.execute(query)
    news_list = result.scalars().all()
    
    logger.info(f"查询到 {len(news_list)} 条带关键词的新闻")
    
    # 执行聚类
    clusters = cluster_news_by_keywords(news_list)
    
    # 转换为响应格式
    events = []
    for idx, cluster in enumerate(clusters[:limit]):
        if len(cluster) < min_cluster_size:
            continue
        
        # 提取共同关键词
        all_keywords = []
        for news in cluster:
            all_keywords.extend(news.keywords or [])
        
        keyword_counts = defaultdict(int)
        for kw in all_keywords:
            keyword_counts[kw.lower()] += 1
        
        # 取出现次数最多的关键词
        common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [k for k, _ in common_keywords[:5]]
        
        # 计算统计信息
        sentiment_sum = sum(n.sentiment_score or 0 for n in cluster)
        avg_sentiment = sentiment_sum / len(cluster) if cluster else 0
        
        dates = [n.publish_date for n in cluster if n.publish_date]
        start = min(dates).isoformat() if dates else ""
        end = max(dates).isoformat() if dates else ""
        
        # 获取主要分类
        category_counts = defaultdict(int)
        for n in cluster:
            if n.category:
                category_counts[n.category] += 1
        main_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        
        # 创建事件对象
        events.append(EventCluster(
            event_id=f"evt_{idx + 1}",
            title=cluster[0].title,  # 取第一条新闻标题作为事件标题
            keywords=top_keywords,
            category=main_category,
            news_count=len(cluster),
            avg_sentiment=round(avg_sentiment, 1),
            start_date=start,
            end_date=end,
            news=[
                TimelineNews(
                    id=n.id,
                    title=n.title,
                    source=n.source,
                    publish_date=n.publish_date.isoformat() if n.publish_date else "",
                    sentiment_score=n.sentiment_score,
                    category=n.category,
                    keywords=n.keywords
                )
                for n in sorted(cluster, key=lambda x: x.publish_date or datetime.min)
            ]
        ))
    
    # 按新闻数量排序
    events.sort(key=lambda x: x.news_count, reverse=True)
    
    logger.info(f"生成 {len(events)} 个事件聚类")
    
    return TimelineResponse(
        events=events,
        total_events=len(events),
        date_range={
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    )


@router.get("/event/{event_id}", response_model=EventCluster)
async def get_event_detail(
    event_id: str,
    db: AsyncSession = Depends(session.get_db),
) -> Any:
    """
    获取单个事件详情
    注意：这是一个简化实现，实际上事件ID是临时的
    """
    # 由于事件是动态聚类的，这里返回一个提示
    # 实际实现可能需要持久化事件数据
    raise Exception("事件详情功能需要持久化存储，请使用 /timeline 接口获取数据")


@router.get("/trending-topics", response_model=List[Dict])
async def get_trending_topics(
    db: AsyncSession = Depends(session.get_db),
    days: int = Query(3, ge=1, le=7, description="时间范围（天）"),
    limit: int = Query(10, ge=5, le=20, description="返回数量"),
) -> Any:
    """
    获取热门话题/关键词
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 查询最近的新闻
    query = select(models.news.News).where(
        and_(
            models.news.News.keywords.isnot(None),
            models.news.News.publish_date >= start_date
        )
    ).limit(200)
    
    result = await db.execute(query)
    news_list = result.scalars().all()
    
    # 统计关键词频率
    keyword_data = defaultdict(lambda: {"count": 0, "sentiment_sum": 0, "news_ids": []})
    
    for news in news_list:
        for kw in (news.keywords or []):
            kw_lower = kw.lower()
            keyword_data[kw_lower]["count"] += 1
            keyword_data[kw_lower]["sentiment_sum"] += news.sentiment_score or 0
            keyword_data[kw_lower]["news_ids"].append(news.id)
    
    # 转换并排序
    trending = []
    for keyword, data in keyword_data.items():
        if data["count"] >= 2:  # 至少出现2次
            avg_sentiment = data["sentiment_sum"] / data["count"]
            trending.append({
                "keyword": keyword,
                "count": data["count"],
                "avg_sentiment": round(avg_sentiment, 1),
                "news_ids": data["news_ids"][:10]
            })
    
    trending.sort(key=lambda x: x["count"], reverse=True)
    
    return trending[:limit]

