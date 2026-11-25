"""API 速率限制。

默认每个 IP 每分钟 120 次。测试可通过环境变量 RATE_LIMIT_ENABLED=false 关闭。
该开关在进程启动时读取一次。
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_enabled() -> bool:
    """是否启用限流。未设置时默认开启。"""
    value = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower()
    return value not in ("0", "false", "no", "off")


# 全局限流器。路由未单独声明时使用 default_limits。
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=_rate_limit_enabled(),
)
