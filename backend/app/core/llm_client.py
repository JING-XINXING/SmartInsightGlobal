import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logger import logger

class LLMClient:
    """
    统一 LLM 客户端，支持多个国产大模型厂商 (DeepSeek, Qwen, Moonshot 等)
    
    Attributes:
        PROVIDERS: 支持的 LLM 厂商配置字典
        timeout: API 调用超时时间 (秒)
        default_provider: 当前默认厂商
        default_model: 当前默认模型
    """
    
    # 支持的 LLM 厂商配置
    PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "api_key_name": "DEEPSEEK_API_KEY",
            "default_model": "deepseek-chat"
        },
        "moonshot": {
            "base_url": "https://api.moonshot.cn/v1",
            "api_key_name": "MOONSHOT_API_KEY",
            "default_model": "moonshot-v1-8k"
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key_name": "QWEN_API_KEY",
            "default_model": "qwen-turbo"
        },
        "baichuan": {
            "base_url": "https://api.baichuan-ai.com/v1",
            "api_key_name": "BAICHUAN_API_KEY",
            "default_model": "Baichuan2-Turbo"
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key_name": "ZHIPU_API_KEY",
            "default_model": "glm-4"
        },
        "minimax": {
            "base_url": "https://api.minimax.chat/v1",
            "api_key_name": "MINIMAX_API_KEY",
            "default_model": "abab5.5-chat"
        }
    }

    def __init__(self):
        self.timeout = 60.0
        self.default_provider = "deepseek"
        self.default_model: Optional[str] = None  # 用户选择的模型，None 表示使用厂商默认
    
    def set_config(self, provider: str, model: Optional[str] = None):
        """
        设置当前使用的厂商和模型
        Args:
            provider: 厂商名称
            model: 模型名称，为 None 时使用厂商默认模型
        """
        if provider in self.PROVIDERS:
            self.default_provider = provider
            self.default_model = model
            logger.info(f"LLM 配置已更新: provider={provider}, model={model or '默认'}")
        
    def get_available_providers(self) -> List[str]:
        """
        Get list of providers that have API keys configured.
        """
        available = []
        for name, config in self.PROVIDERS.items():
            api_key = getattr(settings, config["api_key_name"], None)
            if api_key:
                available.append(name)
        
        if not available:
            # If no keys, return all so we can fallback to mock
            return list(self.PROVIDERS.keys())
            
        return available
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        发送 Chat Completion 请求到 LLM API
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            provider: 厂商名称，为 None 时使用默认厂商
            model: 模型名称，为 None 时使用默认模型
            temperature: 温度参数 (0-1)
            max_tokens: 最大生成 token 数
            
        Returns:
            生成的文本内容，失败时返回 None
        """
        # 选择厂商
        provider_name = provider or self.default_provider
        if provider_name not in self.PROVIDERS:
            logger.warning(f"厂商 {provider_name} 不存在，使用默认厂商 {self.default_provider}")
            provider_name = self.default_provider
            
        provider_config = self.PROVIDERS[provider_name]
        
        # 获取配置
        base_url = provider_config["base_url"]
        api_key_name = provider_config["api_key_name"]
        api_key = getattr(settings, api_key_name, None)
        
        # 选择模型：优先使用参数指定的，其次使用用户配置的，最后使用厂商默认
        if model is None:
            if self.default_model and provider_name == self.default_provider:
                model = self.default_model
            else:
                model = provider_config["default_model"]
            
        # Special handling for providers that might need it
        if provider_name == "minimax":
             # MiniMax sometimes needs group_id in URL or specific headers, 
             # but standard OpenAI compatible endpoint usually works with just API key.
             pass

        if not api_key:
            logger.warning(f"No API key provided for {provider_name} ({api_key_name}). Using MOCK response.")
            return self._mock_response(messages)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            logger.info(f"Calling LLM Provider: {provider_name} | Model: {model}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Error from {provider_name}: {response.status_code} - {response.text}")
                    # Fallback to mock if API fails? Or just return None.
                    # For now, return None to indicate failure.
                    return None
                    
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"LLM response received from {provider_name}: {len(content)} characters")
                    return content
                else:
                    logger.error(f"Unexpected response format from {provider_name}: {data}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout calling LLM API {provider_name} at {base_url}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM API {provider_name}: {e}", exc_info=True)
            return None

    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a mock response based on the user prompt.
        """
        import random
        
        last_message = messages[-1]["content"]
        
        if "情感倾向" in last_message:
            # Return a random sentiment score
            return str(random.randint(-80, 80))
            
        elif "关键词" in last_message:
            # Return random keywords
            keywords = ["Politics", "Economy", "Global", "Tech", "Society", "Future", "Innovation", "Crisis"]
            selected = random.sample(keywords, 3)
            return str(selected).replace("'", '"')
            
        elif "分类" in last_message:
            # Return a random category
            categories = ["政治", "经济", "军事", "科技", "社会", "文化", "国际关系"]
            return random.choice(categories)
            
        return "This is a mock response from the AI assistant."

# Global instance
llm_client = LLMClient()
