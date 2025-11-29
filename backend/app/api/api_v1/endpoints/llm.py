from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from app.core.llm_client import llm_client
from app.core.logger import logger
from pydantic import BaseModel

router = APIRouter()

# LLM 厂商显示名称映射
PROVIDER_DISPLAY_NAMES = {
    "deepseek": "DeepSeek",
    "moonshot": "Moonshot (月之暗面)",
    "qwen": "通义千问",
    "baichuan": "百川智能",
    "zhipu": "智谱 AI",
    "minimax": "MiniMax"
}

class LLMProviderInfo(BaseModel):
    """LLM Provider information."""
    name: str
    display_name: str
    base_url: str
    default_model: str
    available: bool

class LLMConfigUpdate(BaseModel):
    """LLM configuration update request."""
    provider: str
    model: Optional[str] = None

@router.get("/providers", response_model=List[LLMProviderInfo])
async def get_llm_providers() -> Any:
    """
    获取所有可用的 LLM 厂商列表
    Returns:
        LLMProviderInfo 列表，包含厂商名称、显示名、API 地址、默认模型、是否可用
    """
    from app.core.config import settings
    
    providers_info = []
    
    for name, config in llm_client.PROVIDERS.items():
        api_key = getattr(settings, config["api_key_name"], None)
        
        providers_info.append(LLMProviderInfo(
            name=name,
            display_name=PROVIDER_DISPLAY_NAMES.get(name, name.capitalize()),
            base_url=config["base_url"],
            default_model=config["default_model"],
            available=bool(api_key)
        ))
    
    return providers_info

@router.get("/current-config")
async def get_current_llm_config() -> Dict[str, Any]:
    """
    获取当前 LLM 配置
    Returns:
        包含当前厂商、模型、可用厂商列表的配置信息
    """
    # 获取当前厂商配置
    provider_config = llm_client.PROVIDERS.get(llm_client.default_provider, {})
    
    # 确定当前使用的模型
    current_model = (
        llm_client.default_model 
        or provider_config.get("default_model", "")
    )
    
    return {
        "default_provider": llm_client.default_provider,
        "default_model": current_model,
        "available_providers": llm_client.get_available_providers()
    }

@router.post("/update-config")
async def update_llm_config(config: LLMConfigUpdate) -> Dict[str, Any]:
    """
    更新 LLM 配置（修改默认厂商和模型）
    Args:
        config: 包含 provider 和 model 的配置对象
    Returns:
        更新结果，包含状态、厂商、模型信息
    """
    if config.provider not in llm_client.PROVIDERS:
        raise HTTPException(status_code=400, detail=f"无效的厂商: {config.provider}")
    
    # 更新默认厂商和模型配置
    llm_client.set_config(config.provider, config.model)
    
    # 确定实际使用的模型
    actual_model = config.model or llm_client.PROVIDERS[config.provider]["default_model"]
    
    logger.info(f"LLM 配置已更新: provider={config.provider}, model={actual_model}")
    
    return {
        "status": "success",
        "provider": config.provider,
        "model": actual_model,
        "message": f"配置已更新，新的分析任务将使用 {config.provider} 的 {actual_model} 模型"
    }

@router.get("/models/{provider}")
async def get_provider_models(provider: str) -> Dict[str, Any]:
    """
    获取指定厂商的可用模型列表
    Args:
        provider: 厂商名称 (如: deepseek, qwen, moonshot 等)
    Returns:
        包含厂商名称、默认模型、可用模型列表的字典
    """
    if provider not in llm_client.PROVIDERS:
        raise HTTPException(status_code=404, detail=f"厂商不存在: {provider}")
    
    provider_config = llm_client.PROVIDERS[provider]
    
    # 各厂商支持的模型列表
    # TODO: 未来可以从厂商 API 动态获取
    models_map = {
        "deepseek": [
            "deepseek-chat",           # 通用对话模型
            "deepseek-coder",          # 代码专用模型
            "deepseek-reasoner"        # 推理增强模型 (R1)
        ],
        "moonshot": [
            "moonshot-v1-8k",          # 8K 上下文
            "moonshot-v1-32k",         # 32K 上下文
            "moonshot-v1-128k"         # 128K 长上下文
        ],
        "qwen": [
            "qwen-turbo",              # 快速版本
            "qwen-plus",               # 增强版本
            "qwen-max",                # 最强版本
            "qwen-max-longcontext",    # 长上下文版本
            "qwen-vl-plus",            # 视觉语言模型
            "qwen-vl-max"              # 视觉语言增强版
        ],
        "baichuan": [
            "Baichuan2-Turbo",         # Turbo 版本
            "Baichuan2-Turbo-192k",    # 192K 长上下文
            "Baichuan3-Turbo",         # Baichuan3 版本
            "Baichuan3-Turbo-128k",    # 128K 上下文
            "Baichuan4"                # 最新版本
        ],
        "zhipu": [
            "glm-4",                   # GLM-4 标准版
            "glm-4-plus",              # GLM-4 增强版
            "glm-4-air",               # GLM-4 轻量版
            "glm-4-airx",              # GLM-4 极速版
            "glm-4-flash",             # GLM-4 闪电版
            "glm-4v",                  # 视觉模型
            "glm-3-turbo"              # GLM-3 快速版
        ],
        "minimax": [
            "abab5.5-chat",            # ABAB 5.5 对话版
            "abab5.5s-chat",           # ABAB 5.5 精简版
            "abab6-chat",              # ABAB 6 对话版
            "abab6.5-chat",            # ABAB 6.5 对话版
            "abab6.5s-chat"            # ABAB 6.5 精简版
        ]
    }
    
    return {
        "provider": provider,
        "default_model": provider_config["default_model"],
        "available_models": models_map.get(provider, [provider_config["default_model"]])
    }
