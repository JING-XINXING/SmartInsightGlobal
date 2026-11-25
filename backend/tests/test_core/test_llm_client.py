"""
测试统一LLM客户端
"""
import json
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
from app.core.llm_client import LLMClient, llm_client
from app.core.config import settings


@pytest.mark.unit
class TestLLMClient:
    """测试LLM客户端"""

    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """模拟配置"""
        test_settings = {
            "DEEPSEEK_API_KEY": "test-deepseek-key",
            "QWEN_API_KEY": "test-qwen-key",
            "MOONSHOT_API_KEY": "",
            "ZHIPU_API_KEY": "test-zhipu-key"
        }

        for key, value in test_settings.items():
            monkeypatch.setattr(settings, key, value)

        return test_settings

    @pytest.fixture
    def llm_client_instance(self):
        """创建LLM客户端实例"""
        return LLMClient()

    def test_initialization(self, llm_client_instance):
        """测试客户端初始化"""
        assert llm_client_instance.default_provider == "deepseek"
        assert llm_client_instance.default_model is None
        assert llm_client_instance.timeout == 60.0

    def test_providers_configuration(self, llm_client_instance):
        """测试厂商配置"""
        assert "deepseek" in llm_client_instance.PROVIDERS
        assert "qwen" in llm_client_instance.PROVIDERS
        assert "moonshot" in llm_client_instance.PROVIDERS
        assert "zhipu" in llm_client_instance.PROVIDERS

        # 验证配置格式
        deepseek_config = llm_client_instance.PROVIDERS["deepseek"]
        assert "base_url" in deepseek_config
        assert "api_key_name" in deepseek_config
        assert "default_model" in deepseek_config

    def test_get_available_providers_with_keys(self, mock_settings, llm_client_instance):
        """测试获取可用的厂商（有API密钥）"""
        available = llm_client_instance.get_available_providers()

        # 应该包含有密钥的厂商
        assert "deepseek" in available
        assert "qwen" in available
        assert "zhipu" in available

        # 不应该包含没有密钥的厂商
        assert "moonshot" not in available

    def test_get_available_providers_no_keys(self, llm_client_instance):
        """测试获取可用的厂商（无API密钥）"""
        # 模拟所有密钥都为空
        with patch.object(llm_client_instance, 'PROVIDERS', {}) as mock_providers:
            available = llm_client_instance.get_available_providers()
            assert isinstance(available, list)

    def test_set_config(self, llm_client_instance):
        """测试设置配置"""
        llm_client_instance.set_config("deepseek", "deepseek-chat")

        assert llm_client_instance.default_provider == "deepseek"
        assert llm_client_instance.default_model == "deepseek-chat"

    def test_set_config_invalid_provider(self, llm_client_instance):
        """测试设置无效厂商"""
        original_provider = llm_client_instance.default_provider
        original_model = llm_client_instance.default_model

        llm_client_instance.set_config("invalid_provider", "model")

        # 配置不应该改变
        assert llm_client_instance.default_provider == original_provider
        assert llm_client_instance.default_model == original_model

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, llm_client_instance, mock_settings):
        """测试聊天完成成功"""
        # 模拟httpx响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "这是AI的回复"
                    }
                }
            ]
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek"
            )

            assert response == "这是AI的回复"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_no_api_key(self, llm_client_instance):
        """测试聊天完成无API密钥"""
        response = await llm_client_instance.chat_completion(
            messages=[{"role": "user", "content": "测试消息"}],
            provider="moonshot"  # 没有密钥
        )

        # 应该返回mock响应
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_chat_completion_http_error(self, llm_client_instance, mock_settings):
        """测试聊天完成HTTP错误"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text.return_value = "Unauthorized"

        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek"
            )

            assert response is None

    @pytest.mark.asyncio
    async def test_chat_completion_timeout(self, llm_client_instance, mock_settings):
        """测试聊天完成超时"""
        with patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("超时")):
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek"
            )

            assert response is None

    @pytest.mark.asyncio
    async def test_chat_completion_invalid_response_format(self, llm_client_instance, mock_settings):
        """测试聊天完成无效响应格式"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "format"}

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek"
            )

            assert response is None

    @pytest.mark.asyncio
    async def test_chat_completion_custom_model(self, llm_client_instance, mock_settings):
        """测试聊天完成自定义模型"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "自定义模型回复"
                    }
                }
            ]
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek",
                model="custom-model"
            )

            assert response == "自定义模型回复"

            # 验证使用了自定义模型
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "custom-model"

    @pytest.mark.asyncio
    async def test_chat_completion_with_temperature_and_tokens(self, llm_client_instance, mock_settings):
        """测试聊天完成温度和token参数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "参数化回复"
                    }
                }
            ]
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="deepseek",
                temperature=0.5,
                max_tokens=100
            )

            assert response == "参数化回复"

            # 验证参数传递
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["temperature"] == 0.5
            assert payload["max_tokens"] == 100

    def test_mock_response_sentiment(self, llm_client_instance):
        """测试mock情感回复"""
        messages = [
            {"role": "system", "content": "你是一个专业的新闻情感分析助手。"},
            {"role": "user", "content": "请分析以下新闻的情感倾向，并给出一个-100到100之间的分数"}
        ]

        response = llm_client_instance._mock_response(messages)

        # 情感分数可以是负数，isdigit 不能覆盖负号
        assert isinstance(response, str)
        score = int(response)
        assert -100 <= score <= 100

    def test_mock_response_keywords(self, llm_client_instance):
        """测试mock关键词回复"""
        messages = [
            {"role": "system", "content": "你是一个专业的新闻关键词提取助手。"},
            {"role": "user", "content": "请从以下新闻中提取3-5个关键词"}
        ]

        response = llm_client_instance._mock_response(messages)

        # 关键词是随机抽样的 JSON 数组，不依赖某三个固定词
        keywords = json.loads(response)
        assert isinstance(keywords, list)
        assert 1 <= len(keywords) <= 5

    def test_mock_response_category(self, llm_client_instance):
        """测试mock分类回复"""
        messages = [
            {"role": "system", "content": "你是一个专业的新闻分类助手。"},
            {"role": "user", "content": "请将以下新闻分类到最合适的类别中"}
        ]

        response = llm_client_instance._mock_response(messages)

        # 应该返回预定义类别之一
        categories = ["政治", "经济", "军事", "科技", "社会", "文化", "国际关系"]
        assert response in categories

    @pytest.mark.asyncio
    async def test_chat_completion_fallback_to_default_provider(self, llm_client_instance, mock_settings):
        """测试聊天完成回退到默认厂商"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "默认厂商回复"
                    }
                }
            ]
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            # 使用无效厂商，应该回退到默认厂商
            response = await llm_client_instance.chat_completion(
                messages=[{"role": "user", "content": "测试消息"}],
                provider="invalid_provider"
            )

            assert response == "默认厂商回复"

            # 验证使用了默认厂商（deepseek）
            call_args = mock_post.call_args
            assert "deepseek" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_chat_completion_different_providers(self, llm_client_instance, mock_settings):
        """测试不同厂商的聊天完成"""
        mock_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": f"厂商{i+1}回复"
                        }
                    }
                ]
            }
            mock_responses.append(mock_response)

        with patch('httpx.AsyncClient.post', side_effect=mock_responses) as mock_post:
            # 测试不同厂商
            for i, provider in enumerate(["deepseek", "qwen", "zhipu"]):
                response = await llm_client_instance.chat_completion(
                    messages=[{"role": "user", "content": "测试消息"}],
                    provider=provider
                )
                assert response == f"厂商{i+1}回复"

            assert mock_post.call_count == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_client_integration():
    """集成测试：真实LLM客户端（仅在有配置时运行）"""
    # 只在有真实API密钥时运行
    if not settings.DEEPSEEK_API_KEY:
        pytest.skip("需要真实的LLM API密钥")

    client = LLMClient()

    # 测试获取可用厂商
    providers = client.get_available_providers()
    assert len(providers) > 0

    # 测试简单的聊天完成（使用mock模式，避免API调用）
    response = await client.chat_completion(
        messages=[
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请回复一个简单的问候。"}
        ],
        temperature=0.1,
        max_tokens=10
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0