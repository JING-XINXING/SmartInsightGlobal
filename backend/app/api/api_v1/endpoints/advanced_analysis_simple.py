"""
简化版高级分析API端点
避免循环依赖，提供核心分析功能
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import time

from app.core.advanced_nlp import advanced_nlp_analyzer
from app.core.logger import logger

router = APIRouter()


class SimpleAnalysisRequest(BaseModel):
    """简化分析请求"""
    title: str = Field(..., description="新闻标题")
    content: str = Field(..., description="新闻内容")
    analysis_type: str = Field("comprehensive", pattern="^(sentiment|entities|trend|comprehensive)$")


class SimpleBatchRequest(BaseModel):
    """简化批量分析请求"""
    items: List[Dict[str, str]] = Field(..., description="新闻项目列表，每个包含title和content")


@router.post("/analyze-simple")
async def simple_analysis(request: SimpleAnalysisRequest):
    """
    简化的新闻分析端点，无需认证
    """
    start_time = time.time()

    try:
        logger.info(f"Starting simple analysis for: {request.title[:50]}...")

        # 根据分析类型执行相应分析
        if request.analysis_type == "sentiment":
            sentiment_score, details = await advanced_nlp_analyzer.analyze_sentiment_multi_model(
                request.title, request.content
            )
            result = {
                "sentiment_score": sentiment_score,
                "sentiment_details": details
            }

        elif request.analysis_type == "entities":
            entities = await advanced_nlp_analyzer.extract_entities_advanced(
                request.title, request.content
            )
            result = {
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.type.value,
                        "confidence": entity.confidence
                    }
                    for entity in entities
                ]
            }

        elif request.analysis_type == "trend":
            prediction = await advanced_nlp_analyzer.predict_sentiment_trend(
                request.title, request.content
            )
            result = {
                "current_sentiment": prediction.current_sentiment,
                "predicted_trend": prediction.predicted_trend,
                "trend_confidence": prediction.trend_confidence,
                "key_factors": prediction.key_factors
            }

        else:  # comprehensive
            result = await advanced_nlp_analyzer.analyze_comprehensive(
                request.title, request.content
            )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "analysis_type": request.analysis_type,
            "results": result,
            "processing_time": processing_time
        }

    except Exception as e:
        logger.error(f"Simple analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch-analyze-simple")
async def simple_batch_analysis(request: SimpleBatchRequest):
    """
    简化的批量分析端点，无需认证
    """
    if len(request.items) > 20:  # 限制批量大小
        raise HTTPException(status_code=400, detail="Too many items (max 20)")

    start_time = time.time()

    try:
        logger.info(f"Starting simple batch analysis with {len(request.items)} items")

        results = []
        for i, item in enumerate(request.items):
            title = item.get("title", "")
            content = item.get("content", "")

            if not title or not content:
                results.append({
                    "item_index": i,
                    "success": False,
                    "error": "Title and content are required"
                })
                continue

            try:
                # 执行综合分析
                analysis_result = await advanced_nlp_analyzer.analyze_comprehensive(
                    title, content
                )

                results.append({
                    "item_index": i,
                    "success": True,
                    "analysis": {
                        "sentiment_score": analysis_result.get("sentiment", {}).get("score"),
                        "main_entities": [e.get("text") for e in analysis_result.get("entities", [])[:3]],
                        "predicted_trend": analysis_result.get("prediction", {}).get("trend"),
                        "language": analysis_result.get("metadata", {}).get("language")
                    }
                })

            except Exception as e:
                results.append({
                    "item_index": i,
                    "success": False,
                    "error": str(e)
                })

        processing_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])

        return {
            "success": True,
            "batch_id": f"batch_{int(time.time())}",
            "total_items": len(request.items),
            "success_count": success_count,
            "error_count": len(results) - success_count,
            "processing_time": processing_time,
            "results": results
        }

    except Exception as e:
        logger.error(f"Simple batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/analysis-capabilities")
async def get_analysis_capabilities():
    """
    获取分析能力信息
    """
    return {
        "success": True,
        "capabilities": {
            "sentiment_analysis": {
                "available": True,
                "models": ["keyword_based", "llm_based", "rule_based", "emotion_based"],
                "languages": ["zh-CN", "en-US"]
            },
            "entity_extraction": {
                "available": True,
                "entity_types": ["person", "organization", "location", "event", "product"],
                "max_confidence": 1.0
            },
            "trend_prediction": {
                "available": True,
                "horizons": ["short_term", "medium_term", "long_term"],
                "factors": ["historical_sentiment", "content_features", "external_factors"]
            },
            "comprehensive_analysis": {
                "available": True,
                "includes": ["sentiment", "entities", "relations", "prediction", "metadata"]
            }
        },
        "limits": {
            "max_batch_size": 20,
            "max_content_length": 10000,
            "supported_languages": ["zh-CN", "en-US"]
        }
    }


@router.get("/health")
async def analysis_health_check():
    """
    分析系统健康检查
    """
    try:
        # 简单测试分析器是否正常工作
        test_result = await advanced_nlp_analyzer.analyze_sentiment_multi_model(
            "Test", "This is a test."
        )

        return {
            "status": "healthy",
            "analyzer_working": True,
            "test_analysis_score": test_result[0] if test_result else None,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Analysis health check failed: {e}")
        return {
            "status": "unhealthy",
            "analyzer_working": False,
            "error": str(e),
            "timestamp": time.time()
        }