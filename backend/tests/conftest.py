"""
pytest 配置文件
定义测试fixture和共享配置
"""

import pytest
import asyncio
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

# 导入共享fixture
from . import db_session, client, sample_news, sample_source

# 异步测试支持
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 测试标记
pytest_plugins = []

# 自定义标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试 - 快速执行，不依赖外部服务"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试 - 需要数据库或外部服务"
    )
    config.addinivalue_line(
        "markers", "api: API测试 - 测试HTTP端点"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试 - 执行时间较长"
    )

# 测试收集设置
collect_ignore_glob = [
    "*/migrations/*",
    "*/venv/*",
    "*/__pycache__/*"
]

# 异步测试支持
@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """支持异步测试函数"""
    if asyncio.iscoroutinefunction(pyfuncitem.function):
        pyfuncitem.function = pytest.mark.asyncio(pyfuncitem.function)
        return False
    return True