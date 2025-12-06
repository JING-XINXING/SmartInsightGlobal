"""
用户模型
支持JWT认证和基于角色的访问控制(RBAC)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import enum

from app.db.base_class import Base


class RoleEnum(str, SQLEnum):
    """用户角色枚举"""
    ADMIN = "admin"  # 管理员 - 所有权限
    ANALYST = "analyst"  # 分析师 - 查看分析，编辑配置
    VIEWER = "viewer"  # 查看者 - 只读权限
    GUEST = "guest"  # 访客 - 限制访问


class UserStatus(str, SQLEnum):
    """用户状态枚举"""
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"  # 已删除


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # 用户信息
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="zh-CN")

    # 认证相关
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # 角色和权限
    role = Column(String(20), default=RoleEnum.VIEWER, nullable=False)
    permissions = Column(JSON, nullable=True)  # 额外权限列表
    groups = Column(JSON, nullable=True)  # 用户所属组

    # 状态和时间
    status = Column(String(20), default=UserStatus.ACTIVE, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 密码重置
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # 认证相关字段
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # API相关
    api_key = Column(String(255), nullable=True, unique=True)
    api_key_expires = Column(DateTime(timezone=True), nullable=True)

    # 用户偏好设置
    preferences = Column(JSON, nullable=True)  # 用户偏好配置
    notification_settings = Column(JSON, nullable=True)  # 通知设置

    # 关系
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username

    @property
    def is_premium_user(self) -> bool:
        """是否为高级用户"""
        return self.role in [RoleEnum.ADMIN, RoleEnum.ANALYST]

    @property
    def can_analyze_news(self) -> bool:
        """是否可以分析新闻"""
        return self.role in [RoleEnum.ADMIN, RoleEnum.ANALYST]

    @property
    def can_manage_users(self) -> bool:
        """是否可以管理用户"""
        return self.role == RoleEnum.ADMIN

    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        # 管理员有所有权限
        if self.role == RoleEnum.ADMIN:
            return True

        # 检查用户自定义权限
        if self.permissions and permission in self.permissions:
            return True

        # 基于角色的默认权限
        role_permissions = {
            RoleEnum.ANALYST: [
                "read_news", "analyze_news", "manage_llm_config",
                "view_reports", "export_data", "manage_preferences"
            ],
            RoleEnum.VIEWER: [
                "read_news", "view_reports", "export_data"
            ],
            RoleEnum.GUEST: [
                "read_news_limited"
            ]
        }

        return permission in role_permissions.get(self.role, [])

    def get_permissions_list(self) -> list:
        """获取用户权限列表"""
        if self.role == RoleEnum.ADMIN:
            return ["*"]  # 所有权限

        permissions = set(self.permissions or [])

        # 添加角色默认权限
        role_permissions = {
            RoleEnum.ANALYST: [
                "read_news", "analyze_news", "manage_llm_config",
                "view_reports", "export_data", "manage_preferences"
            ],
            RoleEnum.VIEWER: [
                "read_news", "view_reports", "export_data"
            ],
            RoleEnum.GUEST: [
                "read_news_limited"
            ]
        }

        permissions.update(role_permissions.get(self.role, []))
        return list(permissions)

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), nullable=True)

    # 会话信息
    ip_address = Column(String(45), nullable=True)  # IPv6兼容
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)  # 设备信息

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)

    # 关系
    user = relationship("User", back_populates="user_sessions")

    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class AccessLog(Base):
    """访问日志模型"""
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=True, index=True)

    # 请求信息
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 请求结果
    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)  # 毫秒

    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 附加信息
    request_params = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # 关系
    user = relationship("User", back_populates="access_logs")

    def __repr__(self) -> str:
        return f"<AccessLog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # 操作类型
    resource_type = Column(String(100), nullable=False, index=True)  # 资源类型
    resource_id = Column(String(100), nullable=True, index=True)  # 资源ID

    # 操作详情
    details = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)  # 修改前的值
    new_values = Column(JSON, nullable=True)  # 修改后的值

    # 请求信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 操作结果
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"