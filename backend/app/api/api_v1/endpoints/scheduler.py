"""
调度器配置 API 端点
提供定时任务频率的查询和设置接口
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.scheduler_config import scheduler_config
from app.core.logger import logger

router = APIRouter()


class SchedulerConfigResponse(BaseModel):
    """调度器配置响应模型"""
    fetch_interval_hours: int = Field(..., description="新闻采集间隔（小时）")
    analyze_interval_minutes: int = Field(..., description="新闻分析间隔（分钟）")
    fetch_enabled: bool = Field(..., description="是否启用自动采集")
    analyze_enabled: bool = Field(..., description="是否启用自动分析")
    analyze_batch_size: int = Field(..., description="每次分析的新闻数量")


class SchedulerConfigUpdate(BaseModel):
    """调度器配置更新请求模型"""
    fetch_interval_hours: Optional[int] = Field(None, ge=1, le=24, description="新闻采集间隔（小时），范围 1-24")
    analyze_interval_minutes: Optional[int] = Field(None, ge=5, le=120, description="新闻分析间隔（分钟），范围 5-120")
    fetch_enabled: Optional[bool] = Field(None, description="是否启用自动采集")
    analyze_enabled: Optional[bool] = Field(None, description="是否启用自动分析")
    analyze_batch_size: Optional[int] = Field(None, ge=10, le=100, description="每次分析的新闻数量，范围 10-100")


@router.get("/config", response_model=SchedulerConfigResponse)
async def get_scheduler_config() -> Any:
    """
    获取当前调度器配置
    
    返回定时任务的频率设置，包括：
    - 新闻采集间隔（小时）
    - 新闻分析间隔（分钟）
    - 是否启用自动采集/分析
    - 每次分析的新闻数量
    """
    try:
        config = scheduler_config.get_config()
        return SchedulerConfigResponse(**config)
    except Exception as e:
        logger.error(f"获取调度器配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config", response_model=SchedulerConfigResponse)
async def update_scheduler_config(config_update: SchedulerConfigUpdate) -> Any:
    """
    更新调度器配置
    
    更新定时任务的频率设置。只需要传入需要修改的字段。
    
    注意：配置更新后，需要重启 Celery Beat 才能生效。
    """
    try:
        # 获取当前配置
        current_config = scheduler_config.get_config()
        
        # 合并更新
        update_dict = config_update.model_dump(exclude_none=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="没有提供任何更新字段")
        
        new_config = {**current_config, **update_dict}
        
        # 保存配置
        success = scheduler_config.set_config(new_config)
        if not success:
            raise HTTPException(status_code=500, detail="保存配置失败")
        
        logger.info(f"调度器配置已更新: {update_dict}")
        
        # 返回更新后的配置
        return SchedulerConfigResponse(**scheduler_config.get_config())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新调度器配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    获取调度器状态信息
    
    返回当前配置和计算后的实际间隔时间
    """
    try:
        config = scheduler_config.get_config()
        
        return {
            "config": config,
            "computed": {
                "fetch_interval_seconds": scheduler_config.get_fetch_interval_seconds(),
                "analyze_interval_seconds": scheduler_config.get_analyze_interval_seconds(),
                "fetch_interval_display": f"每 {config['fetch_interval_hours']} 小时",
                "analyze_interval_display": f"每 {config['analyze_interval_minutes']} 分钟"
            },
            "message": "配置修改后需要重启 Celery Beat 才能生效"
        }
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取状态失败")

