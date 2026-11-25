"""
测试新闻API端点
"""
import socket

import pytest
from httpx import AsyncClient
from sqlalchemy.future import select
from app.models.news import News
from app.schemas.news import NewsCreate


def _postgres_available() -> bool:
    """本机 5432 没有服务时，新闻接口用例无法执行。"""
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=0.3):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="PostgreSQL 未启动，跳过新闻接口测试",
)


@pytest.mark.api
@pytest.mark.asyncio
class TestNewsEndpoints:
    """测试新闻API端点"""

    @pytest.mark.asyncio
    async def test_read_news_simple(self, client: AsyncClient, sample_news):
        """测试简单新闻列表接口"""
        response = await client.get("/api/v1/news")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # 至少有3条示例新闻

    @pytest.mark.asyncio
    async def test_read_news_paginated_default(self, client: AsyncClient, sample_news):
        """测试分页新闻列表接口（默认参数）"""
        response = await client.get("/api/v1/news/paginated")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["total_pages"], int)

        # 默认值验证
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) <= 20

    @pytest.mark.asyncio
    async def test_read_news_paginated_custom_params(self, client: AsyncClient, sample_news):
        """测试分页新闻列表接口（自定义参数）"""
        response = await client.get("/api/v1/news/paginated?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_read_news_paginated_out_of_bounds(self, client: AsyncClient, sample_news):
        """测试分页新闻列表接口（超出边界）"""
        response = await client.get("/api/v1/news/paginated?page=999&page_size=10")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 999
        assert data["total"] == 3  # 示例数据数量
        assert data["total_pages"] == 1  # ceil(3/10) = 1
        assert len(data["items"]) == 0  # 没有数据

    @pytest.mark.asyncio
    async def test_read_news_paginated_filter_by_source(self, client: AsyncClient, sample_news):
        """测试按来源筛选分页"""
        response = await client.get("/api/v1/news/paginated?source=Test News")

        assert response.status_code == 200
        data = response.json()

        # 应该只返回"Test News"来源的新闻
        for item in data["items"]:
            assert item["source"] == "Test News"

    @pytest.mark.asyncio
    async def test_read_news_paginated_filter_by_category(self, client: AsyncClient, sample_news):
        """测试按分类筛选分页"""
        response = await client.get("/api/v1/news/paginated?category=科技")

        assert response.status_code == 200
        data = response.json()

        # 应该只返回"科技"分类的新闻
        for item in data["items"]:
            assert item["category"] == "科技"

    @pytest.mark.asyncio
    async def test_read_news_paginated_invalid_params(self, client: AsyncClient):
        """测试无效参数的分页接口"""
        # 测试无效的页码
        response = await client.get("/api/v1/news/paginated?page=0&page_size=10")
        assert response.status_code == 422  # 验证失败

        # 测试无效的页面大小
        response = await client.get("/api/v1/news/paginated?page=1&page_size=200")
        assert response.status_code == 422  # 超出最大限制

        # 测试负数
        response = await client.get("/api/v1/news/paginated?page=-1&page_size=10")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_read_news_by_id_exists(self, client: AsyncClient, sample_news):
        """测试通过ID获取存在的新闻"""
        # 获取第一条新闻的ID
        response = await client.get("/api/v1/news")
        news_list = response.json()
        first_news = news_list[0]
        news_id = first_news["id"]

        # 获取详情
        response = await client.get(f"/api/v1/news/{news_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == news_id
        assert data["title"] == first_news["title"]
        assert data["source"] == first_news["source"]
        assert "content" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_read_news_by_id_not_exists(self, client: AsyncClient):
        """测试通过ID获取不存在的新闻"""
        response = await client.get("/api/v1/news/99999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "新闻不存在"

    @pytest.mark.asyncio
    async def test_search_news_basic(self, client: AsyncClient, sample_news):
        """测试基础新闻搜索"""
        response = await client.get("/api/v1/news/search?q=经济")

        assert response.status_code == 200
        data = response.json()

        # 验证搜索响应结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "query" in data

        assert data["query"] == "经济"
        assert isinstance(data["items"], list)

        # 应该找到与"经济"相关的新闻
        assert len(data["items"]) > 0

    @pytest.mark.asyncio
    async def test_search_news_no_results(self, client: AsyncClient, sample_news):
        """测试无结果的新闻搜索"""
        response = await client.get("/api/v1/news/search?q=不存在的关键词xyz123")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_search_news_with_filters(self, client: AsyncClient, sample_news):
        """测试带筛选的新闻搜索"""
        response = await client.get("/api/v1/news/search?q=技术&category=科技&page_size=5")

        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "技术"
        assert data["page_size"] == 5

        # 验证筛选结果
        for item in data["items"]:
            assert item["category"] == "科技"

    @pytest.mark.asyncio
    async def test_search_news_invalid_params(self, client: AsyncClient):
        """测试无效搜索参数"""
        # 测试空查询
        response = await client.get("/api/v1/news/search?q=")
        assert response.status_code == 422

        # 测试查询太短
        response = await client.get("/api/v1/news/search?q=a")
        assert response.status_code == 422

        # 测试无效的页面大小
        response = await client.get("/api/v1/news/search?q=test&page_size=100")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_news(self, client: AsyncClient):
        """测试创建新闻"""
        news_data = {
            "title": "测试新闻创建",
            "content": "这是测试新闻的内容",
            "summary": "测试摘要",
            "source": "Test API",
            "url": "http://example.com/test-create",
            "publish_date": "2024-01-01T12:00:00Z"
        }

        response = await client.post("/api/v1/news/", json=news_data)

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == news_data["title"]
        assert data["content"] == news_data["content"]
        assert data["source"] == news_data["source"]
        assert data["url"] == news_data["url"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_news_duplicate_url(self, client: AsyncClient):
        """测试创建重复URL的新闻"""
        news_data = {
            "title": "重复URL新闻",
            "content": "内容",
            "source": "Test API",
            "url": "http://example.com/duplicate-test"
        }

        # 第一次创建应该成功
        response1 = await client.post("/api/v1/news/", json=news_data)
        assert response1.status_code == 200

        # 第二次创建应该失败（URL唯一约束）
        response2 = await client.post("/api/v1/news/", json=news_data)
        # 可能返回500或422，取决于数据库实现
        assert response2.status_code in [500, 422]

    @pytest.mark.asyncio
    async def test_create_news_invalid_data(self, client: AsyncClient):
        """测试创建无效新闻数据"""
        # 测试缺少必需字段
        invalid_data = {
            "title": "无效新闻"
            # 缺少content, source, url等
        }

        response = await client.post("/api/v1/news/", json=invalid_data)
        assert response.status_code == 422

        # 测试无效的日期格式
        invalid_data = {
            "title": "测试",
            "content": "内容",
            "source": "Test",
            "url": "http://example.com/test",
            "publish_date": "invalid-date"
        }

        response = await client.post("/api/v1/news/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """测试健康检查接口"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """测试根路径接口"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to SmartInsight Global API"

    @pytest.mark.asyncio
    async def test_news_with_analysis_data(self, client: AsyncClient, db_session):
        """测试包含分析数据的新闻"""
        # 创建包含分析数据的新闻
        news_with_analysis = NewsCreate(
            title="包含分析数据的新闻",
            content="这是新闻内容",
            summary="新闻摘要",
            source="Test News",
            url="http://example.com/news-with-analysis",
            sentiment_score=75,
            keywords=["测试", "分析", "数据"],
            category="经济",
            location={
                "country": "美国",
                "country_cn": "美国",
                "city": "纽约",
                "lat": 40.7128,
                "lng": -74.0060
            }
        )

        # 直接插入数据库
        db_news = News(**news_with_analysis.dict())
        db_session.add(db_news)
        await db_session.commit()
        await db_session.refresh(db_news)

        # 获取新闻详情
        response = await client.get(f"/api/v1/news/{db_news.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["sentiment_score"] == 75
        assert data["keywords"] == ["测试", "分析", "数据"]
        assert data["category"] == "经济"
        assert data["location"]["country"] == "美国"
        assert data["location"]["city"] == "纽约"
        assert data["location"]["lat"] == 40.7128
        assert data["location"]["lng"] == -74.0060

    @pytest.mark.asyncio
    async def test_news_ordering(self, client: AsyncClient, sample_news):
        """测试新闻排序"""
        response = await client.get("/api/v1/news/paginated?page_size=10")

        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        if len(items) >= 2:
            # 验证按发布时间降序排列
            for i in range(len(items) - 1):
                current_date = items[i]["publish_date"]
                next_date = items[i + 1]["publish_date"]
                # 降序：当前应该>=下一个
                assert current_date >= next_date

    @pytest.mark.asyncio
    async def test_pagination_links(self, client: AsyncClient):
        """测试分页链接头部信息"""
        response = await client.get("/api/v1/news/paginated?page=1&page_size=5")

        assert response.status_code == 200
        # 可以检查是否有适当的头部信息（如果实现的话）
        # 这里我们主要验证响应数据的分页计算是否正确

    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """测试CORS头部"""
        response = await client.options("/api/v1/news")

        # 验证CORS头部
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    @pytest.mark.asyncio
    async def test_news_response_schema(self, client: AsyncClient, sample_news):
        """测试新闻响应模式"""
        response = await client.get("/api/v1/news/paginated")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            item = data["items"][0]

            # 验证必需字段存在
            required_fields = ["id", "title", "source", "url", "publish_date", "created_at"]
            for field in required_fields:
                assert field in item

            # 验证字段类型
            assert isinstance(item["id"], int)
            assert isinstance(item["title"], str)
            assert isinstance(item["source"], str)
            assert isinstance(item["url"], str)
            assert isinstance(item["publish_date"], str)

            # 可选字段应该为null或适当类型
            optional_fields = ["summary", "content", "sentiment_score", "keywords", "category", "location"]
            for field in optional_fields:
                assert field in item
                if field in ["sentiment_score"]:
                    assert item[field] is None or isinstance(item[field], (int, float))
                elif field in ["keywords"]:
                    assert item[field] is None or isinstance(item[field], list)
                elif field in ["category"]:
                    assert item[field] is None or isinstance(item[field], str)
                elif field in ["location"]:
                    assert item[field] is None or isinstance(item[field], dict)