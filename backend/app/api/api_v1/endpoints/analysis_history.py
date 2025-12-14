"""
分析历史记录 API 端点
提供分析历史的CRUD操作和导出功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import csv
import io
import logging

from app.db.session import get_db
from app.api.api_v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.analysis_history import AnalysisHistory, AnalysisExport

logger = logging.getLogger(__name__)
router = APIRouter()


# ================= Schema 定义 =================

class AnalysisHistoryItem(BaseModel):
    """分析历史记录项"""
    id: int
    title: str
    analysis_type: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    entity_count: Optional[int] = None
    trend_direction: Optional[str] = None
    processing_time: Optional[float] = None
    status: str
    is_favorite: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisHistoryDetail(BaseModel):
    """分析历史详情"""
    id: int
    title: str
    content: str
    news_id: Optional[int] = None
    analysis_type: str
    analysis_config: Optional[dict] = None
    results: dict
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    entity_count: Optional[int] = None
    main_entities: Optional[List[str]] = None
    trend_direction: Optional[str] = None
    trend_confidence: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    language: Optional[str] = None
    status: str
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisHistoryListResponse(BaseModel):
    """分析历史列表响应"""
    success: bool
    total: int
    page: int
    page_size: int
    items: List[AnalysisHistoryItem]


class AnalysisHistoryDetailResponse(BaseModel):
    """分析历史详情响应"""
    success: bool
    data: AnalysisHistoryDetail


class AnalysisStatistics(BaseModel):
    """分析统计信息"""
    total_analyses: int
    analyses_today: int
    analyses_this_week: int
    analyses_this_month: int
    by_type: dict
    average_processing_time: Optional[float] = None
    favorite_count: int


class AnalysisStatisticsResponse(BaseModel):
    """分析统计响应"""
    success: bool
    statistics: AnalysisStatistics


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(..., description="导出格式: json, csv")
    analysis_ids: Optional[List[int]] = Field(None, description="指定的分析ID列表")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    analysis_type: Optional[str] = None


# ================= API 端点 =================

@router.get("/history", response_model=AnalysisHistoryListResponse)
async def get_analysis_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    analysis_type: Optional[str] = Query(None, description="分析类型过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    is_favorite: Optional[bool] = Query(None, description="是否收藏"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的分析历史记录列表
    支持分页、过滤和搜索
    """
    try:
        # 构建查询
        query = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.is_deleted == False
        )
        
        # 应用过滤条件
        if analysis_type:
            query = query.filter(AnalysisHistory.analysis_type == analysis_type)
        
        if start_date:
            query = query.filter(AnalysisHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(AnalysisHistory.created_at <= end_date)
        
        if is_favorite is not None:
            query = query.filter(AnalysisHistory.is_favorite == is_favorite)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(AnalysisHistory.title.ilike(search_pattern))
        
        # 获取总数
        total = query.count()
        
        # 分页并排序
        items = query.order_by(desc(AnalysisHistory.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return AnalysisHistoryListResponse(
            success=True,
            total=total,
            page=page,
            page_size=page_size,
            items=[AnalysisHistoryItem.model_validate(item) for item in items]
        )
        
    except Exception as e:
        logger.error(f"获取分析历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析历史失败: {str(e)}")


@router.get("/history/{analysis_id}", response_model=AnalysisHistoryDetailResponse)
async def get_analysis_detail(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单条分析历史详情
    """
    analysis = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == analysis_id,
        AnalysisHistory.user_id == current_user.id,
        AnalysisHistory.is_deleted == False
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    
    return AnalysisHistoryDetailResponse(
        success=True,
        data=AnalysisHistoryDetail.model_validate(analysis)
    )


@router.delete("/history/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除分析历史记录（软删除）
    """
    analysis = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == analysis_id,
        AnalysisHistory.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    
    analysis.is_deleted = True
    db.commit()
    
    return {"success": True, "message": "分析记录已删除"}


@router.post("/history/{analysis_id}/favorite")
async def toggle_favorite(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    切换分析记录的收藏状态
    """
    analysis = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == analysis_id,
        AnalysisHistory.user_id == current_user.id,
        AnalysisHistory.is_deleted == False
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    
    analysis.is_favorite = not analysis.is_favorite
    db.commit()
    
    return {
        "success": True, 
        "is_favorite": analysis.is_favorite,
        "message": "已收藏" if analysis.is_favorite else "已取消收藏"
    }


@router.get("/statistics", response_model=AnalysisStatisticsResponse)
async def get_analysis_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的分析统计信息
    """
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)
        
        # 基础查询
        base_query = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.is_deleted == False
        )
        
        # 总分析数
        total_analyses = base_query.count()
        
        # 今日分析数
        analyses_today = base_query.filter(
            AnalysisHistory.created_at >= today_start
        ).count()
        
        # 本周分析数
        analyses_this_week = base_query.filter(
            AnalysisHistory.created_at >= week_start
        ).count()
        
        # 本月分析数
        analyses_this_month = base_query.filter(
            AnalysisHistory.created_at >= month_start
        ).count()
        
        # 按类型统计
        type_counts = db.query(
            AnalysisHistory.analysis_type,
            func.count(AnalysisHistory.id)
        ).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.is_deleted == False
        ).group_by(AnalysisHistory.analysis_type).all()
        
        by_type = {t: c for t, c in type_counts}
        
        # 平均处理时间
        avg_time = db.query(func.avg(AnalysisHistory.processing_time)).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.is_deleted == False,
            AnalysisHistory.processing_time.isnot(None)
        ).scalar()
        
        # 收藏数
        favorite_count = base_query.filter(
            AnalysisHistory.is_favorite == True
        ).count()
        
        return AnalysisStatisticsResponse(
            success=True,
            statistics=AnalysisStatistics(
                total_analyses=total_analyses,
                analyses_today=analyses_today,
                analyses_this_week=analyses_this_week,
                analyses_this_month=analyses_this_month,
                by_type=by_type,
                average_processing_time=round(avg_time, 2) if avg_time else None,
                favorite_count=favorite_count
            )
        )
        
    except Exception as e:
        logger.error(f"获取分析统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/export")
async def export_analysis_history(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出分析历史记录
    支持 JSON 和 CSV 格式
    """
    try:
        # 构建查询
        query = db.query(AnalysisHistory).filter(
            AnalysisHistory.user_id == current_user.id,
            AnalysisHistory.is_deleted == False
        )
        
        # 应用过滤条件
        if request.analysis_ids:
            query = query.filter(AnalysisHistory.id.in_(request.analysis_ids))
        
        if request.start_date:
            query = query.filter(AnalysisHistory.created_at >= request.start_date)
        
        if request.end_date:
            query = query.filter(AnalysisHistory.created_at <= request.end_date)
        
        if request.analysis_type:
            query = query.filter(AnalysisHistory.analysis_type == request.analysis_type)
        
        analyses = query.order_by(desc(AnalysisHistory.created_at)).all()
        
        if not analyses:
            raise HTTPException(status_code=404, detail="没有找到符合条件的分析记录")
        
        # 根据格式导出
        if request.format == "json":
            return export_as_json(analyses)
        elif request.format == "csv":
            return export_as_csv(analyses)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.format}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出分析历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def export_as_json(analyses: List[AnalysisHistory]) -> StreamingResponse:
    """导出为 JSON 格式"""
    data = []
    for analysis in analyses:
        data.append({
            "id": analysis.id,
            "title": analysis.title,
            "content": analysis.content,
            "analysis_type": analysis.analysis_type,
            "results": analysis.results,
            "sentiment_score": analysis.sentiment_score,
            "sentiment_label": analysis.sentiment_label,
            "entity_count": analysis.entity_count,
            "trend_direction": analysis.trend_direction,
            "processing_time": analysis.processing_time,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        })
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


def export_as_csv(analyses: List[AnalysisHistory]) -> StreamingResponse:
    """导出为 CSV 格式"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "ID", "标题", "分析类型", "情感分数", "情感标签", 
        "实体数量", "趋势方向", "处理时间(秒)", "创建时间"
    ])
    
    # 写入数据
    for analysis in analyses:
        writer.writerow([
            analysis.id,
            analysis.title,
            analysis.analysis_type,
            analysis.sentiment_score,
            analysis.sentiment_label,
            analysis.entity_count,
            analysis.trend_direction,
            analysis.processing_time,
            analysis.created_at.isoformat() if analysis.created_at else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM for Excel
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.delete("/history/batch")
async def batch_delete_analyses(
    analysis_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量删除分析记录
    """
    count = db.query(AnalysisHistory).filter(
        AnalysisHistory.id.in_(analysis_ids),
        AnalysisHistory.user_id == current_user.id
    ).update({"is_deleted": True}, synchronize_session=False)
    
    db.commit()
    
    return {"success": True, "deleted_count": count, "message": f"已删除 {count} 条记录"}
