from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class NewsBase(BaseModel):
    title: str
    content: str
    source: str
    url: str
    publish_date: Optional[datetime] = None

class NewsCreate(NewsBase):
    summary: Optional[str] = None

class LocationInfo(BaseModel):
    """地理位置信息"""
    country: str = ""
    country_cn: str = ""
    city: str = ""
    lat: float = 0
    lng: float = 0

class News(NewsBase):
    id: int
    created_at: datetime
    summary: Optional[str] = None
    sentiment_score: Optional[int] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class NewsMapItem(BaseModel):
    """地图上显示的新闻项"""
    id: int
    title: str
    source: str
    category: Optional[str] = None
    sentiment_score: Optional[int] = None
    location: LocationInfo
    publish_date: datetime
