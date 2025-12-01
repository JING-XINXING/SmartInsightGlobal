"""
测试LLM配置API端点
"""
import pytest
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.asyncio
class TestLLMEndpoints:
    """测试LLM配置API端点"""

    @pytest.mark.asyncio
    async def test_get_llm_providers(self, client: AsyncClient):
        """测试获取LLM厂商列表"""
        response = await client.get("/api/v1/llm/providers")

        assert response.status_code == 200
        data = response.json()

        # 应该返回支持的厂商列表
        assert isinstance(data, list)
        assert len(data) > 0

        # 验证每个厂商都有基本字段
        for provider in data:
            assert "name" in provider
            assert "display_name" in provider
            assert "default_model" in provider
            assert "configured" in provider  # 是否配置了API密钥

        # 验证包含预期的厂商
        provider_names = [p["name"] for p in data]
        expected_providers = ["deepseek", "qwen", "moonshot", "zhipu", "baichuan", "minimax"]
        for expected in expected_providers:
            assert expected in provider_names

    @pytest.mark.asyncio
    async def test_get_llm_models_configured_provider(self, client: AsyncClient):
        """测试获取已配置厂商的模型列表"""
        response = await client.get("/api/v1/llm/models/deepseek")

        assert response.status_code == 200
        data = response.json()

        # 应该返回模型列表
        assert isinstance(data, list)
        assert len(data) > 0

        # 验证模型格式
        for model in data:
            assert "id" in model
            assert "name" in model
            assert "description" in model

    @pytest.mark.asyncio
    async def test_get_llm_models_unconfigured_provider(self, client: AsyncClient):
        """测试获取未配置厂商的模型列表"""
        # 对于未配置的厂商，应该返回默认模型列表
        response = await client.get("/api/v1/llm/models/moonshot")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # 即使未配置API密钥，也应该返回模型列表（预定义的）

    @pytest.mark.asyncio
    async def test_get_llm_models_invalid_provider(self, client: AsyncClient):
        """测试获取无效厂商的模型列表"""
        response = await client.get("/api/v1/llm/models/invalid_provider")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_llm_config_valid(self, client: AsyncClient):
        """测试更新有效的LLM配置"""
        config_data = {
            "provider": "deepseek",
            "model": "deepseek-chat"
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "success" in data
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_llm_config_different_providers(self, client: AsyncClient):
        """测试更新不同厂商的LLM配置"""
        providers_models = [
            {"provider": "deepseek", "model": "deepseek-chat"},
            {"provider": "qwen", "model": "qwen-turbo"},
            {"provider": "moonshot", "model": "moonshot-v1-8k"},
            {"provider": "zhipu", "model": "glm-4"},
        ]

        for config_data in providers_models:
            response = await client.post("/api/v1/llm/update-config", json=config_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_llm_config_without_model(self, client: AsyncClient):
        """测试更新LLM配置（不指定模型）"""
        config_data = {
            "provider": "deepseek"
            # 不指定model，使用默认模型
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_update_llm_config_invalid_provider(self, client: AsyncClient):
        """测试更新无效厂商的LLM配置"""
        config_data = {
            "provider": "invalid_provider",
            "model": "some-model"
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_llm_config_missing_data(self, client: AsyncClient):
        """测试更新LLM配置（缺少数据）"""
        # 测试缺少provider
        config_data = {
            "model": "deepseek-chat"
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)

        assert response.status_code == 400

        # 测试缺少所有数据
        response = await client.post("/api/v1/llm/update-config", json={})

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_llm_config_invalid_json(self, client: AsyncClient):
        """测试更新LLM配置（无效JSON）"""
        response = await client.post(
            "/api/v1/llm/update-config",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_llm_config_persistence(self, client: AsyncClient):
        """测试LLM配置持久化"""
        # 更新配置
        config_data = {
            "provider": "qwen",
            "model": "qwen-turbo"
        }

        response1 = await client.post("/api/v1/llm/update-config", json=config_data)
        assert response1.status_code == 200

        # 验证配置被保存（通过获取厂商列表验证当前配置）
        response2 = await client.get("/api/v1/llm/providers")
        assert response2.status_code == 200

        providers = response2.json()
        # 验证当前配置反映在响应中
        qwen_provider = next((p for p in providers if p["name"] == "qwen"), None)
        assert qwen_provider is not None
        assert qwen_provider["current_model"] == "qwen-turbo"
        assert qwen_provider["is_current"] is True

    @pytest.mark.asyncio
    async def test_llm_config_reset(self, client: AsyncClient):
        """测试重置LLM配置"""
        # 首先设置一个配置
        config_data = {
            "provider": "deepseek",
            "model": "deepseek-chat"
        }

        response1 = await client.post("/api/v1/llm/update-config", json=config_data)
        assert response1.status_code == 200

        # 重置为默认配置
        reset_data = {
            "provider": "deepseek",
            "model": None  # None表示使用默认模型
        }

        response2 = await client.post("/api/v1/llm/update-config", json=reset_data)
        assert response2.status_code == 200

        # 验证重置生效
        response3 = await client.get("/api/v1/llm/models/deepseek")
        models = response3.json()
        # 应该使用默认模型
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_llm_provider_status(self, client: AsyncClient):
        """测试LLM厂商状态检查"""
        response = await client.get("/api/v1/llm/providers")

        assert response.status_code == 200
        providers = response.json()

        # 验证每个提供商的状态信息
        for provider in providers:
            assert "name" in provider
            assert "display_name" in provider
            assert "configured" in provider
            assert "available" in provider
            assert "default_model" in provider

            # 如果配置了，应该有current_model和is_current
            if provider["configured"]:
                assert "current_model" in provider
                assert "is_current" in provider
            else:
                # 未配置的提供商不应该有当前模型信息
                assert provider.get("current_model") is None
                assert provider.get("is_current") is False

    @pytest.mark.asyncio
    async def test_llm_endpoints_method_validation(self, client: AsyncClient):
        """测试LLM端点HTTP方法验证"""
        # 测试GET /llm/providers 不应该支持POST
        response = await client.post("/api/v1/llm/providers")
        assert response.status_code == 405  # Method Not Allowed

        # 测试GET /llm/models/{provider} 支持GET
        response = await client.get("/api/v1/llm/models/deepseek")
        assert response.status_code == 200

        # 测试POST /llm/update-config 支持POST
        response = await client.post("/api/v1/llm/update-config", json={})
        # 可能400因为缺少数据，但应该是405
        assert response.status_code in [400, 405]

        # 测试GET /llm/update-config 不支持GET
        response = await client.get("/api/v1/llm/update-config")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_llm_config_concurrent_updates(self, client: AsyncClient):
        """测试LLM配置并发更新"""
        import asyncio

        # 准备不同的配置
        configs = [
            {"provider": "deepseek", "model": "deepseek-chat"},
            {"provider": "qwen", "model": "qwen-turbo"},
            {"provider": "moonshot", "model": "moonshot-v1-8k"}
        ]

        # 并发发送更新请求
        responses = await asyncio.gather(*[
            client.post("/api/v1/llm/update-config", json=config)
            for config in configs
        ])

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200

        # 最后一个配置应该是当前配置
        final_response = await client.get("/api/v1/llm/providers")
        providers = final_response.json()

        # 验证moonshot是当前配置（最后一个）
        moonshot_provider = next((p for p in providers if p["name"] == "moonshot"), None)
        assert moonshot_provider is not None
        assert moonshot_provider["current_model"] == "moonshot-v1-8k"
        assert moonshot_provider["is_current"] is True

    @pytest.mark.asyncio
    async def test_llm_config_validation_edge_cases(self, client: AsyncClient):
        """测试LLM配置验证边界情况"""
        # 测试空字符串
        config_data = {
            "provider": "",
            "model": "deepseek-chat"
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)
        assert response.status_code == 400

        # 测试极长的模型名称
        config_data = {
            "provider": "deepseek",
            "model": "a" * 1000  # 1000字符的模型名
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)
        # 可能成功或失败，取决于验证逻辑
        assert response.status_code in [200, 400]

        # 测试特殊字符
        config_data = {
            "provider": "deepseek",
            "model": "model<script>alert('xss')</script>"
        }

        response = await client.post("/api/v1/llm/update-config", json=config_data)
        # 应该被拒绝或清理
        assert response.status_code in [200, 400]