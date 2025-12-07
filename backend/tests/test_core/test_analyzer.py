"""
AI 分析引擎单元测试
测试目标覆盖率: 90%+
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.analyzer import NewsAnalyzer


class TestNewsAnalyzer:
    """新闻分析器测试类"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return NewsAnalyzer()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_analysis_positive(self, analyzer, mock_llm_response):
        """测试正面情感分析"""
        # 模拟 LLM 客户端返回正面情感
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "75"
            
            score = await analyzer.analyze_sentiment(
                "Global economy shows strong recovery",
                "Economic indicators point to robust growth across major markets..."
            )
            
            assert score > 50, "正面新闻应该有正面情感分数"
            assert score <= 100, "情感分数不应超过100"
            mock_chat.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_analysis_negative(self, analyzer):
        """测试负面情感分析"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "-65"
            
            score = await analyzer.analyze_sentiment(
                "Natural disaster causes major casualties",
                "Earthquake results in hundreds of deaths and widespread destruction..."
            )
            
            assert score < -50, "负面新闻应该有负面情感分数"
            assert score >= -100, "情感分数不应低于-100"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_analysis_neutral(self, analyzer):
        """测试中性情感分析"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"sentiment_score": 5}'
            
            score = await analyzer.analyze_sentiment(
                "Government announces new policy",
                "The government has announced a new policy regarding..."
            )
            
            assert -20 <= score <= 20, "中性新闻应该有接近0的情感分数"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_keyword_extraction(self, analyzer):
        """测试关键词提取"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"keywords": ["AI", "technology", "innovation", "breakthrough"]}'
            
            keywords = await analyzer.extract_keywords(
                "AI Technology Breakthrough",
                "Artificial intelligence achieves major breakthrough in medical research..."
            )
            
            assert isinstance(keywords, list), "关键词应该是列表"
            assert len(keywords) >= 3, "应该至少提取3个关键词"
            assert len(keywords) <= 5, "关键词不应超过5个"
            assert "AI" in [k.lower() for k in keywords] or "technology" in [k.lower() for k in keywords]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_keyword_extraction_empty_content(self, analyzer):
        """测试空内容的关键词提取"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '[]'
            keywords = await analyzer.extract_keywords("", "")
            assert keywords == [], "空内容应返回空列表"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_categorize_news(self, analyzer):

        """测试新闻分类"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"category": "科技"}'
            
            category = await analyzer.categorize_news(
                "New AI Model Released",
                "Tech company releases advanced AI model..."
            )
            
            assert category in [
                "政治", "经济", "军事", "科技", "社会", "文化", 
                "体育", "健康", "环境", "灾难", "国际关系", "其他"
            ], "分类应该在预定义类别中"
            assert category == "科技"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_categorize_news_invalid_response(self, analyzer):
        """测试无效响应的新闻分类"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"category": "InvalidCategory"}'
            
            category = await analyzer.categorize_news(
                "Test Article",
                "Test content..."
            )
            
            assert category == "其他", "无效分类应降级为'Other'"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_extract_location(self, analyzer):
        """测试地理位置提取"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = '{"country": "United States", "city": "New York"}'
            
            location = await analyzer.extract_location(
                "New York City News",
                "Events in New York City, United States..."
            )
            
            assert isinstance(location, dict), "位置应该是字典"
            assert "country" in location, "应该包含国家信息"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_news_complete(self, analyzer):
        """测试完整的新闻分析流程"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            # 模拟多次调用返回不同结果
            mock_chat.side_effect = [
                '{"sentiment_score": 60}',
                '{"keywords": ["economy", "growth", "market"]}',
                '{"category": "经济"}',
                '{"country": "China", "city": "Beijing"}'
            ]
            
            result = await analyzer.analyze_news_full(
                title="Economic Growth Accelerates",
                content="China's economy shows strong growth in major cities like Beijing...",
                extract_location=True
            )
            
            assert "sentiment_score" in result
            assert "keywords" in result
            assert "category" in result
            assert "location" in result
            assert result["sentiment_score"] > 0
            assert len(result["keywords"]) >= 3
            assert result["category"] == "经济"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_analyze_news_error_handling(self, analyzer):
        """测试分析过程中的错误处理"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            # 模拟 API 错误
            mock_chat.side_effect = Exception("API Error")
            
            result = await analyzer.analyze_news_full(
                title="Test Article",
                content="Test content...",
                extract_location=False
            )
            
            # 应该返回默认值而不是抛出异常
            assert result["sentiment_score"] == None
            assert result["keywords"] == None
            assert result["category"] == "其他"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_batch_analyze(self, analyzer):
        """测试批量分析"""
        news_list = [
            {"title": "Article 1", "content": "Content 1"},
            {"title": "Article 2", "content": "Content 2"},
            {"title": "Article 3", "content": "Content 3"},
        ]
        
        with patch.object(analyzer, 'analyze_news_full', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "sentiment_score": 50,
                "keywords": ["test"],
                "category": "Other",
                "location": None
            }
            
            results = await analyzer.batch_analyze(news_list, batch_size=2)
            
            assert len(results) == 3
            assert mock_analyze.call_count == 3
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_score_bounds(self, analyzer):
        """测试情感分数边界处理"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            # 测试超出范围的分数
            mock_chat.return_value = '{"sentiment_score": 150}'
            
            score = await analyzer.analyze_sentiment("Test", "Test content")
            
            # 应该被限制在有效范围内
            assert -100 <= score <= 100
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_json_parsing_error(self, analyzer):
        """测试 JSON 解析错误处理"""
        with patch('app.core.analyzer.llm_client.chat_completion', new_callable=AsyncMock) as mock_chat:
            # 返回无效的 JSON
            mock_chat.return_value = 'Invalid JSON {{'
            
            score = await analyzer.analyze_sentiment("Test", "Test content")
            
            # 应该返回默认值
            assert score == None