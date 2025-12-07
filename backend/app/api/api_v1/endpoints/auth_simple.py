"""
认证API端点 - 简化版本
JWT认证、用户注册、登录等功能
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
import secrets

from app.db.session import get_db
from app.core.auth import auth_manager, password_manager, jwt_manager
from app.core.logger import logger
from app.models.user import User, RoleEnum
from app.core.config import settings


router = APIRouter()


# Pydantic模型
class UserCreate(BaseModel):
    """用户创建模型"""
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime


class TokenWithUser(BaseModel):
    """令牌和用户信息响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    - 创建新用户账户
    - 验证邮箱唯一性
    - 哈希用户密码
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

        # 创建新用户
        hashed_password = password_manager.hash_password(user_data.password)

        db_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            role=RoleEnum.VIEWER,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(timezone.utc)
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        logger.info(f"User registered successfully: {db_user.email}")

        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            role=db_user.role,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenWithUser)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
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

        # 创建令牌
        tokens = auth_manager.create_user_tokens(user)

        logger.info(f"User logged in successfully: {user.email} (role: {user.role})")

        return TokenWithUser(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout():
    """
    用户登出
    """
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(db: AsyncSession = Depends(get_db)):
    """
    获取当前用户信息
    """
    # 这里需要实现JWT令牌验证
    # 暂时返回示例用户
    return UserResponse(
        id=1,
        email="demo@example.com",
        username="demo_user",
        role="viewer",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )