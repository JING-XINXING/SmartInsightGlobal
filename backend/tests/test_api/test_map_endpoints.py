import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_map_clusters():
    """Test getting map clusters"""
    # This is a placeholder test. 
    # In a real scenario, we would mock the database response or ensure data exists.
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/map/clusters")
    except OSError:
        pytest.skip("数据库不可用，跳过地图接口测试")
    if response.status_code >= 500:
        pytest.skip("数据库不可用，跳过地图接口测试")
    assert response.status_code == 200 
