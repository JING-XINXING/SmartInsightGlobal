"""
分析历史记录模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=True, index=True)
    
    # 基础信息
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    
    # 分析配置
    analysis_type = Column(String(50), nullable=False, index=True)  # comprehensive, sentiment, etc.
    analysis_config = Column(JSON, nullable=True)  # 参数配置
    model_used = Column(String(50), nullable=True)
    language = Column(String(10), default="zh-CN")
    
    # 分析结果 (完整JSON)
    results = Column(JSON, nullable=True)
    
    # 关键指标 (提取以便快速查询)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    entity_count = Column(Integer, default=0)
    trend_direction = Column(String(20), nullable=True)
    trend_confidence = Column(Float, nullable=True)
    
    # 元数据
    processing_time = Column(Float, nullable=True)  # 秒
    status = Column(String(20), default="completed")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 用户交互
    is_favorite = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    # user = relationship("User", back_populates="analyses") # 需要在 User 模型中添加 analyses
    # news = relationship("News")
    
    def __repr__(self):
        return f"<AnalysisHistory(id={self.id}, title={self.title}, type={self.analysis_type})>"

class AnalysisExport(Base):
    """导出记录"""
    __tablename__ = "analysis_exports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    format = Column(String(10), nullable=False)  # json, csv, pdf
    file_path = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
