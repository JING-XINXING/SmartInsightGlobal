from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# 获取项目根目录（backend 的父目录）
# 支持从任意目录启动时都能正确找到 .env 文件
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

# 如果 backend/.env 不存在，尝试项目根目录
if not ENV_FILE.exists():
    ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    应用配置类
    从 .env 文件和环境变量中读取配置
    """
    PROJECT_NAME: str = "SmartInsight Global"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "xinxingjing"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "smartinsight"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # LLM API Keys
    DEEPSEEK_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    MOONSHOT_API_KEY: Optional[str] = None
    DASHSCOPE_API_KEY: Optional[str] = None
    BAICHUAN_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    MINIMAX_API_KEY: Optional[str] = None
    DOUBAO_API_KEY: Optional[str] = None
    XUNFEI_API_KEY: Optional[str] = None
    BAIDU_API_KEY: Optional[str] = None

    class Config:
        case_sensitive = True
        # 使用绝对路径，确保从任意目录启动都能找到 .env 文件
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        # 允许 .env 中存在未定义的额外字段（忽略它们）
        extra = "ignore"

    def assemble_db_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
