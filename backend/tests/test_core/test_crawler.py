"""
测试RSS爬虫
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import feedparser
from app.core.crawler import crawler, RSSCrawler


@pytest.mark.unit
class TestRSSCrawler:
    """测试RSS爬虫"""

    @pytest.fixture
    def rss_crawler_instance(self):
        """创建RSS爬虫实例"""
        return RSSCrawler()

    def test_initialization(self, rss_crawler_instance):
        """测试爬虫初始化"""
        assert rss_crawler_instance.headers["User-Agent"] == "SmartInsightGlobal/1.0"

    @pytest.mark.asyncio
    async def test_fetch_feed_success(self, rss_crawler_instance):
        """测试成功获取RSS源"""
        # 模拟RSS内容
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>测试新闻源</title>
    <description>测试描述</description>
    <item>
      <title>测试新闻1</title>
      <link>http://example.com/news1</link>
      <description>新闻摘要1</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>测试新闻2</title>
      <link>http://example.com/news2</link>
      <description>新闻摘要2</description>
      <pubDate>Mon, 02 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert len(entries) == 2
            assert entries[0]["title"] == "测试新闻1"
            assert entries[0]["url"] == "http://example.com/news1"
            assert entries[0]["summary"] == "新闻摘要1"
            assert entries[0]["source"] == "测试新闻源"

            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_feed_with_content(self, rss_crawler_instance):
        """测试带内容的RSS源"""
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>测试新闻源</title>
    <item>
      <title>带内容的新闻</title>
      <link>http://example.com/news</link>
      <description>新闻摘要</description>
      <content:encoded>完整的新闻内容，包含详细信息...</content:encoded>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert len(entries) == 1
            assert entries[0]["content"] == "完整的新闻内容，包含详细信息..."

    @pytest.mark.asyncio
    async def test_fetch_feed_timeout(self, rss_crawler_instance):
        """测试RSS获取超时"""
        with patch('httpx.AsyncClient.get', side_effect=Exception("Timeout")):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert entries == []

    @pytest.mark.asyncio
    async def test_fetch_feed_http_error(self, rss_crawler_instance):
        """测试HTTP错误"""
        import httpx

        with patch('httpx.AsyncClient.get', side_effect=httpx.HTTPStatusError("404", request=Mock(), response=Mock(status_code=404))):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert entries == []

    @pytest.mark.asyncio
    async def test_fetch_feed_invalid_xml(self, rss_crawler_instance):
        """测试无效XML"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "这不是有效的XML内容"

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            # feedparser应该处理无效XML，可能返回空列表或部分数据
            assert isinstance(entries, list)

    @pytest.mark.asyncio
    async def test_fetch_feed_no_items(self, rss_crawler_instance):
        """测试无新闻项的RSS"""
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>空新闻源</title>
    <description>没有新闻项</description>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_fetch_feed_malformed_entry(self, rss_crawler_instance):
        """测试格式错误的新闻项"""
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>测试新闻源</title>
    <item>
      <!-- 缺少必需的字段 -->
      <title>不完整新闻</title>
    </item>
    <item>
      <title>完整新闻</title>
      <link>http://example.com/complete</link>
      <description>完整描述</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            # 应该至少有一个有效条目
            complete_entries = [entry for entry in entries if all(key in entry for key in ['title', 'url', 'summary', 'source'])]
            assert len(complete_entries) >= 1

    @pytest.mark.asyncio
    async def test_fetch_feed_with_updated_date(self, rss_crawler_instance):
        """测试使用updated日期"""
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>测试新闻源</title>
    <item>
      <title>使用updated日期</title>
      <link>http://example.com/news</link>
      <description>新闻描述</description>
      <updated>2024-01-01T12:00:00Z</updated>
    </item>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert len(entries) == 1
            assert entries[0]["title"] == "使用updated日期"
            assert entries[0]["publish_date"] is not None

    @pytest.mark.asyncio
    async def test_fetch_feed_unicode_content(self, rss_crawler_instance):
        """测试Unicode内容"""
        mock_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Unicode新闻源</title>
    <item>
      <title>🚀 智察全球 🌍 AI技术突破</title>
      <link>http://example.com/unicode-news</link>
      <description>包含Emoji和中文的新闻摘要 🎉</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_rss_content

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")

            assert len(entries) == 1
            assert "🚀" in entries[0]["title"]
            assert "🌍" in entries[0]["title"]
            assert "AI" in entries[0]["title"]
            assert "🎉" in entries[0]["summary"]

    @pytest.mark.asyncio
    async def test_fetch_feed_error_handling(self, rss_crawler_instance):
        """测试错误处理"""
        # 测试网络错误
        with patch('httpx.AsyncClient.get', side_effect=Exception("网络错误")):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")
            assert entries == []

        # 测试空响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            entries = await rss_crawler_instance.fetch_feed("http://example.com/rss.xml")
            assert isinstance(entries, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_rss_feed():
    """集成测试：真实RSS源（仅在没有网络限制时运行）"""
    try:
        # 使用BBC RSS作为测试（稳定且可靠）
        entries = await crawler.fetch_feed("http://feeds.bbci.co.uk/news/rss.xml")

        # 验证基本结构
        assert isinstance(entries, list)

        if len(entries) > 0:
            entry = entries[0]
            assert "title" in entry
            assert "url" in entry
            assert "source" in entry
            assert entry["source"] == "BBC News"

    except Exception as e:
        # 网络问题可能失败，这是可以接受的
        pytest.skip(f"RSS测试因网络问题跳过: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_error_logging(caplog):
    """测试错误日志记录"""
    with patch('httpx.AsyncClient.get', side_effect=Exception("测试错误")):
        await crawler.fetch_feed("http://example.com/error.xml")

        # 验证错误被记录
        assert any("Error parsing feed" in record.message for record in caplog.records)
        assert any("error.xml" in record.message for record in caplog.records)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_crawler_with_redirect():
    """测试处理重定向的RSS源"""
    mock_final_response = Mock()
    mock_final_response.status_code = 200
    mock_final_response.text = '''<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>重定向后的新闻</title>
      <link>http://final-destination.com/news</link>
      <description>新闻描述</description>
    </item>
  </channel>
</rss>'''

    with patch('httpx.AsyncClient.get', return_value=mock_final_response) as mock_get:
        entries = await crawler.fetch_feed("http://redirecting-url.com/rss.xml")

        assert len(entries) == 1
        assert entries[0]["title"] == "重定向后的新闻"

        # 验证follow_redirects=True被使用
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get('follow_redirects') is True