"""
SmartInsight Global - 全球智能情报分析系统
后端 API 服务入口
版本: V1.7.0
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.exceptions import error_body, register_exception_handlers
from app.core.rate_limit import limiter
from app.core.version import APP_NAME, APP_VERSION

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
当前版本: V1.7.0
    """,
    version=APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件配置
# 开发端口避开 3000/8000。前端默认 18421，后端默认 18080。
cors_origins = [
    "http://localhost:18421",
    "http://127.0.0.1:18421",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 统一错误响应与按 IP 限流（默认 120 次/分钟）
register_exception_handlers(app)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """限流时返回统一错误结构。"""
    return JSONResponse(
        status_code=429,
        content=error_body(429, "请求过于频繁，请稍后再试", None),
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
        "message": f"Welcome to {APP_NAME} API",
        "version": APP_VERSION,
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
        "version": APP_VERSION,
        "service": "smartinsight-backend"
    }


@app.get(f"{settings.API_V1_STR}/meta/version", tags=["Meta"])
async def meta_version():
    """返回服务名称与版本，供前端和发布检查使用。"""
    return {"name": APP_NAME, "version": APP_VERSION}
