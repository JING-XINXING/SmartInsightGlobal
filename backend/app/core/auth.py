"""
JWT认证和权限管理模块
实现用户认证、令牌生成、权限验证等功能
"""
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.logger import logger
from app.models.user import User, UserSession, AccessLog, RoleEnum
from app.db.session import get_db


# JWT配置
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7   # 7天

# OAuth2密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTAuthManager:
    """JWT认证管理器"""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌

        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间

        Returns:
            JWT访问令牌
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建刷新令牌

        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间

        Returns:
            JWT刷新令牌
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌
            token_type: 令牌类型

        Returns:
            令牌载荷数据

        Raises:
            JWTException: 令牌无效
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError("Invalid token type")

            # 检查过期时间
            if datetime.now(timezone.utc) > datetime.fromtimestamp(payload["exp"], tz=timezone.utc):
                raise jwt.ExpiredSignatureError("Token has expired")

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )


class PasswordManager:
    """密码管理器"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        # bcrypt有72字节的限制，截断超长密码
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            密码是否正确
        """
        return self.pwd_context.verify(plain_password, hashed_password)


class AuthenticationManager:
    """认证管理器"""

    def __init__(self):
        self.jwt_manager = JWTAuthManager()
        self.password_manager = PasswordManager()

    async def authenticate_user(self, email_or_username: str, password: str, db: AsyncSession) -> Optional[User]:
        """
        认证用户

        Args:
            email_or_username: 用户邮箱或用户名
            password: 密码
            db: 数据库会话

        Returns:
            认证成功的用户对象，认证失败返回None
        """
        try:
            # 先尝试按邮箱查找用户
            result = await db.execute(
                select(User).where(User.email == email_or_username)
            )
            user = result.scalar_one_or_none()

            # 如果邮箱没找到，尝试按用户名查找
            if not user:
                result = await db.execute(
                    select(User).where(User.username == email_or_username)
                )
                user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Authentication failed: User not found for email/username {email_or_username}")
                return None

            # 检查用户状态
            if not user.is_active or user.status != "active":
                logger.warning(f"Authentication failed: User {user.email} is not active")
                return None

            # 验证密码
            if not self.password_manager.verify_password(password, user.password_hash):
                logger.warning(f"Authentication failed: Invalid password for user {email_or_username}")
                return None

            # 更新最后登录时间
            user.update_last_login()
            await db.commit()

            logger.info(f"User {email_or_username} authenticated successfully")
            return user

        except Exception as e:
            logger.error(f"Authentication error for user {email_or_username}: {e}")
            return None

    def create_user_tokens(self, user: User) -> Dict[str, str]:
        """
        创建用户令牌

        Args:
            user: 用户对象

        Returns:
            访问令牌和刷新令牌
        """
        # 创建访问令牌
        access_token = self.jwt_manager.create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "username": user.username,
            "permissions": user.get_permissions_list()
        })

        # 创建刷新令牌
        refresh_token = self.jwt_manager.create_refresh_token({
            "sub": user.email,
            "user_id": user.id,
            "type": "refresh"
        })

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.jwt_manager.access_token_expire_minutes * 60
        }

    async def create_user_session(self, user: User, refresh_token: str,
                                   request_info: Dict[str, Any], db: AsyncSession) -> UserSession:
        """
        创建用户会话

        Args:
            user: 用户对象
            refresh_token: 刷新令牌
            request_info: 请求信息
            db: 数据库会话

        Returns:
            用户会话对象
        """
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.jwt_manager.refresh_token_expire_days)

        user_session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            device_info=request_info.get("device_info", {}),
            expires_at=expires_at
        )

        db.add(user_session)
        await db.commit()
        await db.refresh(user_session)

        return user_session

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        从令牌获取当前用户信息

        Args:
            token: JWT访问令牌

        Returns:
            用户信息，验证失败返回None
        """
        try:
            payload = self.jwt_manager.verify_token(token, "access")
            return {
                "user_id": payload["user_id"],
                "email": payload["sub"],
                "role": payload["role"],
                "username": payload["username"],
                "permissions": payload.get("permissions", [])
            }
        except Exception as e:
            logger.error(f"Failed to get user from token: {e}")
            return None

    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> Optional[User]:
        """
        根据用户ID获取用户

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            用户对象，用户不存在返回None
        """
        try:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    async def log_access(self, user_id: Optional[int], session_id: Optional[int],
                         endpoint: str, method: str, status_code: int,
                         request_info: Dict[str, Any], db: AsyncSession) -> None:
        """
        记录访问日志

        Args:
            user_id: 用户ID
            session_id: 会话ID
            endpoint: API端点
            method: HTTP方法
            status_code: 状态码
            request_info: 请求信息
            db: 数据库会话
        """
        try:
            access_log = AccessLog(
                user_id=user_id,
                session_id=session_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                ip_address=request_info.get("ip_address"),
                user_agent=request_info.get("user_agent"),
                request_params=request_info.get("params", {}),
                response_data=request_info.get("response_data", {}),
                error_message=request_info.get("error_message")
            )

            db.add(access_log)
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to log access: {e}")

    async def log_audit(self, user_id: Optional[int], action: str,
                       resource_type: str, resource_id: Optional[str],
                       old_values: Optional[Dict], new_values: Optional[Dict],
                       request_info: Dict[str, Any], success: bool = True,
                       error_message: Optional[str] = None, db: AsyncSession = Depends(get_db)) -> None:
        """
        记录审计日志

        Args:
            user_id: 用户ID
            action: 操作动作
            resource_type: 资源类型
            resource_id: 资源ID
            old_values: 修改前的值
            new_values: 修改后的值
            request_info: 请求信息
            success: 操作是否成功
            error_message: 错误消息
            db: 数据库会话
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    "request_info": request_info
                },
                old_values=old_values,
                new_values=new_values,
                ip_address=request_info.get("ip_address"),
                user_agent=request_info.get("user_agent"),
                success=success,
                error_message=error_message
            )

            db.add(audit_log)
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# 全局实例
auth_manager = AuthenticationManager()
jwt_manager = JWTAuthManager()
password_manager = PasswordManager()


# 导出便捷函数
def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return password_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    return jwt_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    return jwt_manager.create_refresh_token(data, expires_delta)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """验证JWT令牌"""
    return jwt_manager.verify_token(token, token_type)