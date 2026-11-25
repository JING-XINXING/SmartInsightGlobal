"""异步数据库会话。

API 进程使用队列连接池，避免每次请求新建连接。
Celery 任务通过 asyncio.run 创建新的事件循环，池里的连接仍绑定旧循环，
因此 worker 在导入本模块之前设置 CELERY_WORKER=1，改用 NullPool。
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _is_celery_worker() -> bool:
    """当前进程是否为 Celery worker。"""
    value = os.getenv("CELERY_WORKER", "").strip().lower()
    return value in ("1", "true", "yes")


def _engine_kwargs() -> dict:
    """按进程类型返回引擎参数。"""
    if _is_celery_worker():
        return {"poolclass": NullPool}
    return {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,
    }


engine = create_async_engine(
    settings.assemble_db_url(),
    echo=os.getenv("SQL_ECHO", "false").strip().lower() in ("1", "true", "yes"),
    future=True,
    **_engine_kwargs(),
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """FastAPI 依赖：提供一次请求范围的数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session
