"""
调度器配置管理模块
用于管理 Celery Beat 定时任务的频率配置
"""
import json
import redis
from typing import Optional
from app.core.config import settings
from app.core.logger import logger


class SchedulerConfig:
    """
    调度器配置管理类
    使用 Redis 存储配置，支持动态更新
    """
    
    # Redis 配置键名
    CONFIG_KEY = "smartinsight:scheduler:config"
    
    # 默认配置
    DEFAULT_CONFIG = {
        "fetch_interval_hours": 1,      # 新闻采集间隔（小时）
        "analyze_interval_minutes": 30,  # 新闻分析间隔（分钟）
        "fetch_enabled": True,           # 是否启用自动采集
        "analyze_enabled": True,         # 是否启用自动分析
        "analyze_batch_size": 50,        # 每次分析的新闻数量
        "backup_enabled": True           # 是否启用自动备份
    }
    
    def __init__(self):
        """初始化 Redis 连接"""
        self._redis: Optional[redis.Redis] = None
    
    @property
    def redis_client(self) -> redis.Redis:
        """获取 Redis 客户端（延迟初始化）"""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,  # 使用 db=1 存储配置，与 Celery 的 db=0 分开
                decode_responses=True
            )
        return self._redis
    
    def get_config(self) -> dict:
        """
        获取当前调度器配置
        Returns:
            配置字典，包含采集和分析的频率设置
        """
        try:
            config_str = self.redis_client.get(self.CONFIG_KEY)
            if config_str:
                config = json.loads(config_str)
                # 合并默认配置，确保所有字段都存在
                return {**self.DEFAULT_CONFIG, **config}
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"获取调度器配置失败: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def set_config(self, config: dict) -> bool:
        """
        更新调度器配置
        Args:
            config: 新的配置字典
        Returns:
            是否更新成功
        """
        try:
            # 验证配置值
            validated_config = self._validate_config(config)
            
            # 保存到 Redis
            self.redis_client.set(
                self.CONFIG_KEY,
                json.dumps(validated_config)
            )
            
            logger.info(f"调度器配置已更新: {validated_config}")
            return True
        except Exception as e:
            logger.error(f"更新调度器配置失败: {e}")
            return False
    
    def _validate_config(self, config: dict) -> dict:
        """
        验证并清洗配置值
        Args:
            config: 原始配置
        Returns:
            验证后的配置
        """
        validated = self.DEFAULT_CONFIG.copy()
        
        # 采集间隔（小时）：1-24
        if "fetch_interval_hours" in config:
            val = int(config["fetch_interval_hours"])
            validated["fetch_interval_hours"] = max(1, min(24, val))
        
        # 分析间隔（分钟）：5-120
        if "analyze_interval_minutes" in config:
            val = int(config["analyze_interval_minutes"])
            validated["analyze_interval_minutes"] = max(5, min(120, val))
        
        # 启用状态
        if "fetch_enabled" in config:
            validated["fetch_enabled"] = bool(config["fetch_enabled"])
        
        if "analyze_enabled" in config:
            validated["analyze_enabled"] = bool(config["analyze_enabled"])
        
        # 分析批次大小：10-100
        if "analyze_batch_size" in config:
            val = int(config["analyze_batch_size"])
            validated["analyze_batch_size"] = max(10, min(100, val))
        
        # 备份启用状态
        if "backup_enabled" in config:
            validated["backup_enabled"] = bool(config["backup_enabled"])
        
        return validated
    
    def get_fetch_interval_seconds(self) -> float:
        """获取采集间隔（秒）"""
        config = self.get_config()
        return config["fetch_interval_hours"] * 3600.0
    
    def get_analyze_interval_seconds(self) -> float:
        """获取分析间隔（秒）"""
        config = self.get_config()
        return config["analyze_interval_minutes"] * 60.0
    
    def is_fetch_enabled(self) -> bool:
        """是否启用自动采集"""
        return self.get_config()["fetch_enabled"]
    
    def is_analyze_enabled(self) -> bool:
        """是否启用自动分析"""
        return self.get_config()["analyze_enabled"]
    
    def is_backup_enabled(self) -> bool:
        """是否启用自动备份"""
        return self.get_config()["backup_enabled"]


# 全局实例
scheduler_config = SchedulerConfig()

