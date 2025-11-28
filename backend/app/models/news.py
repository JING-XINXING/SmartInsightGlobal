from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    summary = Column(Text, nullable=True)
    source = Column(String)
    url = Column(String, unique=True, index=True)
    publish_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Analysis fields
    sentiment_score = Column(Integer, nullable=True) # -100 to 100
    keywords = Column(JSON, nullable=True)
    category = Column(String, nullable=True)

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String)
    type = Column(String) # rss, api, web
    is_active = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
