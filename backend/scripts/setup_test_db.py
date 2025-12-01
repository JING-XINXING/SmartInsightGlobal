#!/usr/bin/env python3
"""
测试数据库设置脚本
创建测试数据库和用户
"""
import asyncio
import asyncpg
import sys
import os


async def setup_test_db():
    """设置测试数据库"""
    try:
        # 连接到默认postgres数据库
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test",
            password="test",
            database="postgres"
        )

        print("✅ 连接到PostgreSQL成功")

        # 创建测试数据库
        await conn.execute("CREATE DATABASE test_smartinsight;")
        print("✅ 创建测试数据库: test_smartinsight")

        # 关闭连接
        await conn.close()

        # 连接到测试数据库
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test",
            password="test",
            database="test_smartinsight"
        )

        print("✅ 连接到测试数据库成功")

        # 创建扩展
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";")
        print("✅ 创建数据库扩展")

        # 关闭连接
        await conn.close()

        print("✅ 测试数据库设置完成!")
        return 0

    except Exception as e:
        print(f"❌ 设置测试数据库失败: {e}")
        return 1


async def drop_test_db():
    """删除测试数据库"""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test",
            password="test",
            database="postgres"
        )

        # 终止现有连接
        await conn.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'test_smartinsight' AND pid <> pg_backend_pid();
        """)

        # 删除数据库
        await conn.execute("DROP DATABASE IF EXISTS test_smartinsight;")
        print("✅ 删除测试数据库: test_smartinsight")

        await conn.close()
        print("✅ 清理完成!")
        return 0

    except Exception as e:
        print(f"❌ 清理测试数据库失败: {e}")
        return 1


async def check_db_health():
    """检查数据库健康状态"""
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test",
            password="test",
            database="test_smartinsight"
        )

        # 简单查询测试连接
        await conn.execute("SELECT 1;")

        await conn.close()
        print("✅ 数据库连接健康")
        return 0

    except Exception as e:
        print(f"❌ 数据库连接不健康: {e}")
        return 1


async def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python setup_test_db.py <setup|drop|check>")
        return 1

    command = sys.argv[1]

    if command == "setup":
        return await setup_test_db()
    elif command == "drop":
        return await drop_test_db()
    elif command == "check":
        return await check_db_health()
    else:
        print("无效命令。使用: setup, drop, 或 check")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)