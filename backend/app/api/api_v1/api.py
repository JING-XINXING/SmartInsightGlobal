from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    news, llm, scheduler, map_simple, events, auth_simple, i18n_simple,
    advanced_analysis_simple, reports
)

api_router = APIRouter()

# 核心功能端点
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(map_simple.router, prefix="/map", tags=["map"])
api_router.include_router(events.router, prefix="/events", tags=["events"])

# V1.3新增端点
api_router.include_router(auth_simple.router, prefix="/auth", tags=["authentication"])
api_router.include_router(i18n_simple.router, prefix="/i18n", tags=["internationalization"])

# V1.3高级分析和报告端点（简化版，避免循环依赖）
api_router.include_router(advanced_analysis_simple.router, prefix="/analysis", tags=["advanced_analysis"])
api_router.include_router(reports.router, prefix="/reports", tags=["report_generation"])
