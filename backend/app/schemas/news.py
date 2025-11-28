from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class NewsBase(BaseModel):
    title: str
    content: str
    source: str
    url: str
    publish_date: Optional[datetime] = None

class NewsCreate(NewsBase):
    summary: Optional[str] = None

class News(NewsBase):
    id: int
    created_at: datetime
    summary: Optional[str] = None
    sentiment_score: Optional[int] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True
