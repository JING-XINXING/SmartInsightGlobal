"""
报告生成API端点
提供PDF、HTML、Markdown格式的分析报告生成功能
"""
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import tempfile
import os

from app.core.report_generator import report_generator, ReportFormat, ReportType, ReportMetadata, ReportSection
from app.core.i18n import i18n_manager, Language, get_current_language
from app.api.api_v1.endpoints.auth import get_current_user, require_permission
from app.models.user import User
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.news import News

router = APIRouter()


class ReportRequest(BaseModel):
    """报告生成请求模型"""
    title: str = Field(..., description="报告标题")
    report_type: str = Field(..., regex="^(news_analysis|sentiment_trend|geographic_analysis|comprehensive_report|custom)$")
    format: str = Field("html", regex="^(pdf|html|markdown)$")
    language: Optional[str] = Field(None, description="语言代码")
    time_range: Optional[str] = Field(None, description="时间范围")
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")
    include_charts: bool = Field(True, description="是否包含图表")
    include_raw_data: bool = Field(False, description="是否包含原始数据")


class NewsAnalysisReportRequest(BaseModel):
    """新闻分析报告请求"""
    title: str = Field(..., description="报告标题")
    format: str = Field("html", regex="^(pdf|html|markdown)$")
    language: Optional[str] = Field(None, description="语言代码")
    time_range: Optional[str] = Field(None, description="时间范围")
    categories: Optional[List[str]] = Field(None, description="新闻类别筛选")
    sentiment_range: Optional[List[int]] = Field(None, description="情感分数范围")


class CustomReportRequest(BaseModel):
    """自定义报告请求"""
    title: str = Field(..., description="报告标题")
    format: str = Field("html", regex="^(pdf|html|markdown)$")
    language: Optional[str] = Field(None, description="语言代码")
    sections: List[Dict[str, Any]] = Field(..., description="报告章节内容")


