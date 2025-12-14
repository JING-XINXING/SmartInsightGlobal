"""
用户偏好设置 API 端点测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Mock 用户对象
class MockUser:
    def __init__(self):
        self.id = 1
        self.username = "testuser"
        self.email = "test@example.com"
        self.role = "analyst"
        self.notification_settings = {
            "email_enabled": True,
            "push_enabled": False,
            "frequency": "daily",
            "news_updates": True,
            "report_ready": True,
            "system_alerts": True
        }
        self.preferences = {
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
            "theme": "light",
            "items_per_page": 20
        }
        self.language = "zh-CN"
        self.timezone = "Asia/Shanghai"


class TestNotificationSettings:
    """通知设置测试"""

    def test_get_notification_settings_default(self):
        """测试获取默认通知设置"""
        from app.schemas.preferences import NotificationSettings
        
        settings = NotificationSettings()
        
        assert settings.email_enabled == True
        assert settings.push_enabled == False
        assert settings.frequency == "daily"
        assert settings.news_updates == True
        assert settings.report_ready == True
        assert settings.system_alerts == True

    def test_notification_settings_update_schema(self):
        """测试通知设置更新 Schema"""
        from app.schemas.preferences import NotificationSettingsUpdate
        
        update = NotificationSettingsUpdate(
            email_enabled=False,
            frequency="hourly"
        )
        
        assert update.email_enabled == False
        assert update.frequency == "hourly"
        assert update.push_enabled is None  # 未设置的字段应为 None

    def test_notification_settings_response(self):
        """测试通知设置响应模型"""
        from app.schemas.preferences import NotificationSettings, NotificationSettingsResponse
        
        settings = NotificationSettings()
        response = NotificationSettingsResponse(
            success=True,
            message="获取成功",
            settings=settings
        )
        
        assert response.success == True
        assert response.message == "获取成功"
        assert response.settings.email_enabled == True


class TestUserPreferences:
    """用户偏好设置测试"""

    def test_get_user_preferences_default(self):
        """测试获取默认用户偏好"""
        from app.schemas.preferences import UserPreferences
        
        prefs = UserPreferences()
        
        assert prefs.language == "zh-CN"
        assert prefs.timezone == "Asia/Shanghai"
        assert prefs.theme == "light"
        assert prefs.items_per_page == 20
        assert prefs.default_news_category is None

    def test_user_preferences_update_schema(self):
        """测试用户偏好更新 Schema"""
        from app.schemas.preferences import UserPreferencesUpdate
        
        update = UserPreferencesUpdate(
            language="en-US",
            theme="dark"
        )
        
        assert update.language == "en-US"
        assert update.theme == "dark"
        assert update.timezone is None  # 未设置的字段应为 None

    def test_user_preferences_response(self):
        """测试用户偏好响应模型"""
        from app.schemas.preferences import UserPreferences, UserPreferencesResponse
        
        prefs = UserPreferences()
        response = UserPreferencesResponse(
            success=True,
            message="获取成功",
            preferences=prefs
        )
        
        assert response.success == True
        assert response.preferences.language == "zh-CN"


class TestPreferencesValidation:
    """偏好设置验证测试"""

    def test_notification_frequency_valid_values(self):
        """测试通知频率有效值"""
        from app.schemas.preferences import NotificationSettingsUpdate
        
        valid_frequencies = ["realtime", "hourly", "daily", "weekly"]
        
        for freq in valid_frequencies:
            update = NotificationSettingsUpdate(frequency=freq)
            assert update.frequency == freq

    def test_theme_valid_values(self):
        """测试主题有效值"""
        from app.schemas.preferences import UserPreferencesUpdate
        
        valid_themes = ["light", "dark", "system"]
        
        for theme in valid_themes:
            update = UserPreferencesUpdate(theme=theme)
            assert update.theme == theme

    def test_items_per_page_range(self):
        """测试每页条目数范围"""
        from app.schemas.preferences import UserPreferencesUpdate
        
        update = UserPreferencesUpdate(items_per_page=50)
        assert update.items_per_page == 50

    def test_language_values(self):
        """测试语言有效值"""
        from app.schemas.preferences import UserPreferencesUpdate
        
        valid_languages = ["zh-CN", "en-US"]
        
        for lang in valid_languages:
            update = UserPreferencesUpdate(language=lang)
            assert update.language == lang


class TestPreferencesModelDump:
    """测试模型转储功能"""

    def test_notification_settings_dump(self):
        """测试通知设置模型转储"""
        from app.schemas.preferences import NotificationSettingsUpdate
        
        update = NotificationSettingsUpdate(
            email_enabled=True,
            push_enabled=False
        )
        
        # 只包含已设置的字段
        data = update.model_dump(exclude_unset=True)
        
        assert "email_enabled" in data
        assert "push_enabled" in data
        assert "frequency" not in data  # 未设置

    def test_user_preferences_dump(self):
        """测试用户偏好模型转储"""
        from app.schemas.preferences import UserPreferencesUpdate
        
        update = UserPreferencesUpdate(
            theme="dark"
        )
        
        data = update.model_dump(exclude_unset=True)
        
        assert "theme" in data
        assert data["theme"] == "dark"
        assert "language" not in data  # 未设置
