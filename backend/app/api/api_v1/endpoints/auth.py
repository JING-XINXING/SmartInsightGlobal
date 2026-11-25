"""
认证API端点
JWT认证、用户注册、登录、权限验证等功能
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
import secrets

from app.db.session import get_db
from app.core.auth import auth_manager, password_manager, jwt_manager, oauth2_scheme
from app.core.logger import logger
from app.models.user import User, UserSession, RoleEnum, UserStatus
from app.core.config import settings


router = APIRouter()


# Pydantic模型
class UserCreate(BaseModel):
    """用户创建模型"""
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    role: RoleEnum = RoleEnum.VIEWER


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    email: str
    username: str
    display_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    permissions: list[str]


class TokenRefresh(BaseModel):
    """刷新令牌模型"""
    refresh_token: str


class PasswordChange(BaseModel):
    """密码修改模型"""
    current_password: str
    new_password: str
    confirm_password: str


class PasswordReset(BaseModel):
    """密码重置模型"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str
    new_password: str
    confirm_password: str


class UserProfile(BaseModel):
    """用户资料模型"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: str = "UTC"
    language: str = "zh-CN"
    notification_settings: dict = {}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户依赖"""
    try:
        payload = jwt_manager.verify_token(token, "access")
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # 查询用户
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return user

    except HTTPException:
        # verify_token 已把令牌错误转成 401，不能再包成 500
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


