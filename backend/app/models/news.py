from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
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

    # 基础分析字段
    sentiment_score = Column(Integer, nullable=True) # -100 to 100
    sentiment_confidence = Column(Float, nullable=True)  # 情感分析置信度 0-1
    keywords = Column(JSON, nullable=True)
    category = Column(String, nullable=True)
    location = Column(JSON, nullable=True)  # {"country": "...", "city": "...", "lat": ..., "lng": ...}

    # 高级NLP分析字段
    sentiment_details = Column(JSON, nullable=True)  # 多模型情感分析详情
    entities = Column(JSON, nullable=True)  # 实体识别结果
    relations = Column(JSON, nullable=True)  # 实体关系
    emotions = Column(JSON, nullable=True)  # 细粒度情感分析

    # 情感预测字段
    sentiment_trend = Column(String, nullable=True)  # "improving", "declining", "stable"
    trend_confidence = Column(Float, nullable=True)  # 趋势预测置信度
    trend_horizon = Column(String, nullable=True)  # "short_term", "medium_term", "long_term"
    trend_factors = Column(JSON, nullable=True)  # 影响趋势的因素

    # 文本特征字段
    text_length = Column(Integer, nullable=True)  # 文本长度
    language = Column(String, nullable=True)  # 检测到的语言
    readability_score = Column(Float, nullable=True)  # 可读性分数

    # 高级分类和标签
    subcategory = Column(String, nullable=True)  # 子分类
    tags = Column(JSON, nullable=True)  # 标签列表
    topics = Column(JSON, nullable=True)  # 主题标签

    # 分析质量评估
    analysis_quality = Column(Float, nullable=True)  # 分析质量评分 0-1
    analysis_version = Column(String, nullable=True)  # 分析模型版本
    analysis_time = Column(Float, nullable=True)  # 分析耗时（秒）

    # 原始数据备份
    raw_analysis_data = Column(JSON, nullable=True)  # 完整的原始分析结果

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String)
    type = Column(String) # rss, api, web
    is_active = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
