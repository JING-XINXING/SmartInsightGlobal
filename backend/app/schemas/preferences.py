"""
用户偏好设置相关的 Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationSettings(BaseModel):
    """通知设置"""
    email_enabled: bool = Field(default=True, description="是否启用邮件通知")
    push_enabled: bool = Field(default=False, description="是否启用推送通知")
    frequency: str = Field(default="daily", description="通知频率: instant, hourly, daily, weekly")
    news_updates: bool = Field(default=True, description="新闻更新通知")
    report_ready: bool = Field(default=True, description="报告生成完成通知")
    system_alerts: bool = Field(default=True, description="系统警报通知")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email_enabled": True,
                "push_enabled": False,
                "frequency": "daily",
                "news_updates": True,
                "report_ready": True,
                "system_alerts": True
            }
        }


class UserPreferences(BaseModel):
    """用户偏好设置"""
    language: str = Field(default="zh-CN", description="界面语言")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    theme: str = Field(default="light", description="主题: light, dark, auto")
    items_per_page: int = Field(default=20, description="每页显示条数")
    default_news_category: Optional[str] = Field(default=None, description="默认新闻分类")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "zh-CN",
                "timezone": "Asia/Shanghai",
                "theme": "light",
                "items_per_page": 20,
                "default_news_category": "all"
            }
        }


class NotificationSettingsUpdate(BaseModel):
    """更新通知设置请求"""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    frequency: Optional[str] = None
    news_updates: Optional[bool] = None
    report_ready: Optional[bool] = None
    system_alerts: Optional[bool] = None


class UserPreferencesUpdate(BaseModel):
    """更新用户偏好请求"""
    language: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    items_per_page: Optional[int] = None
    default_news_category: Optional[str] = None


class NotificationSettingsResponse(BaseModel):
    """通知设置响应"""
    success: bool
    message: str
    settings: NotificationSettings
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "通知设置已更新",
                "settings": {
                    "email_enabled": True,
                    "push_enabled": False,
                    "frequency": "daily",
                    "news_updates": True,
                    "report_ready": True,
                    "system_alerts": True
                }
            }
        }


class UserPreferencesResponse(BaseModel):
    """用户偏好响应"""
    success: bool
    message: str
    preferences: UserPreferences
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "用户偏好已更新",
                "preferences": {
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai",
                    "theme": "light",
                    "items_per_page": 20,
                    "default_news_category": "all"
                }
            }
        }
