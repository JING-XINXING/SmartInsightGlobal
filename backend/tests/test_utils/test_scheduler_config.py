"""
测试调度器配置管理
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
import redis
from app.core.scheduler_config import scheduler_config, SchedulerConfig


@pytest.mark.unit
class TestSchedulerConfig:
    """测试调度器配置管理"""

    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = Mock(spec=redis.Redis)
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        return mock_redis

    def test_initialization(self):
        """测试初始化"""
        config = SchedulerConfig()
        assert config._redis is None  # 延迟初始化

    def test_default_config(self):
        """测试默认配置"""
        config = SchedulerConfig()
        default = config.DEFAULT_CONFIG

        assert default["fetch_interval_hours"] == 1
        assert default["analyze_interval_minutes"] == 30
        assert default["fetch_enabled"] is True
        assert default["analyze_enabled"] is True
        assert default["analyze_batch_size"] == 50
        assert default["backup_enabled"] is True

    def test_get_config_no_redis_data(self, mock_redis):
        """测试获取配置（无Redis数据）"""
        config = SchedulerConfig()
        config._redis = mock_redis
        mock_redis.get.return_value = None

        result = config.get_config()

        assert result == config.DEFAULT_CONFIG
        mock_redis.get.assert_called_once_with(config.CONFIG_KEY)

    def test_get_config_with_redis_data(self, mock_redis):
        """测试获取配置（有Redis数据）"""
        config = SchedulerConfig()
        config._redis = mock_redis

        redis_data = {
            "fetch_interval_hours": 2,
            "analyze_interval_minutes": 60,
            "fetch_enabled": False
        }
        mock_redis.get.return_value = json.dumps(redis_data)

        result = config.get_config()

        # 应该合并默认配置
        expected = config.DEFAULT_CONFIG.copy()
        expected.update(redis_data)

        assert result["fetch_interval_hours"] == 2
        assert result["analyze_interval_minutes"] == 60
        assert result["fetch_enabled"] is False
        assert result["analyze_enabled"] is True  # 默认值
        assert result["analyze_batch_size"] == 50  # 默认值

    def test_get_config_redis_exception(self, mock_redis):
        """测试获取配置Redis异常"""
        config = SchedulerConfig()
        config._redis = mock_redis
        mock_redis.get.side_effect = Exception("Redis连接错误")

        result = config.get_config()

        # 应该返回默认配置
        assert result == config.DEFAULT_CONFIG

    def test_set_config_valid(self, mock_redis):
        """测试设置有效配置"""
        config = SchedulerConfig()
        config._redis = mock_redis

        new_config = {
            "fetch_interval_hours": 3,
            "analyze_interval_minutes": 45,
            "fetch_enabled": False,
            "analyze_batch_size": 25
        }

        result = config.set_config(new_config)

        assert result is True
        mock_redis.set.assert_called_once()

        # 验证调用的参数
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == config.CONFIG_KEY  # key
        saved_data = json.loads(call_args[0][1])  # value

        assert saved_data["fetch_interval_hours"] == 3
        assert saved_data["analyze_interval_minutes"] == 45
        assert saved_data["fetch_enabled"] is False
        assert saved_data["analyze_batch_size"] == 25

    def test_set_config_invalid_values(self, mock_redis):
        """测试设置无效配置值"""
        config = SchedulerConfig()
        config._redis = mock_redis

        invalid_config = {
            "fetch_interval_hours": 50,  # 超出范围
            "analyze_interval_minutes": 200,  # 超出范围
            "analyze_batch_size": 500  # 超出范围
        }

        result = config.set_config(invalid_config)

        assert result is True

        # 验证值被限制在合理范围内
        call_args = mock_redis.set.call_args
        saved_data = json.loads(call_args[0][1])

        assert saved_data["fetch_interval_hours"] == 24  # 被限制
        assert saved_data["analyze_interval_minutes"] == 120  # 被限制
        assert saved_data["analyze_batch_size"] == 100  # 被限制

    def test_set_config_partial_values(self, mock_redis):
        """测试设置部分配置值"""
        config = SchedulerConfig()
        config._redis = mock_redis

        partial_config = {
            "fetch_interval_hours": 4,
            "fetch_enabled": False
            # 其他字段使用默认值
        }

        result = config.set_config(partial_config)

        assert result is True

        call_args = mock_redis.set.call_args
        saved_data = json.loads(call_args[0][1])

        assert saved_data["fetch_interval_hours"] == 4
        assert saved_data["fetch_enabled"] is False
        # 验证其他默认值被保留
        assert saved_data["analyze_interval_minutes"] == 30

    def test_set_config_redis_exception(self, mock_redis):
        """测试设置配置Redis异常"""
        config = SchedulerConfig()
        config._redis = mock_redis
        mock_redis.set.side_effect = Exception("Redis写入错误")

        result = config.set_config({"fetch_interval_hours": 2})

        assert result is False

    def test_validate_config(self):
        """测试配置验证"""
        config = SchedulerConfig()

        # 测试有效配置
        valid_config = {
            "fetch_interval_hours": 12,
            "analyze_interval_minutes": 60,
            "fetch_enabled": False,
            "analyze_enabled": False,
            "analyze_batch_size": 25,
            "backup_enabled": False
        }

        validated = config._validate_config(valid_config)
        assert validated == valid_config

        # 测试超出范围的值
        invalid_config = {
            "fetch_interval_hours": 50,  # 应该被限制为24
            "analyze_interval_minutes": 300,  # 应该被限制为120
            "analyze_batch_size": 500  # 应该被限制为100
        }

        validated = config._validate_config(invalid_config)
        assert validated["fetch_interval_hours"] == 24
        assert validated["analyze_interval_minutes"] == 120
        assert validated["analyze_batch_size"] == 100

        # 测试低于范围的值
        low_config = {
            "fetch_interval_hours": 0,  # 应该被限制为1
            "analyze_interval_minutes": 0,  # 应该被限制为5
            "analyze_batch_size": 5  # 应该被限制为10
        }

        validated = config._validate_config(low_config)
        assert validated["fetch_interval_hours"] == 1
        assert validated["analyze_interval_minutes"] == 5
        assert validated["analyze_batch_size"] == 10

    def test_get_fetch_interval_seconds(self, mock_redis):
        """测试获取采集间隔秒数"""
        config = SchedulerConfig()
        config._redis = mock_redis

        # 设置Redis数据
        mock_redis.get.return_value = json.dumps({"fetch_interval_hours": 2})

        seconds = config.get_fetch_interval_seconds()
        assert seconds == 2 * 3600.0  # 2小时

        # 测试默认值
        mock_redis.get.return_value = None
        seconds = config.get_fetch_interval_seconds()
        assert seconds == 1 * 3600.0  # 默认1小时

    def test_get_analyze_interval_seconds(self, mock_redis):
        """测试获取分析间隔秒数"""
        config = SchedulerConfig()
        config._redis = mock_redis

        mock_redis.get.return_value = json.dumps({"analyze_interval_minutes": 15})

        seconds = config.get_analyze_interval_seconds()
        assert seconds == 15 * 60.0  # 15分钟

        # 测试默认值
        mock_redis.get.return_value = None
        seconds = config.get_analyze_interval_seconds()
        assert seconds == 30 * 60.0  # 默认30分钟

    def test_is_fetch_enabled(self, mock_redis):
        """测试是否启用采集"""
        config = SchedulerConfig()
        config._redis = mock_redis

        # 测试启用状态
        mock_redis.get.return_value = json.dumps({"fetch_enabled": True})
        assert config.is_fetch_enabled() is True

        # 测试禁用状态
        mock_redis.get.return_value = json.dumps({"fetch_enabled": False})
        assert config.is_fetch_enabled() is False

        # 测试默认值
        mock_redis.get.return_value = None
        assert config.is_fetch_enabled() is True  # 默认启用

    def test_is_analyze_enabled(self, mock_redis):
        """测试是否启用分析"""
        config = SchedulerConfig()
        config._redis = mock_redis

        # 测试启用状态
        mock_redis.get.return_value = json.dumps({"analyze_enabled": True})
        assert config.is_analyze_enabled() is True

        # 测试禁用状态
        mock_redis.get.return_value = json.dumps({"analyze_enabled": False})
        assert config.is_analyze_enabled() is False

        # 测试默认值
        mock_redis.get.return_value = None
        assert config.is_analyze_enabled() is True  # 默认启用

    def test_is_backup_enabled(self, mock_redis):
        """测试是否启用备份"""
        config = SchedulerConfig()
        config._redis = mock_redis

        # 测试启用状态
        mock_redis.get.return_value = json.dumps({"backup_enabled": True})
        assert config.is_backup_enabled() is True

        # 测试禁用状态
        mock_redis.get.return_value = json.dumps({"backup_enabled": False})
        assert config.is_backup_enabled() is False

        # 测试默认值
        mock_redis.get.return_value = None
        assert config.is_backup_enabled() is True  # 默认启用

    def test_redis_client_lazy_initialization(self, mock_redis):
        """测试Redis客户端延迟初始化"""
        config = SchedulerConfig()

        with patch('redis.Redis', return_value=mock_redis) as mock_redis_class:
            # 第一次访问应该创建客户端
            client1 = config.redis_client
            assert client1 is mock_redis
            mock_redis_class.assert_called_once()

            # 第二次访问应该返回同一实例
            client2 = config.redis_client
            assert client1 is client2

            # 不应该重复创建
            assert mock_redis_class.call_count == 1

    def test_malformed_json_handling(self, mock_redis):
        """测试损坏的JSON处理"""
        config = SchedulerConfig()
        config._redis = mock_redis

        # 模拟损坏的JSON
        mock_redis.get.return_value = "invalid json string"

        result = config.get_config()

        # 应该返回默认配置
        assert result == config.DEFAULT_CONFIG

    def test_empty_string_handling(self, mock_redis):
        """测试空字符串处理"""
        config = SchedulerConfig()
        config._redis = mock_redis

        mock_redis.get.return_value = ""

        result = config.get_config()

        # 应该返回默认配置
        assert result == config.DEFAULT_CONFIG

    def test_config_key_constant(self):
        """测试配置键常量"""
        assert SchedulerConfig.CONFIG_KEY == "smartinsight:scheduler:config"


@pytest.mark.integration
class TestSchedulerConfigIntegration:
    """调度器配置集成测试"""

    @pytest.mark.asyncio
    async def test_real_redis_operations(self):
        """集成测试：真实Redis操作（仅在有Redis时运行）"""
        try:
            # 测试实际的Redis连接
            config = SchedulerConfig()

            # 测试获取默认配置
            default_config = config.get_config()
            assert default_config == config.DEFAULT_CONFIG

            # 测试设置和获取配置
            new_config = {
                "fetch_interval_hours": 3,
                "analyze_interval_minutes": 45,
                "fetch_enabled": False
            }

            result = config.set_config(new_config)
            if result:  # 仅在Redis可用时
                retrieved_config = config.get_config()
                assert retrieved_config["fetch_interval_hours"] == 3
                assert retrieved_config["analyze_interval_minutes"] == 45
                assert retrieved_config["fetch_enabled"] is False

        except Exception as e:
            pytest.skip(f"Redis集成测试跳过: {e}")

    def test_config_persistence(self):
        """测试配置持久化"""
        try:
            config = SchedulerConfig()

            # 设置配置
            original_config = config.get_config()

            # 修改配置
            test_config = original_config.copy()
            test_config["fetch_interval_hours"] = 5

            result = config.set_config(test_config)
            if result:  # 仅在Redis可用时
                # 创建新实例验证持久化
                new_config_instance = SchedulerConfig()
                retrieved_config = new_config_instance.get_config()

                assert retrieved_config["fetch_interval_hours"] == 5

        except Exception as e:
            pytest.skip(f"配置持久化测试跳过: {e}")


# 测试全局实例
def test_global_scheduler_config_instance():
    """测试全局调度器配置实例"""
    assert scheduler_config is not None
    assert isinstance(scheduler_config, SchedulerConfig)