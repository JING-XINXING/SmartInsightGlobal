"""
缓存服务层
为API端点提供高性能缓存功能
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime

from app.core.cache import cache_service
from app.core.logger import logger


def cache_result(
    key_func: Callable,
    ttl: Optional[int] = None,
    cache_group: str = "default"
):
    """
    缓存函数结果的装饰器

    Args:
        key_func: 生成缓存键的函数
        ttl: 缓存时间(秒)，None使用默认
        cache_group: 缓存组，用于TTL配置
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = key_func(*args, **kwargs)

            # 尝试从缓存获取
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # 缓存未命中，执行函数
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # 获取TTL
            if ttl is None:
                from app.core.cache import CACHE_TTL
                ttl = CACHE_TTL.get(cache_group, 300)

            # 存入缓存
            await cache_service.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class NewsCacheService:
    """新闻缓存服务"""

    @staticmethod
    def make_news_list_key(page: int, page_size: int, source: str = None, category: str = None):
        """生成新闻列表缓存键"""
        return cache_service.news_list_key(page, page_size, source, category)

    @staticmethod
    def make_search_key(query: str, page: int, page_size: int, source: str = None, category: str = None):
        """生成搜索缓存键"""
        return cache_service.search_key(query, page, page_size, source, category)

    @staticmethod
    def make_map_clusters_key(category: str = None):
        """生成地图聚类缓存键"""
        return cache_service.map_clusters_key(category)

    @staticmethod
    def make_events_key(days: int, category: str = None):
        """生成事件缓存键"""
        return cache_service.events_key(days, category)

    @staticmethod
    async def invalidate_news_cache():
        """失效新闻相关缓存"""
        try:
            # 清理新闻列表缓存
            await cache_service.clear_pattern("news_list:*")

            # 清理搜索缓存
            await cache_service.clear_pattern("search:*")

            logger.info("新闻缓存已失效")
            return True
        except Exception as e:
            logger.error(f"缓存失效失败: {e}")
            return False

    @staticmethod
    async def invalidate_map_cache():
        """失效地图相关缓存"""
        try:
            await cache_service.clear_pattern("map_clusters:*")
            logger.info("地图缓存已失效")
            return True
        except Exception as e:
            logger.error(f"地图缓存失效失败: {e}")
            return False

    @staticmethod
    async def invalidate_events_cache():
        """失效事件相关缓存"""
        try:
            await cache_service.clear_pattern("events:*")
            logger.info("事件缓存已失效")
            return True
        except Exception as e:
            logger.error(f"事件缓存失效失败: {e}")
            return False

    @staticmethod
    async def get_cache_stats() -> dict:
        """获取缓存统计信息"""
        try:
            if not cache_service.is_available:
                return {"status": "unavailable"}

            # 检查不同类型的缓存命中
            test_keys = [
                "news_list:page_1:size_20",
                "search:q_test:page_1:size_20",
                "map_clusters:*",
                "events:days_7"
            ]

            cache_status = {}
            for key in test_keys:
                exists = await cache_service.exists(key)
                cache_status[key] = exists

            return {
                "status": "available",
                "test_keys": cache_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"status": "error", "error": str(e)}