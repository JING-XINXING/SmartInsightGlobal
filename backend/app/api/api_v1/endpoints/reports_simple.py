"""
简化版报告生成API端点
避免循环依赖，提供核心报告功能
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import time

from app.core.report_generator import report_generator, ReportFormat, ReportType, ReportMetadata, ReportSection
from app.core.i18n import i18n_manager, Language
from app.core.logger import logger

router = APIRouter()


class SimpleReportRequest(BaseModel):
    """简化报告请求"""
    title: str = Field(..., description="报告标题")
    content: str = Field(..., description="报告内容")
    format: str = Field("html", pattern="^(html|markdown)$")
    language: str = Field("zh-CN", pattern="^(zh-CN|en-US)$")


class SimpleNewsReportRequest(BaseModel):
    """简化新闻分析报告请求"""
    title: str = Field(..., description="报告标题")
    format: str = Field("html", pattern="^(html|markdown)$")
    time_range: str = Field("week", pattern="^(day|week|month)$")
    language: str = Field("zh-CN", pattern="^(zh-CN|en-US)$")


@router.post("/generate-simple")
async def generate_simple_report(request: SimpleReportRequest):
    """
    生成简单报告，无需认证
    """
    try:
        logger.info(f"Generating simple report: {request.title}")

        # 解析语言
        try:
            language = i18n_manager.validate_language(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

        # 解析格式
        try:
            report_format = ReportFormat(request.format)
            if report_format == ReportFormat.PDF:
                report_format = ReportFormat.HTML  # 暂时使用HTML替代PDF
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # 创建报告章节
        section = ReportSection(
            title=request.title,
            content=request.content,
            subsections=[]
        )

        # 创建报告元数据
        metadata = ReportMetadata(
            title=request.title,
            author="SmartInsight System",
            language=language,
            report_type=ReportType.CUSTOM,
            created_at=datetime.now(timezone.utc),
            data_sources=["User Input"]
        )

        # 生成报告
        result = await report_generator.generate_report(
            metadata=metadata,
            sections=[section],
            format=report_format
        )

        return {
            "success": True,
            "message": "报告生成成功" if language == Language.CHINESE else "Report generated successfully",
            "report": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simple report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/generate-news-summary")
async def generate_news_summary_report(request: SimpleNewsReportRequest):
    """
    生成新闻摘要报告，无需认证
    """
    try:
        logger.info(f"Generating news summary report: {request.title}")

        # 解析语言
        try:
            language = i18n_manager.validate_language(request.language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

        # 解析格式
        try:
            report_format = ReportFormat(request.format)
            if report_format == ReportFormat.PDF:
                report_format = ReportFormat.HTML  # 暂时使用HTML替代PDF
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # 模拟新闻数据（实际应该从数据库获取）
        sample_news_data = [
            {
                "title": "科技新闻示例",
                "category": "科技",
                "sentiment_score": 0.2,
                "publish_date": datetime.now(timezone.utc).isoformat(),
                "summary": "这是一条关于科技创新的新闻"
            },
            {
                "title": "经济新闻示例",
                "category": "经济",
                "sentiment_score": -0.1,
                "publish_date": datetime.now(timezone.utc).isoformat(),
                "summary": "这是一条关于经济发展的新闻"
            },
            {
                "title": "社会新闻示例",
                "category": "社会",
                "sentiment_score": 0.0,
                "publish_date": datetime.now(timezone.utc).isoformat(),
                "summary": "这是一条关于社会事件的新闻"
            }
        ]

        # 创建新闻分析章节
        analysis_section = await report_generator.create_news_analysis_report(
            sample_news_data, language, request.time_range
        )

        # 创建报告元数据
        metadata = ReportMetadata(
            title=request.title,
            author="SmartInsight System",
            language=language,
            report_type=ReportType.NEWS_ANALYSIS,
            created_at=datetime.now(timezone.utc),
            time_range=request.time_range,
            data_sources=["Sample Data"]
        )

        # 生成报告
        result = await report_generator.generate_report(
            metadata=metadata,
            sections=[analysis_section],
            format=report_format
        )

        return {
            "success": True,
            "message": "新闻摘要报告生成成功" if language == Language.CHINESE else "News summary report generated successfully",
            "report": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"News summary report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """
    获取支持的报告格式
    """
    try:
        formats = []

        # 检查可用格式
        available_formats = [ReportFormat.HTML, ReportFormat.MARKDOWN]
        if report_generator.html_available:
            available_formats.append(ReportFormat.HTML)

        for format_type in available_formats:
            formats.append({
                "format": format_type.value,
                "name": format_type.value.title(),
                "available": True,
                "description": f"{format_type.value} format report"
            })

        return {
            "success": True,
            "formats": formats
        }

    except Exception as e:
        logger.error(f"Failed to get formats: {e}")
        return {
            "success": False,
            "error": str(e),
            "formats": []
        }


@router.get("/types")
async def get_report_types():
    """
    获取报告类型列表
    """
    try:
        types = []

        for report_type in ReportType:
            types.append({
                "type": report_type.value,
                "name": report_type.value.replace("_", " ").title(),
                "description": f"{report_type.value} report type"
            })

        return {
            "success": True,
            "types": types
        }

    except Exception as e:
        logger.error(f"Failed to get report types: {e}")
        return {
            "success": False,
            "error": str(e),
            "types": []
        }


@router.get("/status")
async def get_report_system_status():
    """
    获取报告生成系统状态
    """
    try:
        # 测试报告生成器
        test_metadata = ReportMetadata(
            title="Test Report",
            author="System",
            language=Language.CHINESE,
            report_type=ReportType.CUSTOM,
            created_at=datetime.now(timezone.utc),
            data_sources=["Test"]
        )

        test_section = ReportSection(
            title="Test Section",
            content="This is a test section."
        )

        # 尝试生成简单HTML报告
        test_result = await report_generator.generate_report(
            metadata=test_metadata,
            sections=[test_section],
            format=ReportFormat.HTML
        )

        return {
            "success": True,
            "status": "healthy",
            "report_generation": "working",
            "test_report_generated": test_result is not None,
            "output_directory": str(report_generator.output_dir),
            "supported_formats": ["html", "markdown"],
            "supported_types": [t.value for t in ReportType],
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Report system status check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/templates")
async def get_report_templates():
    """
    获取可用的报告模板
    """
    try:
        templates = [
            {
                "id": "news_analysis",
                "name": "新闻分析报告",
                "description": "分析新闻情感、趋势和关键信息",
                "sections": ["概览", "情感分析", "实体识别", "趋势预测", "结论"]
            },
            {
                "id": "sentiment_trend",
                "name": "情感趋势报告",
                "description": "展示情感变化趋势和预测",
                "sections": ["趋势概览", "时间序列分析", "影响因素", "预测模型", "建议"]
            },
            {
                "id": "geographic_analysis",
                "name": "地理分析报告",
                "description": "分析地理分布和热点区域",
                "sections": ["地理分布", "热点分析", "区域对比", "趋势变化", "洞察"]
            },
            {
                "id": "comprehensive",
                "name": "综合分析报告",
                "description": "全面的多维度分析报告",
                "sections": ["执行摘要", "数据概览", "情感分析", "地理分析", "趋势预测", "详细结论"]
            }
        ]

        return {
            "success": True,
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        return {
            "success": False,
            "error": str(e),
            "templates": []
        }