def require_permission(permission: str):
    """权限装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    - 创建新用户账户
    - 验证邮箱唯一性
    - 哈希用户密码
    - 发送验证邮件(可选)
    """
    try:
        # 检查邮箱是否已存在
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_username = result.scalar_one_or_none()

        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # 创建用户
        hashed_password = password_manager.hash_password(user_data.password)
        full_name = f"{user_data.first_name} {user_data.last_name}".strip()

        # 生成API密钥
        api_key = secrets.token_urlsafe(32)
        api_key_expires = datetime.now(timezone.utc) + timedelta(days=365)

        db_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            full_name=full_name,
            role=user_data.role,
            is_active=True,
            is_verified=False,  # 需要邮件验证
            api_key=api_key,
            api_key_expires=api_key_expires,
            status=UserStatus.ACTIVE
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # 生成访问和刷新令牌
        tokens = auth_manager.create_user_tokens(db_user)

        # 创建用户会话
        request_info = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "device_info": {}
        }
        await auth_manager.create_user_session(db_user, tokens["refresh_token"], request_info, db)

        # 记录访问日志
        await auth_manager.log_access(
            user_id=db_user.id,
            session_id=None,
            endpoint="/auth/register",
            method="POST",
            status_code=201,
            request_info=request_info,
            db=db
        )

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=db_user.id,
            action="user_registered",
            resource_type="user",
            resource_id=str(db_user.id),
            old_values=None,
            new_values={
                "email": db_user.email,
                "username": db_user.username,
                "role": db_user.role
            },
            request_info=request_info,
            db=db
        )

        logger.info(f"User registered successfully: {db_user.email}")

        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            display_name=db_user.display_name,
            role=db_user.role,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            permissions=db_user.get_permissions_list()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    - 验证用户凭据
    - 生成访问和刷新令牌
    - 创建用户会话
    - 记录登录日志
    """
    try:
        # 认证用户
        user = await auth_manager.authenticate_user(form_data.username, form_data.password, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 生成令牌
        tokens = auth_manager.create_user_tokens(user)

        # 创建会话
        request_info = {
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "device_info": {}
        }
        session = await auth_manager.create_user_session(user, tokens["refresh_token"], request_info, db)

        # 记录访问日志
        await auth_manager.log_access(
            user_id=user.id,
            session_id=session.id,
            endpoint="/auth/login",
            method="POST",
            status_code=200,
            request_info=request_info,
            db=db
        )

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=user.id,
            action="user_login",
            resource_type="user",
            resource_id=str(user.id),
            old_values=None,
            new_values={
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "session_created": session.created_at.isoformat()
            },
            request_info=request_info,
            db=db
        )

        logger.info(f"User logged in successfully: {user.email}")

        return Token(**tokens)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_data: TokenRefresh,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    - 验证刷新令牌
    - 生成新的访问令牌
    - 更新会话
    """
    try:
        # 验证刷新令牌
        payload = jwt_manager.verify_token(token_data.refresh_token, "refresh")
        refresh_token = token_data.refresh_token
        user_id = payload.get("user_id")

        # 查找会话
        session_result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            )
        )
        session = session_result.scalar_one_or_none()

        if not session or session.is_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # 获取用户信息
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # 生成新的访问令牌
        access_token = jwt_manager.create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "username": user.username,
            "permissions": user.get_permissions_list()
        })

        # 更新会话活动时间
        session.last_activity = datetime.now(timezone.utc)
        db.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=jwt_manager.access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status_STATUS.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出
    - 验证访问令牌
    - 使会话失效
    - 记录登出日志
    """
    try:
        # 从请求头中获取令牌
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        token = authorization.replace("Bearer ", "")
        payload = jwt_manager.verify_token(token, "access")
        user_id = payload.get("user_id")

        # 失效用户的所有会话
        session_result = await db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        )
        sessions = session_result.scalars().all()

        for session in sessions:
            session.is_active = False

        await db.commit()

        # 记录访问日志
        await auth_manager.log_access(
            user_id=user_id,
            session_id=None,
            endpoint="/auth/logout",
            method="POST",
            status_code=200,
            request_info={
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            },
            db=db
        )

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=user_id,
            action="user_logout",
            resource_type="user_session",
            resource_id=str(user_id),
            old_values={
                "active_sessions": len([s for s in sessions if s.is_active])
            },
            new_values={"active_sessions": 0},
            request_info={
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            },
            db=db
        )

        logger.info(f"User logged out successfully: user_id={user_id}")

        return {"message": "Successfully logged out"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    - 验证用户身份
    - 返回用户信息
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        permissions=current_user.get_permissions_list()
    )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户资料
    - 验证用户身份
    - 更新用户信息
    - 记录审计日志
    """
    try:
        # 记录旧值
        old_values = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "bio": current_user.bio,
            "timezone": current_user.timezone,
            "language": current_user.language,
            "notification_settings": current_user.notification_settings
        }

        # 更新用户信息
        if profile_data.first_name:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name:
            current_user.last_name = profile_data.last_name
        if profile_data.bio:
            current_user.bio = profile_data.bio
        if profile_data.timezone:
            current_user.timezone = profile_data.timezone
        if profile_data.language:
            current_user.language = profile_data.language
        if profile_data.notification_settings:
            current_user.notification_settings = profile_data.notification_settings

        # 更新全名
        if profile_data.first_name and profile_data.last_name:
            current_user.full_name = f"{profile_data.first_name} {profile_data.last_name}".strip()

        await db.commit()
        await db.refresh(current_user)

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=current_user.id,
            action="profile_updated",
            resource_type="user",
            resource_id=str(current_user.id),
            old_values=old_values,
            new_values={
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "bio": current_user.bio,
                "timezone": current_user.timezone,
                "language": current_user.language,
                "notification_settings": current_user.notification_settings
            },
            request_info={},  # TODO: 从请求中获取
            db=db
        )

        logger.info(f"User profile updated: user_id={current_user.id}")

        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            display_name=current_user.display_name,
            role=current_user.role,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at,
            last_login=current_user.last_login,
            permissions=current_user.get_permissions_list()
        )

    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    - 验证当前密码
    - 设置新密码
    - 更新用户记录
    """
    try:
        # 验证当前密码
        if not password_manager.verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # 验证新密码一致性
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )

        # 更新密码
        current_user.password_hash = password_manager.hash_password(password_data.new_password)
        db.commit()

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=current_user.id,
            action="password_changed",
            resource_type="user",
            resource_id=str(current_user.id),
            old_values=None,
            new_values={"password_changed": True},
            request_info={},
            db=db
        )

        logger.info(f"Password changed successfully: user_id={current_user.id}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    email_data: PasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    忘记密码
    - 验证用户邮箱
    - 生成重置令牌
    - 发送重置邮件（TODO: 集成邮件服务）
    """
    try:
        # 查找用户
        result = await db.execute(
            select(User).where(User.email == email_data.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            # 为了安全，不透露用户是否存在
            return {"message": "If the email is registered, you will receive a password reset link"}

        # 生成重置令牌
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # 更新用户记录
        user.reset_token = reset_token
        user.reset_token_expires = reset_token_expires
        db.commit()

        # TODO: 发送密码重置邮件
        # await send_password_reset_email(user.email, reset_token)

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=user.id,
            action="password_reset_requested",
            resource_type="user",
            resource_id=str(user.id),
            old_values=None,
            new_values={"reset_token_issued": True},
            request_info={
                "ip_address": request.client.host
            },
            db=db
        )

        logger.info(f"Password reset requested: email={email_data.email}")

        return {"message": "If the email is registered, you will receive a password reset link"}

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    重置密码
    - 验证重置令牌
    - 设置新密码
    - 清除重置令牌
    """
    try:
        # 查找用户
        result = await db.execute(
            select(User).where(User.reset_token == reset_data.token)
        )
        user = result.scalar_one_or_none()

        if not user or not user.reset_token_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # 检查令牌是否过期
        if datetime.now(timezone.utc) > user.reset_token_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

        # 验证新密码一致性
        if reset_data.new_password != reset_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        # 更新密码
        user.password_hash = password_manager.hash_password(reset_data.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        # 记录审计日志
        await auth_manager.log_audit(
            user_id=user.id,
            action="password_reset_completed",
            resource_type="user",
            resource_id=str(user.id),
            old_values=None,
            new_values={"password_reset": True},
            request_info={},
            db=db
        )

        logger.info(f"Password reset completed: user_id={user.id}")

        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/permissions")
async def get_permissions(current_user: User = Depends(get_current_user)):
    """
    获取用户权限列表
    - 验证用户身份
    - 返回用户权限
    """
    return {
        "user_id": current_user.id,
        "role": current_user.role,
        "permissions": current_user.get_permissions_list(),
        "is_admin": current_user.role == RoleEnum.ADMIN,
        "can_analyze_news": current_user.can_analyze_news(),
        "can_manage_users": current_user.can_manage_users(),
        "is_premium_user": current_user.is_premium_user()
    }


@router.get("/check-auth")
async def check_auth(current_user: User = Depends(get_current_user)):
    """
    检查认证状态
    - 验证令牌有效性
    - 返回用户简要信息
    """
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role
    }


@router.get("/test-permission/{permission}")
async def test_permission(
    permission: str,
    current_user: User = Depends(get_current_user)
):
    """
    测试用户权限
    - 验证用户权限
    - 返回测试结果
    """
    if not current_user.has_permission(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required"
        )

    return {
        "has_permission": True,
        "permission": permission,
        "user_id": current_user.id,
        "role": current_user.role
    }