import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logger import logger

class LLMClient:
    """
    Unified LLM client supporting multiple providers (DeepSeek, Qwen, OpenAI-compatible APIs)
    """
    
    def __init__(self):
        self.timeout = 30.0
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Send chat completion request to LLM API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            api_key: API key (defaults to settings)
            base_url: API base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if error
        """
        if not api_key:
            # Try to get from settings based on base_url
            if "deepseek" in base_url.lower():
                api_key = settings.DEEPSEEK_API_KEY
            elif "qwen" in base_url.lower() or "dashscope" in base_url.lower():
                api_key = settings.QWEN_API_KEY
            else:
                api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            logger.error(f"No API key provided for {base_url}")
            return None
        
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"LLM response received: {len(content)} characters")
                    return content
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout calling LLM API at {base_url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from LLM API: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}", exc_info=True)
            return None

# Global instance
llm_client = LLMClient()
