"""
分析历史记录 API 端点测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pydantic import BaseModel


class TestAnalysisHistorySchemas:
    """分析历史记录 Schema 测试"""

    def test_analysis_history_item_schema(self):
        """测试分析历史记录项 Schema"""
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryItem
        
        item = AnalysisHistoryItem(
            id=1,
            title="测试新闻标题",
            analysis_type="comprehensive",
            sentiment_score=45.5,
            sentiment_label="positive",
            entity_count=5,
            trend_direction="increasing",
            processing_time=2.5,
            status="completed",
            is_favorite=False,
            created_at=datetime.now()
        )
        
        assert item.id == 1
        assert item.title == "测试新闻标题"
        assert item.analysis_type == "comprehensive"
        assert item.sentiment_score == 45.5
        assert item.status == "completed"

    def test_analysis_history_detail_schema(self):
        """测试分析历史详情 Schema"""
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryDetail
        
        detail = AnalysisHistoryDetail(
            id=1,
            title="测试新闻",
            content="测试内容",
            news_id=None,
            analysis_type="sentiment",
            analysis_config={"model": "multi"},
            results={"sentiment": {"score": 50}},
            sentiment_score=50.0,
            sentiment_label="positive",
            entity_count=3,
            main_entities=["实体1", "实体2"],
            trend_direction="stable",
            trend_confidence=0.85,
            processing_time=1.5,
            model_used="llm",
            language="zh-CN",
            status="completed",
            is_favorite=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert detail.id == 1
        assert detail.main_entities == ["实体1", "实体2"]
        assert detail.trend_confidence == 0.85

    def test_analysis_statistics_schema(self):
        """测试分析统计 Schema"""
        from app.api.api_v1.endpoints.analysis_history import AnalysisStatistics
        
        stats = AnalysisStatistics(
            total_analyses=100,
            analyses_today=5,
            analyses_this_week=25,
            analyses_this_month=80,
            by_type={"comprehensive": 50, "sentiment": 30, "entities": 20},
            average_processing_time=2.1,
            favorite_count=15
        )
        
        assert stats.total_analyses == 100
        assert stats.by_type["comprehensive"] == 50
        assert stats.favorite_count == 15

    def test_export_request_schema(self):
        """测试导出请求 Schema"""
        from app.api.api_v1.endpoints.analysis_history import ExportRequest
        
        request = ExportRequest(
            format="json",
            analysis_ids=[1, 2, 3],
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            analysis_type="comprehensive"
        )
        
        assert request.format == "json"
        assert len(request.analysis_ids) == 3
        assert request.analysis_type == "comprehensive"

    def test_export_request_csv_format(self):
        """测试 CSV 格式导出请求"""
        from app.api.api_v1.endpoints.analysis_history import ExportRequest
        
        request = ExportRequest(format="csv")
        
        assert request.format == "csv"
        assert request.analysis_ids is None


class TestAnalysisHistoryListResponse:
    """分析历史列表响应测试"""

    def test_list_response_structure(self):
        """测试列表响应结构"""
        from app.api.api_v1.endpoints.analysis_history import (
            AnalysisHistoryItem, 
            AnalysisHistoryListResponse
        )
        
        items = [
            AnalysisHistoryItem(
                id=i,
                title=f"新闻{i}",
                analysis_type="comprehensive",
                status="completed",
                is_favorite=False,
                created_at=datetime.now()
            )
            for i in range(1, 6)
        ]
        
        response = AnalysisHistoryListResponse(
            success=True,
            total=100,
            page=1,
            page_size=10,
            items=items
        )
        
        assert response.success == True
        assert response.total == 100
        assert response.page == 1
        assert len(response.items) == 5


class TestAnalysisHistoryExport:
    """导出功能测试"""

    def test_export_as_json_format(self):
        """测试 JSON 导出格式"""
        from app.api.api_v1.endpoints.analysis_history import export_as_json
        
        # 创建模拟的分析历史对象
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.title = "测试新闻"
        mock_analysis.content = "测试内容"
        mock_analysis.analysis_type = "comprehensive"
        mock_analysis.results = {"sentiment": {"score": 50}}
        mock_analysis.sentiment_score = 50.0
        mock_analysis.sentiment_label = "positive"
        mock_analysis.entity_count = 3
        mock_analysis.trend_direction = "increasing"
        mock_analysis.processing_time = 2.0
        mock_analysis.created_at = datetime.now()
        
        response = export_as_json([mock_analysis])
        
        assert response.media_type == "application/json"
        assert "attachment" in response.headers.get("Content-Disposition", "")

    def test_export_as_csv_format(self):
        """测试 CSV 导出格式"""
        from app.api.api_v1.endpoints.analysis_history import export_as_csv
        
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.title = "测试新闻"
        mock_analysis.analysis_type = "comprehensive"
        mock_analysis.sentiment_score = 50.0
        mock_analysis.sentiment_label = "positive"
        mock_analysis.entity_count = 3
        mock_analysis.trend_direction = "increasing"
        mock_analysis.processing_time = 2.0
        mock_analysis.created_at = datetime.now()
        
        response = export_as_csv([mock_analysis])
        
        assert response.media_type == "text/csv"
        assert "attachment" in response.headers.get("Content-Disposition", "")


class TestAnalysisHistoryValidation:
    """分析历史验证测试"""

    def test_valid_analysis_types(self):
        """测试有效的分析类型"""
        valid_types = ["comprehensive", "sentiment", "entities", "trend"]
        
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryItem
        
        for analysis_type in valid_types:
            item = AnalysisHistoryItem(
                id=1,
                title="测试",
                analysis_type=analysis_type,
                status="completed",
                is_favorite=False,
                created_at=datetime.now()
            )
            assert item.analysis_type == analysis_type

    def test_valid_status_values(self):
        """测试有效的状态值"""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryItem
        
        for status in valid_statuses:
            item = AnalysisHistoryItem(
                id=1,
                title="测试",
                analysis_type="comprehensive",
                status=status,
                is_favorite=False,
                created_at=datetime.now()
            )
            assert item.status == status

    def test_sentiment_labels(self):
        """测试情感标签"""
        valid_labels = ["positive", "negative", "neutral"]
        
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryItem
        
        for label in valid_labels:
            item = AnalysisHistoryItem(
                id=1,
                title="测试",
                analysis_type="sentiment",
                sentiment_label=label,
                status="completed",
                is_favorite=False,
                created_at=datetime.now()
            )
            assert item.sentiment_label == label

    def test_trend_directions(self):
        """测试趋势方向"""
        valid_directions = ["increasing", "decreasing", "stable"]
        
        from app.api.api_v1.endpoints.analysis_history import AnalysisHistoryItem
        
        for direction in valid_directions:
            item = AnalysisHistoryItem(
                id=1,
                title="测试",
                analysis_type="trend",
                trend_direction=direction,
                status="completed",
                is_favorite=False,
                created_at=datetime.now()
            )
            assert item.trend_direction == direction
