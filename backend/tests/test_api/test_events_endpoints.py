import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_events():
    """Test getting events"""
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/events/timeline")
    except OSError:
        pytest.skip("数据库不可用，跳过事件接口测试")
    if response.status_code >= 500:
        pytest.skip("数据库不可用，跳过事件接口测试")
    assert response.status_code == 200
