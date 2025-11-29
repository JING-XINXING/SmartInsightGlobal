from fastapi import APIRouter
from app.api.api_v1.endpoints import news, llm, scheduler

api_router = APIRouter()
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
