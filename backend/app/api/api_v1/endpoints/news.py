from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, text, or_
from pydantic import BaseModel

from app import schemas, models
from app.db import session
from app.core.cache_service import NewsCacheService, cache_result

router = APIRouter()


class PaginatedNewsResponse(BaseModel):
    """分页新闻响应模型"""
    items: List[schemas.news.News]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/", response_model=List[schemas.news.News])
async def read_news(
    db: AsyncSession = Depends(session.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    获取新闻列表（简单模式，向后兼容）
    """
    result = await db.execute(
        select(models.news.News)
        .order_by(models.news.News.publish_date.desc())
        .offset(skip)
        .limit(limit)
    )
    news = result.scalars().all()
    return news


@router.get("/paginated", response_model=PaginatedNewsResponse)
async def read_news_paginated(
    db: AsyncSession = Depends(session.get_db),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=10, le=100, description="每页数量，10-100"),
    source: Optional[str] = Query(None, description="按来源筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
) -> Any:
    """
    获取新闻列表（分页模式）

    返回分页数据，包含：
    - items: 当前页的新闻列表
    - total: 总新闻数
    - page: 当前页码
    - page_size: 每页数量
    - total_pages: 总页数
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

    return PaginatedNewsResponse(
        items=news,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/paginated/cached", response_model=PaginatedNewsResponse)
@cache_result(
    key_func=lambda page, page_size, source, category: NewsCacheService.make_news_list_key(page, page_size, source, category),
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

    性能优化特性：
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

    return PaginatedNewsResponse(
        items=news,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


class SearchResponse(BaseModel):
    """搜索响应模型"""
    items: List[schemas.news.News]
    total: int
    page: int
    page_size: int
    query: str


@router.get("/search", response_model=SearchResponse)
async def search_news(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    db: AsyncSession = Depends(session.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=10, le=50, description="每页数量"),
    source: Optional[str] = Query(None, description="按来源筛选"),
    category: Optional[str] = Query(None, description="按分类筛选"),
) -> Any:
    """
    简单搜索新闻

    使用 SQL LIKE 查询，支持:
    - 标题匹配
    - 摘要匹配
    - 内容匹配

    结果按发布时间排序
    """
    # 基础查询 - 使用简单的LIKE搜索
    base_conditions = [
        models.news.News.title.ilike(f"%{q}%")
    ]

    # 添加摘要和内容搜索条件
    search_conditions = base_conditions + [
        models.news.News.summary.ilike(f"%{q}%"),
        models.news.News.content.ilike(f"%{q}%")
    ]

    # 构建基础查询
    base_query = select(models.news.News).where(
        or_(*search_conditions)
    )

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

    # 按发布时间排序并分页
    skip = (page - 1) * page_size
    result_query = base_query.order_by(
        models.news.News.publish_date.desc()
    ).offset(skip).limit(page_size)

    result = await db.execute(result_query)
    news_list = result.scalars().all()

    return SearchResponse(
        items=news_list,
        total=total,
        page=page,
        page_size=page_size,
        query=q
    )


@router.get("/{news_id}", response_model=schemas.news.News)
async def read_news_by_id(
    news_id: int,
    db: AsyncSession = Depends(session.get_db),
) -> Any:
    """
    根据 ID 获取单条新闻详情
    """
    result = await db.execute(
        select(models.news.News).where(models.news.News.id == news_id)
    )
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return news


@router.post("/", response_model=schemas.news.News)
async def create_news(
    *,
    db: AsyncSession = Depends(session.get_db),
    news_in: schemas.news.NewsCreate,
) -> Any:
    """
    创建新闻
    """
    news = models.news.News(**news_in.dict())
    db.add(news)
    await db.commit()
    await db.refresh(news)

    # 创建新闻后失效缓存
    await NewsCacheService.invalidate_news_cache()

    return news


@router.post("/invalidate/cache")
async def invalidate_cache():
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
