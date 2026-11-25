"""V1.6 平台基础能力测试。

覆盖版本号、统一错误响应、连接池和限流开关。
这些用例不依赖 PostgreSQL。
"""
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import error_body
from app.core.version import APP_VERSION
from app.db.session import engine
from app.main import app


@pytest.mark.unit
def test_error_body_shape() -> None:
    """统一错误体包含 code、message、data。"""
    body = error_body(422, "请求参数校验失败", [{"loc": ["body"]}])
    assert body["code"] == 422
    assert body["message"] == "请求参数校验失败"
    assert isinstance(body["data"], list)


@pytest.mark.unit
def test_rate_limit_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """限流开关读取环境变量，默认开启。"""
    from app.core.rate_limit import _rate_limit_enabled

    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    assert _rate_limit_enabled() is True
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    assert _rate_limit_enabled() is False
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    assert _rate_limit_enabled() is True


@pytest.mark.unit
def test_api_process_uses_connection_pool() -> None:
    """API 进程不使用 NullPool。Celery 才在导入前切到 NullPool。"""
    pool_name = type(engine.pool).__name__
    assert "Null" not in pool_name


@pytest.mark.api
@pytest.mark.asyncio
async def test_health_and_version() -> None:
    """健康检查和元信息返回 V1.6 版本号。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/health")
        meta = await client.get("/api/v1/meta/version")

    assert health.status_code == 200
    assert health.json()["version"] == APP_VERSION
    assert health.json()["status"] == "healthy"
    assert meta.status_code == 200
    assert meta.json() == {"name": "SmartInsight Global", "version": APP_VERSION}


@pytest.mark.api
@pytest.mark.asyncio
async def test_not_found_uses_unified_error() -> None:
    """未知路径返回 code/message/data，而不是仅有 detail。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/does-not-exist")

    body: dict[str, Any] = response.json()
    assert response.status_code == 404
    assert body["code"] == 404
    assert isinstance(body["message"], str)
    assert "data" in body


@pytest.mark.api
@pytest.mark.asyncio
async def test_validation_error_uses_unified_error() -> None:
    """缺少必填字段时返回 422 统一错误体。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/llm/update-config", json={})

    body = response.json()
    assert response.status_code == 422
    assert body["code"] == 422
    assert body["message"] == "请求参数校验失败"
    assert isinstance(body["data"], list)


@pytest.mark.api
@pytest.mark.asyncio
async def test_full_routers_are_mounted() -> None:
    """正式模块已挂载，简化副本里没有的路径可以访问到路由。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        spec = (await client.get("/api/v1/openapi.json")).json()

    paths = spec["paths"]
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/map/hotspots" in paths
    assert "/api/v1/i18n/detect-language" in paths
    assert "/api/v1/analysis/history" in paths
    assert "/api/v1/meta/version" in paths
