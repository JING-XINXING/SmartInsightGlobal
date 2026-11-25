"""
简单的API测试验证
不依赖数据库，验证FastAPI应用能正常启动
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_check():
    """测试健康检查接口"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_root_endpoint():
    """测试根接口"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


if __name__ == "__main__":
    try:
        test_health_check()
        test_root_endpoint()
        print("✅ API基础功能测试通过")
    except Exception as e:
        print(f"❌ API测试失败: {e}")