@router.post("/generate/news-analysis")
async def generate_news_analysis_report(
    request: NewsAnalysisReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成新闻分析报告

    需要权限: view_reports
    """
    require_permission(current_user, "view_reports")

    try:
        # 解析语言
        language = Language.CHINESE  # 默认中文
        if request.language:
            try:
                language = i18n_manager.validate_language(request.language)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

        # 解析格式
        try:
            report_format = ReportFormat(request.format)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # 构建查询
        query = select(News)

        # 应用筛选条件
        if request.categories:
            query = query.where(News.category.in_(request.categories))

        if request.sentiment_range and len(request.sentiment_range) == 2:
            min_sent, max_sent = request.sentiment_range
            query = query.where(News.sentiment_score.between(min_sent, max_sent))

        # 执行查询
        result = await db.execute(query.order_by(News.publish_date.desc()).limit(1000))
        news_items = result.scalars().all()

        if not news_items:
            raise HTTPException(status_code=404, detail="No news data found for the specified criteria")

        # 准备新闻数据
        news_data = []
        for news in news_items:
            news_data.append({
                "id": news.id,
                "title": news.title,
                "category": news.category,
                "sentiment_score": news.sentiment_score,
                "publish_date": news.publish_date.isoformat() if news.publish_date else None,
                "source": news.source
            })

        # 创建报告元数据
        metadata = ReportMetadata(
            title=request.title,
            author=current_user.username,
            language=language,
            report_type=ReportType.NEWS_ANALYSIS,
            created_at=datetime.now(timezone.utc),
            time_range=request.time_range,
            filters={
                "categories": request.categories,
                "sentiment_range": request.sentiment_range
            },
            data_sources=["News Database"]
        )

        # 创建分析章节
        analysis_section = await report_generator.create_news_analysis_report(
            news_data, language, request.time_range
        )

        # 生成报告
        result = await report_generator.generate_report(
            metadata=metadata,
            sections=[analysis_section],
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
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/generate/sentiment-trend")
async def generate_sentiment_trend_report(
    title: str = Field(..., description="报告标题"),
    format: str = Field("html", regex="^(pdf|html|markdown)$"),
    language: Optional[str] = Field(None, description="语言代码"),
    time_range: str = Field("week", regex="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_user)
):
    """
    生成情感趋势报告

    需要权限: view_reports
    """
    require_permission(current_user, "view_reports")

    try:
        # 解析参数
        target_language = Language.CHINESE
        if language:
            try:
                target_language = i18n_manager.validate_language(language)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

        report_format = ReportFormat(format)

        # 模拟趋势数据（实际应该从数据库获取）
        trend_data = []
        import random
        from datetime import datetime, timedelta

        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        for i in range(7):
            trend_data.append({
                "timestamp": (base_time + timedelta(days=i)).isoformat(),
                "avg_sentiment": random.uniform(-30, 30),
                "location_count": random.randint(10, 100),
                "top_categories": [
                    {"category": "科技", "count": random.randint(5, 20)},
                    {"category": "经济", "count": random.randint(3, 15)}
                ]
            })

        # 创建报告元数据
        metadata = ReportMetadata(
            title=title,
            author=current_user.username,
            language=target_language,
            report_type=ReportType.SENTIMENT_TREND,
            created_at=datetime.now(timezone.utc),
            time_range=time_range,
            data_sources=["News Database", "Sentiment Analysis"]
        )

        # 创建趋势分析章节
        trend_section = await report_generator.create_sentiment_trend_report(
            trend_data, target_language
        )

        # 生成报告
        result = await report_generator.generate_report(
            metadata=metadata,
            sections=[trend_section],
            format=report_format
        )

        return {
            "success": True,
            "message": "情感趋势报告生成成功" if target_language == Language.CHINESE else "Sentiment trend report generated successfully",
            "report": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment trend report generation failed: {str(e)}")


@router.post("/generate/custom")
async def generate_custom_report(
    request: CustomReportRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成自定义报告

    需要权限: view_reports
    """
    require_permission(current_user, "view_reports")

    try:
        # 解析语言
        language = Language.CHINESE
        if request.language:
            try:
                language = i18n_manager.validate_language(request.language)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

        # 解析格式
        try:
            report_format = ReportFormat(request.format)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # 创建报告章节
        sections = []
        for section_data in request.sections:
            section = ReportSection(
                title=section_data.get("title", ""),
                content=section_data.get("content", ""),
                subsections=[
                    ReportSection(
                        title=sub.get("title", ""),
                        content=sub.get("content", "")
                    )
                    for sub in section_data.get("subsections", [])
                ]
            )
            sections.append(section)

        # 创建报告元数据
        metadata = ReportMetadata(
            title=request.title,
            author=current_user.username,
            language=language,
            report_type=ReportType.CUSTOM,
            created_at=datetime.now(timezone.utc),
            data_sources=["Custom Input"]
        )

        # 生成报告
        result = await report_generator.generate_report(
            metadata=metadata,
            sections=sections,
            format=report_format
        )

        return {
            "success": True,
            "message": "自定义报告生成成功" if language == Language.CHINESE else "Custom report generated successfully",
            "report": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom report generation failed: {str(e)}")


@router.get("/download/{filename}")
async def download_report(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载报告文件

    需要权限: view_reports
    """
    require_permission(current_user, "view_reports")

    try:
        # 安全检查文件名
        if not filename or ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = report_generator.output_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        # 确定媒体类型
        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".html"):
            media_type = "text/html"
        elif filename.endswith(".md"):
            media_type = "text/markdown"
        else:
            media_type = "application/octet-stream"

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report download failed: {str(e)}")


@router.get("/list")
async def list_reports(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制")
):
    """
    列出可用的报告文件

    需要权限: view_reports
    """
    require_permission(current_user, "view_reports")

    try:
        reports = []
        output_dir = report_generator.output_dir

        if output_dir.exists():
            # 获取所有报告文件
            for file_path in output_dir.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    reports.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                        "format": file_path.suffix[1:] if file_path.suffix else "unknown"
                    })

        # 按创建时间倒序排序
        reports.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "success": True,
            "reports": reports[:limit],
            "total": len(reports)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.delete("/{filename}")
async def delete_report(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除报告文件

    需要权限: manage_reports
    """
    require_permission(current_user, "manage_reports")

    try:
        # 安全检查文件名
        if not filename or ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = report_generator.output_dir / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")

        # 删除文件
        file_path.unlink()

        return {
            "success": True,
            "message": "报告删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """
    获取支持的报告格式

    Returns:
        支持的格式列表
    """
    formats = []

    for format_type in ReportFormat:
        is_available = True
        if format_type == ReportFormat.PDF and not report_generator.pdf_available:
            is_available = False
        elif format_type == ReportFormat.HTML and not report_generator.html_available:
            is_available = False

        formats.append({
            "format": format_type.value,
            "name": format_type.value.title(),
            "available": is_available,
            "description": f"{format_type.value} format report"
        })

    return {
        "success": True,
        "formats": formats
    }


@router.get("/types")
async def get_report_types():
    """
    获取报告类型列表

    Returns:
        报告类型列表
    """
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


@router.get("/status")
async def get_report_generation_status():
    """
    获取报告生成状态

    Returns:
        系统状态信息
    """
    return {
        "success": True,
        "status": {
            "pdf_generation": report_generator.pdf_available,
            "html_generation": report_generator.html_available,
            "markdown_generation": True,
            "output_directory": str(report_generator.output_dir),
            "supported_formats": [f.value for f in ReportFormat],
            "supported_types": [t.value for t in ReportType]
        },
        "dependencies": {
            "reportlab": report_generator.pdf_available,
            "jinja2": report_generator.html_available
        }
    }