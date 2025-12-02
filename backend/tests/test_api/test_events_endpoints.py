import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_events():
    """Test getting events"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/events")
        assert response.status_code in [200, 404]
