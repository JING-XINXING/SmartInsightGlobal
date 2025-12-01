"""
测试新闻分析引擎
"""
import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
from app.core.analyzer import news_analyzer, NewsAnalyzer


@pytest.mark.unit
class TestNewsAnalyzer:
    """测试新闻分析器"""

    @pytest.fixture
    def mock_llm_client(self, monkeypatch):
        """模拟LLM客户端"""
        mock_client = Mock()
        mock_client.get_available_providers.return_value = ["deepseek", "moonshot"]
        mock_client.chat_completion = AsyncMock()
        monkeypatch.setattr("app.core.analyzer.llm_client", mock_client)
        return mock_client

    @pytest.mark.asyncio
    async def test_sentiment_analysis_positive(self, mock_llm_client):
        """测试正面情感分析"""
        # 模拟正面情感回复
        mock_llm_client.chat_completion.return_value = "75"

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment(
            "全球经济复苏加速",
            "最新经济数据显示，全球主要经济体在第三季度表现强劲，市场信心大幅提升..."
        )

        assert score == 75
        mock_llm_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_sentiment_analysis_negative(self, mock_llm_client):
        """测试负面情感分析"""
        # 模拟负面情感回复
        mock_llm_client.chat_completion.return_value = "-80"

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment(
            "自然灾害造成重大损失",
            "地震导致数百人遇难，经济损失严重，救援工作正在紧急进行..."
        )

        assert score == -80
        mock_llm_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_sentiment_analysis_neutral(self, mock_llm_client):
        """测试中性情感分析"""
        # 模拟中性情感回复
        mock_llm_client.chat_completion.return_value = "5"

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment(
            "政府召开例行会议",
            "今天上午，政府召开了季度例行工作会议..."
        )

        assert score == 5

    @pytest.mark.asyncio
    async def test_sentiment_analysis_no_response(self, mock_llm_client):
        """测试LLM无响应情况"""
        # 模拟无响应
        mock_llm_client.chat_completion.return_value = None

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment("测试标题", "测试内容")

        assert score is None

    @pytest.mark.asyncio
    async def test_sentiment_analysis_exception(self, mock_llm_client):
        """测试LLM异常情况"""
        # 模拟异常
        mock_llm_client.chat_completion.side_effect = Exception("API错误")

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment("测试标题", "测试内容")

        assert score is None

    @pytest.mark.asyncio
    async def test_sentiment_score_clamping(self, mock_llm_client):
        """测试情感分数范围限制"""
        # 测试超出范围的分数
        mock_llm_client.chat_completion.return_value = "150"  # 超过100

        analyzer = NewsAnalyzer()
        score = await analyzer.analyze_sentiment("测试", "测试")

        assert score == 100  # 应该被限制在100

        # 测试低于范围的分数
        mock_llm_client.chat_completion.return_value = "-150"  # 低于-100
        score = await analyzer.analyze_sentiment("测试", "测试")

        assert score == -100  # 应该被限制在-100

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, mock_llm_client):
        """测试关键词提取"""
        # 模拟关键词提取回复
        mock_llm_client.chat_completion.return_value = '["AI", "技术", "创新", "未来", "发展"]'

        analyzer = NewsAnalyzer()
        keywords = await analyzer.extract_keywords(
            "人工智能技术取得重大突破",
            "最新研究显示，AI在多个领域实现了技术突破，未来发展前景广阔..."
        )

        assert keywords == ["AI", "技术", "创新", "未来", "发展"]
        assert len(keywords) == 5

    @pytest.mark.asyncio
    async def test_keyword_extraction_invalid_json(self, mock_llm_client):
        """测试关键词提取无效JSON"""
        # 模拟无效JSON响应
        mock_llm_client.chat_completion.return_value = "AI, 技术, 创新"  # 不是JSON格式

        analyzer = NewsAnalyzer()
        keywords = await analyzer.extract_keywords("测试", "测试")

        assert keywords is None

    @pytest.mark.asyncio
    async def test_news_categorization(self, mock_llm_client):
        """测试新闻分类"""
        # 模拟分类回复
        mock_llm_client.chat_completion.return_value = "科技"

        analyzer = NewsAnalyzer()
        category = await analyzer.categorize_news(
            "AI技术突破",
            "人工智能在医疗领域取得重大进展..."
        )

        assert category == "科技"

    @pytest.mark.asyncio
    async def test_news_categorization_fallback(self, mock_llm_client):
        """测试新闻分类回退情况"""
        # 模拟无匹配分类
        mock_llm_client.chat_completion.return_value = "未知类别"

        analyzer = NewsAnalyzer()
        category = await analyzer.categorize_news("测试", "测试")

        assert category == "其他"  # 应该回退到默认类别

    @pytest.mark.asyncio
    async def test_location_extraction(self, mock_llm_client):
        """测试地理位置提取"""
        # 模拟位置提取回复
        mock_llm_client.chat_completion.return_value = '''{
            "country": "美国",
            "country_cn": "美国",
            "city": "旧金山",
            "lat": 37.7749,
            "lng": -122.4194
        }'''

        analyzer = NewsAnalyzer()
        location = await analyzer.extract_location(
            "美国旧金山科技公司发布新产品",
            "位于硅谷的科技公司今日发布..."
        )

        assert location["country"] == "美国"
        assert location["country_cn"] == "美国"
        assert location["city"] == "旧金山"
        assert location["lat"] == 37.7749
        assert location["lng"] == -122.4194

    @pytest.mark.asyncio
    async def test_location_extraction_no_location(self, mock_llm_client):
        """测试地理位置提取无位置信息"""
        # 模拟无位置信息回复
        mock_llm_client.chat_completion.return_value = '''{
            "country": "",
            "country_cn": "",
            "city": "",
            "lat": 0,
            "lng": 0
        }'''

        analyzer = NewsAnalyzer()
        location = await analyzer.extract_location("纯文本新闻", "无地理信息内容")

        # 空位置应该返回None
        assert location is None

    @pytest.mark.asyncio
    async def test_full_analysis(self, mock_llm_client):
        """测试完整新闻分析"""
        # 设置不同的响应
        def mock_chat_completion(*args, **kwargs):
            messages = kwargs.get("messages", [])
            content = messages[-1]["content"].lower() if messages else ""

            if "情感" in content:
                return "60"
            elif "关键词" in content:
                return '["技术", "AI", "创新"]'
            elif "分类" in content:
                return "科技"
            elif "地理位置" in content:
                return '''{
                    "country": "中国",
                    "country_cn": "中国",
                    "city": "北京",
                    "lat": 39.9042,
                    "lng": 116.4074
                }'''
            return None

        mock_llm_client.chat_completion.side_effect = mock_chat_completion

        analyzer = NewsAnalyzer()
        results = await analyzer.analyze_news_full(
            "AI技术在中国北京取得突破",
            "中国北京的研究团队在人工智能领域取得重大进展...",
            extract_location=True
        )

        # 验证所有分析结果
        assert results["sentiment_score"] == 60
        assert results["keywords"] == ["技术", "AI", "创新"]
        assert results["category"] == "科技"
        assert results["location"]["country"] == "中国"
        assert results["location"]["city"] == "北京"

    @pytest.mark.asyncio
    async def test_full_analysis_parallel_execution(self, mock_llm_client):
        """测试完整分析的并行执行"""
        call_count = 0

        def mock_chat_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # 模拟一些延迟
            await asyncio.sleep(0.1)
            return f"response_{call_count}"

        mock_llm_client.chat_completion.side_effect = mock_chat_completion

        analyzer = NewsAnalyzer()
        start_time = asyncio.get_event_loop().time()
        results = await analyzer.analyze_news_full("测试标题", "测试内容")
        end_time = asyncio.get_event_loop().time()

        # 并行执行应该比串行快
        execution_time = end_time - start_time
        assert execution_time < 0.3  # 应该小于3个0.1秒的串行时间

        # 验证所有方法都被调用
        assert mock_llm_client.chat_completion.call_count >= 3

    @pytest.mark.asyncio
    async def test_analyze_with_empty_content(self, mock_llm_client):
        """测试空内容的分析处理"""
        mock_llm_client.chat_completion.return_value = "50"

        analyzer = NewsAnalyzer()

        # 测试空标题
        score = await analyzer.analyze_sentiment("", "有内容")
        assert score == 50

        # 测试空内容
        score = await analyzer.analyze_sentiment("有标题", "")
        assert score == 50

        # 测试都为空
        score = await analyzer.analyze_sentiment("", "")
        assert score == 50