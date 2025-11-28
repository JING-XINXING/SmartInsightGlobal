from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartInsight Global"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "xinxingjing"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "smartinsight"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # LLM API Keys
    DEEPSEEK_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"

    def assemble_db_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
