"""
Redis缓存系统
提供高性能缓存服务，支持：
- 新闻列表缓存
- 搜索结果缓存
- 地图数据缓存
- 事件聚类缓存
"""
import json
import asyncio
from typing import Any, Optional, Union, List
from datetime import datetime, timedelta
import logging

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
except ImportError:
    redis = None
    ConnectionPool = None

from app.core.logger import logger
from app.core.config import settings


class CacheService:
    """高性能缓存服务"""

    def __init__(self):
        """初始化缓存服务"""
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5分钟默认TTL
        self.is_available = False

    async def initialize(self):
        """初始化Redis连接"""
        if not redis:
            logger.warning("Redis未安装，缓存功能不可用")
            return False

        try:
            # 创建连接池
            self.pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )

            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.pool)

            # 测试连接
            await self.redis_client.ping()

            self.is_available = True
            logger.info("Redis缓存系统初始化成功")
            return True

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.is_available = False
            return False

    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            if hasattr(self, 'pool'):
                await self.pool.disconnect()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                # 尝试解析JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.error(f"缓存读取失败 {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        if not self.is_available:
            return False

        try:
            # 序列化值
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, ensure_ascii=False)

            # 设置TTL
            expire_time = ttl or self.default_ttl

            # 设置缓存
            await self.redis_client.setex(
                key=key,
                time=expire_time,
                value=value
            )
            return True

        except Exception as e:
            logger.error(f"缓存写入失败 {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存键"""
        if not self.is_available:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self.is_available:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"批量清除缓存失败 {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.is_available:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"缓存检查失败 {key}: {e}")
            return False

    def make_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)

    # 预定义的缓存键生成器
    def news_list_key(self, page: int, page_size: int, source: str = None, category: str = None):
        """新闻列表缓存键"""
        parts = [f"page_{page}", f"size_{page_size}"]
        if source:
            parts.append(f"source_{source}")
        if category:
            parts.append(f"category_{category}")
        return self.make_key("news_list", *parts)

    def search_key(self, query: str, page: int, page_size: int, source: str = None, category: str = None):
        """搜索结果缓存键"""
        parts = [f"q_{query}", f"page_{page}", f"size_{page_size}"]
        if source:
            parts.append(f"source_{source}")
        if category:
            parts.append(f"category_{category}")
        return self.make_key("search", *parts)

    def map_clusters_key(self, category: str = None):
        """地图聚类缓存键"""
        parts = []
        if category:
            parts.append(f"category_{category}")
        return self.make_key("map_clusters", *parts)

    def events_key(self, days: int, category: str = None):
        """事件时间轴缓存键"""
        parts = [f"days_{days}"]
        if category:
            parts.append(f"category_{category}")
        return self.make_key("events", *parts)


# 全局缓存服务实例
cache_service = CacheService()


async def get_cache() -> CacheService:
    """获取缓存服务实例"""
    if not cache_service.is_available:
        await cache_service.initialize()
    return cache_service


# 缓存TTL配置
CACHE_TTL = {
    "news_list": 300,      # 5分钟 - 新闻更新频繁
    "search": 600,           # 10分钟 - 搜索结果变化不快
    "map_clusters": 900,    # 15分钟 - 地图数据变化较慢
    "events": 1200,          # 20分钟 - 事件分析相对稳定
    "llm_config": 3600,      # 1小时 - LLM配置变化很少
    "stats": 180,            # 3分钟 - 统计数据变化较快
}