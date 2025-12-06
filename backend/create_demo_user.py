#!/usr/bin/env python3
"""
创建Demo用户的脚本
用于SmartInsightGlobal系统的初始用户设置
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.auth import password_manager
from app.models.user import User, RoleEnum, UserStatus
from datetime import datetime, timezone
import secrets
from datetime import timedelta

async def create_demo_user():
    """创建demo用户"""

    demo_user_data = {
        "username": "demo",
        "email": "demo@smartinsight.com",
        "password": "demo123",  # 简单密码，仅用于演示
        "first_name": "Demo",
        "last_name": "User",
        "role": RoleEnum.ADMIN
    }

    async with AsyncSessionLocal() as db:
        try:
            # 检查用户是否已存在
            result = await db.execute(
                text("SELECT id, username, email FROM users WHERE username = :username OR email = :email"),
                {"username": demo_user_data["username"], "email": demo_user_data["email"]}
            )
            existing_user = result.fetchone()

            if existing_user:
                print(f"❌ 用户已存在: {existing_user[1]} ({existing_user[2]})")
                return False

            # 哈希密码
            hashed_password = password_manager.hash_password(demo_user_data["password"])

            # 生成API密钥
            api_key = secrets.token_urlsafe(32)
            api_key_expires = datetime.now(timezone.utc) + timedelta(days=365)

            # 创建用户
            full_name = f"{demo_user_data['first_name']} {demo_user_data['last_name']}"

            db_user = User(
                username=demo_user_data["username"],
                email=demo_user_data["email"],
                password_hash=hashed_password,
                first_name=demo_user_data["first_name"],
                last_name=demo_user_data["last_name"],
                full_name=full_name,
                role=demo_user_data["role"],
                is_active=True,
                is_verified=True,  # 直接验证，用于演示
                status=UserStatus.ACTIVE,
                api_key=api_key,
                api_key_expires=api_key_expires
            )

            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

            print(f"✅ Demo用户创建成功:")
            print(f"   用户名: {db_user.username}")
            print(f"   邮箱: {db_user.email}")
            print(f"   姓名: {db_user.display_name}")
            print(f"   角色: {db_user.role}")
            print(f"   密码: {demo_user_data['password']}")
            print(f"   用户ID: {db_user.id}")

            return True

        except Exception as e:
            print(f"❌ 创建demo用户失败: {e}")
            await db.rollback()
            return False

async def create_additional_demo_users():
    """创建更多演示用户"""

    demo_users = [
        {
            "username": "analyst",
            "email": "analyst@smartinsight.com",
            "password": "analyst123",
            "first_name": "新闻",
            "last_name": "分析师",
            "role": RoleEnum.ANALYST
        },
        {
            "username": "viewer",
            "email": "viewer@smartinsight.com",
            "password": "viewer123",
            "first_name": "查看",
            "last_name": "用户",
            "role": RoleEnum.VIEWER
        }
    ]

    async with AsyncSessionLocal() as db:
        success_count = 0

        for user_data in demo_users:
            try:
                # 检查用户是否已存在
                result = await db.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": user_data["username"]}
                )
                if result.fetchone():
                    print(f"⚠️  用户 {user_data['username']} 已存在，跳过创建")
                    continue

                # 创建用户
                hashed_password = password_manager.hash_password(user_data["password"])
                api_key = secrets.token_urlsafe(32)
                full_name = f"{user_data['first_name']} {user_data['last_name']}"

                db_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hashed_password,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    full_name=full_name,
                    role=user_data["role"],
                    is_active=True,
                    is_verified=True,
                    status=UserStatus.ACTIVE,
                    api_key=api_key,
                    api_key_expires=datetime.now(timezone.utc) + timedelta(days=365)
                )

                db.add(db_user)
                await db.commit()
                await db.refresh(db_user)

                print(f"✅ 用户 {user_data['username']} 创建成功 (密码: {user_data['password']})")
                success_count += 1

            except Exception as e:
                print(f"❌ 创建用户 {user_data['username']} 失败: {e}")
                await db.rollback()

        return success_count

async def main():
    """主函数"""
    print("🚀 SmartInsightGlobal - 创建Demo用户")
    print("=" * 50)

    # 创建主demo用户
    print("正在创建主demo用户...")
    demo_success = await create_demo_user()

    # 创建其他演示用户
    print("\n正在创建其他演示用户...")
    other_success = await create_additional_demo_users()

    print("\n" + "=" * 50)
    if demo_success:
        print("✅ Demo用户创建完成！")
        print("\n📋 登录信息:")
        print("主管理员账户:")
        print("  用户名: demo")
        print("  密码: demo123")
        print("\n其他账户:")
        print("  分析师账户: analyst / analyst123")
        print("  查看者账户: viewer / viewer123")
    else:
        print("❌ Demo用户创建失败")

    print("\n🌐 请访问: http://localhost:3000/login")

if __name__ == "__main__":
    asyncio.run(main())