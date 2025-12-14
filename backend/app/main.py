"""
SmartInsight Global - 全球智能情报分析系统
后端 API 服务入口
版本: V1.5.0
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.api_v1.api import api_router
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的处理"""
    logger.info("SmartInsight Global API 启动中...")
    yield
    logger.info("SmartInsight Global API 关闭中...")

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
## SmartInsight Global - 全球智能情报分析系统

### 功能模块

* **新闻采集** - RSS/API/爬虫多源采集
* **智能分析** - 情感分析、实体识别、趋势预测
* **地图可视化** - 全球新闻热点地图
* **报告生成** - 自动化分析报告
* **用户管理** - 认证、授权、偏好设置

### API 版本
当前版本: V1.5.0
    """,
    version="1.5.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件配置
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root():
    """
    API 根路径
    返回欢迎信息和基本版本信息
    """
    return {
        "message": "Welcome to SmartInsight Global API",
        "version": "1.5.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康检查端点
    用于容器编排和负载均衡器检查服务状态
    """
    return {
        "status": "healthy",
        "version": "1.5.0",
        "service": "smartinsight-backend"
    }
