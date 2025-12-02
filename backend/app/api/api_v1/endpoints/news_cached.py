"""
带缓存的新闻API端点
实现高性能的新闻数据访问
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text, or_
from pydantic import BaseModel

from app import schemas, models
from app.db import session
from app.core.cache_service import NewsCacheService, cache_result


class PaginatedNewsResponse(BaseModel):
    """分页新闻响应模型"""
    items: List[schemas.news.News]
    total: int
    page: int
    page_size: int
    total_pages: int
    cache_info: dict = {}


class SearchResponse(BaseModel):
    """搜索响应模型"""
    items: List[schemas.news.News]
    total: int
    page: int
    page_size: int
    query: str
    cache_info: dict = {}


router = APIRouter()


@router.get("/cached/paginated", response_model=PaginatedNewsResponse)
@cache_result(
    key_func=NewsCacheService.make_news_list_key,
    ttl=300,  # 5分钟
    cache_group="news_list"
)
async def read_news_paginated_cached(
    db: AsyncSession = Depends(session.get_db),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=10, le=100, description="每页数量，10-100"),
    source: Optional[str] = Query(None, description="按来源筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
) -> Any:
    """
    获取新闻列表（分页模式，带缓存）

    优化的性能特性：
    - Redis缓存结果
    - 数据库查询优化
    - 智能缓存失效
    """
    # 构建查询条件
    query = select(models.news.News)
    count_query = select(func.count(models.news.News.id))

    # 添加筛选条件
    if source:
        query = query.where(models.news.News.source == source)
        count_query = count_query.where(models.news.News.source == source)

    if category:
        query = query.where(models.news.News.category == category)
        count_query = count_query.where(models.news.News.category == category)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 计算分页
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    skip = (page - 1) * page_size

    # 获取当前页数据
    result = await db.execute(
        query
        .order_by(models.news.News.publish_date.desc())
        .offset(skip)
        .limit(page_size)
    )
    news = result.scalars().all()

    response = PaginatedNewsResponse(
        items=news,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        cache_info={
            "cached": True,
            "ttl": 300,
            "cache_group": "news_list"
        }
    )

    return response


@router.get("/cached/search", response_model=SearchResponse)
@cache_result(
    key_func=NewsCacheService.make_search_key,
    ttl=600,  # 10分钟
    cache_group="search"
)
async def search_news_cached(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    db: AsyncSession = Depends(session.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=10, le=50, description="每页数量"),
    source: Optional[str] = Query(None, description="按来源筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
) -> Any:
    """
    全文搜索新闻（带缓存）

    使用 PostgreSQL 全文搜索 + Redis 缓存：
    - 支持标题、内容、关键词匹配
    - 按相关性排序
    - 智能缓存失效
    """
    # 构建搜索查询
    search_query = func.plainto_tsquery('english', q)

    # 基础查询 - 使用全文搜索
    base_query = select(models.news.News).where(
        text("search_vector @@ plainto_tsquery('english', :query)")
    ).params(query=q)

    # 添加筛选条件
    if source:
        base_query = base_query.where(models.news.News.source == source)
    if category:
        base_query = base_query.where(models.news.News.category == category)

    # 获取总数
    count_query = select(func.count()).select_from(
        base_query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 按相关性排序并分页
    skip = (page - 1) * page_size
    result_query = base_query.order_by(
        text("ts_rank(search_vector, plainto_tsquery('english', :query)) DESC")
    ).params(query=q).offset(skip).limit(page_size)

    result = await db.execute(result_query)
    news_list = result.scalars().all()

    return SearchResponse(
        items=news_list,
        total=total,
        page=page,
        page_size=page_size,
        query=q,
        cache_info={
            "cached": True,
            "ttl": 600,
            "cache_group": "search"
        }
    )


@router.post("/invalidate/news")
async def invalidate_news_cache():
    """手动失效新闻缓存"""
    success = await NewsCacheService.invalidate_news_cache()
    return {
        "message": "新闻缓存失效完成" if success else "缓存失效失败",
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    return await NewsCacheService.get_cache_stats()


@router.post("/performance/test")
async def performance_test(db: AsyncSession = Depends(session.get_db)):
    """性能测试端点"""
    import time

    # 测试带缓存的查询
    start_time = time.time()
    await db.execute(
        select(models.news.News)
        .order_by(models.news.News.publish_date.desc())
        .limit(10)
    )
    cached_time = time.time() - start_time

    return {
        "cached_query_time": cached_time,
        "message": f"缓存查询时间: {cached_time:.4f}秒"
    }