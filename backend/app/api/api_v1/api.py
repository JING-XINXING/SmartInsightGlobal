"""API v1 路由聚合。

V1.6 起只挂载完整实现，不再挂载 *_simple 副本。
地图、认证、国际化、高级分析和分析历史都走正式模块。
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    advanced_analysis,
    analysis_history,
    auth,
    events,
    i18n,
    llm,
    map,
    news,
    preferences,
    reports,
    scheduler,
)

api_router = APIRouter()

# 核心功能端点
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(map.router, prefix="/map", tags=["map"])
api_router.include_router(events.router, prefix="/events", tags=["events"])

# 认证与国际化
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(i18n.router, prefix="/i18n", tags=["internationalization"])

# 高级分析、报告与历史记录共用 /analysis 前缀，路径互不重叠
api_router.include_router(advanced_analysis.router, prefix="/analysis", tags=["advanced_analysis"])
api_router.include_router(reports.router, prefix="/reports", tags=["report_generation"])
api_router.include_router(analysis_history.router, prefix="/analysis", tags=["analysis_history"])

# 用户偏好
api_router.include_router(preferences.router, prefix="/preferences", tags=["user_preferences"])
