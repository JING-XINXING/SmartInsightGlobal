"""
测试新闻数据模型
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models.news import News


@pytest.mark.unit
class TestNewsModel:
    """测试新闻模型"""

    async def test_news_creation(self, db_session):
        """测试新闻创建"""
        news = News(
            title="测试新闻标题",
            content="这是测试新闻内容",
            summary="测试摘要",
            source="测试来源",
            url="http://example.com/test-news",
            sentiment_score=50,
            keywords=["测试", "新闻"],
            category="科技"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.id is not None
        assert news.title == "测试新闻标题"
        assert news.content == "这是测试新闻内容"
        assert news.summary == "测试摘要"
        assert news.source == "测试来源"
        assert news.url == "http://example.com/test-news"
        assert news.sentiment_score == 50
        assert news.keywords == ["测试", "新闻"]
        assert news.category == "科技"
        assert news.created_at is not None

    async def test_news_creation_minimal(self, db_session):
        """测试最小新闻创建"""
        news = News(
            title="最小新闻",
            source="测试来源",
            url="http://example.com/minimal"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.id is not None
        assert news.title == "最小新闻"
        assert news.content is None
        assert news.summary is None
        assert news.sentiment_score is None
        assert news.keywords is None
        assert news.category is None
        assert news.created_at is not None

    async def test_news_unique_url_constraint(self, db_session):
        """测试URL唯一约束"""
        # 第一条新闻
        news1 = News(
            title="新闻1",
            source="来源1",
            url="http://example.com/same-url"
        )

        db_session.add(news1)
        await db_session.commit()

        # 第二条新闻，相同URL应该失败
        news2 = News(
            title="新闻2",
            source="来源2",
            url="http://example.com/same-url"
        )

        db_session.add(news2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_news_different_urls(self, db_session):
        """测试不同URL可以创建"""
        news1 = News(
            title="新闻1",
            source="来源1",
            url="http://example.com/different-url1"
        )

        news2 = News(
            title="新闻2",
            source="来源2",
            url="http://example.com/different-url2"
        )

        db_session.add(news1)
        db_session.add(news2)
        await db_session.commit()

        # 两条新闻都应该成功创建
        assert news1.id is not None
        assert news2.id is not None
        assert news1.id != news2.id

    async def test_news_with_publish_date(self, db_session):
        """测试带发布日期的新闻创建"""
        publish_date = datetime(2024, 1, 1, 12, 0, 0)
        news = News(
            title="带日期的新闻",
            content="内容",
            source="来源",
            url="http://example.com/dated-news",
            publish_date=publish_date
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.publish_date == publish_date

    async def test_news_with_keywords(self, db_session):
        """测试带关键词的新闻创建"""
        keywords = ["人工智能", "技术", "创新", "未来", "发展"]
        news = News(
            title="AI技术新闻",
            content="内容",
            source="来源",
            url="http://example.com/ai-news",
            keywords=keywords
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.keywords == keywords

    async def test_news_with_location(self, db_session):
        """测试带位置信息的新闻创建"""
        location = {
            "country": "美国",
            "country_cn": "美国",
            "city": "旧金山",
            "lat": 37.7749,
            "lng": -122.4194
        }
        news = News(
            title="位置新闻",
            content="内容",
            source="来源",
            url="http://example.com/location-news",
            location=location
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.location == location

    async def test_news_sentiment_score_range(self, db_session):
        """测试情感分数范围"""
        # 测试有效范围
        valid_scores = [-100, -50, 0, 50, 100]
        for score in valid_scores:
            news = News(
                title=f"新闻{score}",
                source="来源",
                url=f"http://example.com/news-{score}"
            )
            db_session.add(news)
            await db_session.commit()
            await db_session.refresh(news)
            assert news.sentiment_score == score
            await db_session.delete(news)
            await db_session.commit()

    async def test_news_string_fields_length(self, db_session):
        """测试字符串字段长度"""
        # 测试非常长的标题
        long_title = "a" * 1000
        news = News(
            title=long_title,
            source="来源",
            url="http://example.com/long-title"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        # 应该成功存储（PostgreSQL支持长文本）
        assert len(news.title) == 1000

    async def test_news_json_fields(self, db_session):
        """测试JSON字段"""
        # 测试复杂的关键词
        complex_keywords = [
            {"type": "技术", "value": "AI"},
            {"type": "公司", "value": "OpenAI"},
            {"type": "概念", "value": "大语言模型"}
        ]
        news = News(
            title="复杂关键词新闻",
            source="来源",
            url="http://example.com/complex-keywords",
            keywords=complex_keywords
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.keywords == complex_keywords

        # 测试复杂的位置信息
        complex_location = {
            "country": "美国",
            "country_cn": "美国",
            "city": "旧金山",
            "state": "加利福尼亚",
            "lat": 37.7749,
            "lng": -122.4194,
            "timezone": "America/Los_Angeles",
            "coordinates": [37.7749, -122.4194]
        }
        news.location = complex_location

        await db_session.commit()
        await db_session.refresh(news)

        assert news.location == complex_location

    async def test_news_update(self, db_session):
        """测试新闻更新"""
        # 创建新闻
        news = News(
            title="原始标题",
            content="原始内容",
            source="来源",
            url="http://example.com/updatable-news"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        original_id = news.id

        # 更新新闻
        news.title = "更新后的标题"
        news.content = "更新后的内容"
        news.sentiment_score = 75
        news.keywords = ["更新", "关键词"]
        news.category = "更新分类"

        await db_session.commit()
        await db_session.refresh(news)

        assert news.id == original_id
        assert news.title == "更新后的标题"
        assert news.content == "更新后的内容"
        assert news.sentiment_score == 75
        assert news.keywords == ["更新", "关键词"]
        assert news.category == "更新分类"

    async def test_news_delete(self, db_session):
        """测试新闻删除"""
        # 创建新闻
        news = News(
            title="待删除的新闻",
            source="来源",
            url="http://example.com/deletable-news"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        news_id = news.id
        assert news_id is not None

        # 删除新闻
        await db_session.delete(news)
        await db_session.commit()

        # 验证删除
        deleted_news = await db_session.get(News, news_id)
        assert deleted_news is None

    async def test_news_query_by_source(self, db_session, sample_news):
        """测试按来源查询新闻"""
        from sqlalchemy.future import select

        # 查询特定来源的新闻
        result = await db_session.execute(
            select(News).where(News.source == "Test News")
        )
        news_list = result.scalars().all()

        assert len(news_list) >= 3  # sample_news中有3条Test News

        for news in news_list:
            assert news.source == "Test News"

    async def test_news_query_by_category(self, db_session, sample_news):
        """测试按分类查询新闻"""
        from sqlalchemy.future import select

        # 查询特定分类的新闻
        result = await db_session.execute(
            select(News).where(News.category == "科技")
        )
        news_list = result.scalars().all()

        assert len(news_list) >= 1  # sample_news中有1条科技新闻

        for news in news_list:
            assert news.category == "科技"

    async def test_news_query_with_sentiment_filter(self, db_session, sample_news):
        """测试带情感过滤的新闻查询"""
        from sqlalchemy.future import select

        # 查询正面情感的新闻
        result = await db_session.execute(
            select(News).where(News.sentiment_score > 0)
        )
        news_list = result.scalars().all()

        assert len(news_list) >= 1  # sample_news中有正面新闻

        for news in news_list:
            assert news.sentiment_score > 0

    async def test_news_query_ordering(self, db_session, sample_news):
        """测试新闻排序查询"""
        from sqlalchemy.future import select
        from sqlalchemy import desc

        # 按创建时间降序查询
        result = await db_session.execute(
            select(News).order_by(desc(News.created_at))
        )
        news_list = result.scalars().all()

        # 验证排序
        for i in range(len(news_list) - 1):
            assert news_list[i].created_at >= news_list[i + 1].created_at

    async def test_news_partial_update(self, db_session):
        """测试部分更新新闻"""
        # 创建新闻
        news = News(
            title="原始标题",
            content="原始内容",
            source="来源",
            url="http://example.com/partial-update-news"
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        original_content = news.content

        # 部分更新（只更新情感分数）
        news.sentiment_score = 25
        await db_session.commit()
        await db_session.refresh(news)

        # 验证部分更新
        assert news.sentiment_score == 25
        assert news.title == "原始标题"  # 未更新
        assert news.content == original_content  # 未更新

    async def test_news_json_field_types(self, db_session):
        """测试JSON字段类型"""
        # 测试关键词作为列表
        news_with_list_keywords = News(
            title="列表关键词",
            source="来源",
            url="http://example.com/list-keywords",
            keywords=["关键词1", "关键词2", "关键词3"]
        )

        # 测试关键词作为对象
        news_with_object_keywords = News(
            title="对象关键词",
            source="来源",
            url="http://example.com/object-keywords",
            keywords={"primary": "关键词1", "secondary": "关键词2"}
        )

        db_session.add(news_with_list_keywords)
        db_session.add(news_with_object_keywords)
        await db_session.commit()

        await db_session.refresh(news_with_list_keywords)
        await db_session.refresh(news_with_object_keywords)

        assert isinstance(news_with_list_keywords.keywords, list)
        assert isinstance(news_with_object_keywords.keywords, dict)

    async def test_news_with_null_fields(self, db_session):
        """测试空字段处理"""
        news = News(
            title="空字段测试",
            source="来源",
            url="http://example.com/null-fields",
            sentiment_score=None,
            keywords=None,
            category=None,
            location=None
        )

        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        assert news.id is not None
        assert news.title == "空字段测试"
        assert news.sentiment_score is None
        assert news.keywords is None
        assert news.category is None
        assert news.location is None