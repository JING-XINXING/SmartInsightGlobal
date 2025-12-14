"""
用户偏好设置 API 端点
提供用户通知设置和偏好管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.db.session import get_db
from app.api.api_v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.preferences import (
    NotificationSettings,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    UserPreferences,
    UserPreferencesUpdate,
    UserPreferencesResponse
)

router = APIRouter()


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的通知设置
    """
    # 获取用户的通知设置，如果没有则返回默认值
    settings_dict = current_user.notification_settings or {}
    
    # 创建 NotificationSettings 对象，使用默认值填充缺失的字段
    settings = NotificationSettings(
        email_enabled=settings_dict.get("email_enabled", True),
        push_enabled=settings_dict.get("push_enabled", False),
        frequency=settings_dict.get("frequency", "daily"),
        news_updates=settings_dict.get("news_updates", True),
        report_ready=settings_dict.get("report_ready", True),
        system_alerts=settings_dict.get("system_alerts", True)
    )
    
    return NotificationSettingsResponse(
        success=True,
        message="获取通知设置成功",
        settings=settings
    )


@router.post("/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的通知设置
    """
    # 获取现有设置
    current_settings = current_user.notification_settings or {}
    
    # 更新设置（只更新提供的字段）
    update_data = settings_update.model_dump(exclude_unset=True)
    current_settings.update(update_data)
    
    # 保存到数据库
    current_user.notification_settings = current_settings
    await db.commit()
    await db.refresh(current_user)
    
    # 返回更新后的设置
    settings = NotificationSettings(**current_settings)
    
    return NotificationSettingsResponse(
        success=True,
        message="通知设置已更新",
        settings=settings
    )


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的偏好设置
    """
    # 获取用户的偏好设置，如果没有则返回默认值
    prefs_dict = current_user.preferences or {}
    
    # 创建 UserPreferences 对象
    preferences = UserPreferences(
        language=prefs_dict.get("language", current_user.language or "zh-CN"),
        timezone=prefs_dict.get("timezone", current_user.timezone or "Asia/Shanghai"),
        theme=prefs_dict.get("theme", "light"),
        items_per_page=prefs_dict.get("items_per_page", 20),
        default_news_category=prefs_dict.get("default_news_category")
    )
    
    return UserPreferencesResponse(
        success=True,
        message="获取用户偏好成功",
        preferences=preferences
    )


@router.post("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的偏好设置
    """
    # 获取现有偏好
    current_prefs = current_user.preferences or {}
    
    # 更新偏好（只更新提供的字段）
    update_data = preferences_update.model_dump(exclude_unset=True)
    current_prefs.update(update_data)
    
    # 同时更新用户表中的 language 和 timezone 字段
    if "language" in update_data:
        current_user.language = update_data["language"]
    if "timezone" in update_data:
        current_user.timezone = update_data["timezone"]
    
    # 保存到数据库
    current_user.preferences = current_prefs
    await db.commit()
    await db.refresh(current_user)
    
    # 返回更新后的偏好
    preferences = UserPreferences(**current_prefs)
    
    return UserPreferencesResponse(
        success=True,
        message="用户偏好已更新",
        preferences=preferences
    )
