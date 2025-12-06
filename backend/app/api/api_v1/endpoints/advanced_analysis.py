"""
高级分析API端点
提供高级NLP分析、情感预测、实体识别等功能
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field

from app.api.api_v1.endpoints.auth import get_current_user, require_permission
from app.core.advanced_nlp import advanced_nlp_analyzer
from app.core.logger import logger
from app.db.session import get_db
from app.models.news import News
from app.models.user import User


router = APIRouter()


# 请求和响应模型
class AdvancedAnalysisRequest(BaseModel):
    """高级分析请求"""
    news_id: Optional[int] = None
    title: str
    content: str
    enable_sentiment_prediction: bool = True
    enable_entity_extraction: bool = True
    enable_relation_extraction: bool = True
    historical_sentiments: Optional[List[float]] = None


class AdvancedAnalysisResponse(BaseModel):
    """高级分析响应"""
    success: bool
    analysis_id: Optional[str] = None
    results: Dict[str, Any]
    processing_time: float
    analysis_metadata: Dict[str, Any]


class SentimentAnalysisRequest(BaseModel):
    """情感分析请求"""
    title: str
    content: str
    use_multi_model: bool = True


class EntityExtractionRequest(BaseModel):
    """实体提取请求"""
    title: str
    content: str
    include_relations: bool = True


class SentimentTrendRequest(BaseModel):
    """情感趋势预测请求"""
    title: str
    content: str
    historical_sentiments: Optional[List[float]] = None
    prediction_horizon: str = Field("short_term", regex="^(short_term|medium_term|long_term)$")


class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""
    news_items: List[Dict[str, Any]]
    analysis_options: Dict[str, bool] = Field(default_factory=lambda: {
        "sentiment": True,
        "entities": True,
        "relations": True,
        "prediction": True
    })


@router.post("/analyze", response_model=AdvancedAnalysisResponse)
async def analyze_news_advanced(
    request: AdvancedAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    执行高级新闻分析

    需要权限: analyze_news
    """
    # 权限检查
    require_permission(current_user, "analyze_news")

    start_time = datetime.now(timezone.utc)
    analysis_id = f"analysis_{start_time.strftime('%Y%m%d_%H%M%S')}_{current_user.id}"

    try:
        logger.info(f"Starting advanced analysis {analysis_id} for user {current_user.id}")

        # 如果提供了news_id，先从数据库获取新闻
        if request.news_id:
            result = await db.execute(
                select(News).where(News.id == request.news_id)
            )
            news_item = result.scalar_one_or_none()
            if not news_item:
                raise HTTPException(status_code=404, detail="News item not found")

            title = news_item.title
            content = news_item.content
        else:
            title = request.title
            content = request.content

        # 执行综合分析
        analysis_results = await advanced_nlp_analyzer.analyze_comprehensive(
            title=title,
            content=content,
            historical_sentiments=request.historical_sentiments
        )

        # 计算处理时间
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # 如果提供了news_id，更新数据库记录
        if request.news_id and request.news_id:
            await _update_news_with_advanced_analysis(
                db, request.news_id, analysis_results, processing_time
            )

        response = AdvancedAnalysisResponse(
            success=True,
            analysis_id=analysis_id,
            results=analysis_results,
            processing_time=processing_time,
            analysis_metadata=analysis_results.get("analysis_metadata", {})
        )

        logger.info(f"Advanced analysis {analysis_id} completed in {processing_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f"Advanced analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/sentiment", response_model=Dict[str, Any])
async def analyze_sentiment_advanced(
    request: SentimentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    高级情感分析

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        if request.use_multi_model:
            sentiment_score, model_details = await advanced_nlp_analyzer.analyze_sentiment_multi_model(
                request.title, request.content
            )

            return {
                "sentiment_score": sentiment_score,
                "model_details": model_details,
                "analysis_type": "multi_model"
            }
        else:
            sentiment_score = await advanced_nlp_analyzer._sentiment_analysis_llm(
                request.title, request.content
            )

            return {
                "sentiment_score": sentiment_score,
                "analysis_type": "llm_only"
            }

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/entities", response_model=Dict[str, Any])
async def extract_entities_advanced(
    request: EntityExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    高级实体识别

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        # 提取实体
        entities = await advanced_nlp_analyzer.extract_entities_advanced(
            request.title, request.content
        )

        result = {
            "entities": [
                {
                    "text": entity.text,
                    "type": entity.type.value,
                    "confidence": entity.confidence,
                    "metadata": entity.metadata
                }
                for entity in entities
            ]
        }

        # 如果需要，提取关系
        if request.include_relations and entities:
            relations = await advanced_nlp_analyzer.extract_relations(
                request.title, request.content, entities
            )

            result["relations"] = [
                {
                    "subject": relation.subject,
                    "predicate": relation.predicate,
                    "object": relation.object,
                    "confidence": relation.confidence
                }
                for relation in relations
            ]

        return result

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@router.post("/predict-trend", response_model=Dict[str, Any])
async def predict_sentiment_trend(
    request: SentimentTrendRequest,
    current_user: User = Depends(get_current_user)
):
    """
    情感趋势预测

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        prediction = await advanced_nlp_analyzer.predict_sentiment_trend(
            request.title, request.content, request.historical_sentiments
        )

        return {
            "current_sentiment": prediction.current_sentiment,
            "predicted_trend": prediction.predicted_trend,
            "trend_confidence": prediction.trend_confidence,
            "prediction_horizon": prediction.prediction_horizon,
            "key_factors": prediction.key_factors
        }

    except Exception as e:
        logger.error(f"Sentiment trend prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trend prediction failed: {str(e)}")


@router.post("/batch-analyze", response_model=Dict[str, Any])
async def batch_analyze_news(
    request: BatchAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量分析新闻

    需要权限: analyze_news
    """
    require_permission(current_user, "analyze_news")

    if len(request.news_items) > 50:  # 限制批量大小
        raise HTTPException(status_code=400, detail="Too many news items for batch processing (max 50)")

    start_time = datetime.now(timezone.utc)
    batch_id = f"batch_{start_time.strftime('%Y%m%d_%H%M%S')}_{current_user.id}"

    try:
        logger.info(f"Starting batch analysis {batch_id} with {len(request.news_items)} items")

        results = []
        errors = []

        # 并行处理新闻项目
        import asyncio
        tasks = []

        for item in request.news_items:
            task = _process_single_news_item(item, request.analysis_options)
            tasks.append(task)

        # 等待所有任务完成
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                errors.append({
                    "item_index": i,
                    "error": str(result)
                })
            else:
                results.append({
                    "item_index": i,
                    "analysis": result
                })

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        batch_result = {
            "batch_id": batch_id,
            "success_count": len(results),
            "error_count": len(errors),
            "total_items": len(request.news_items),
            "processing_time": processing_time,
            "results": results,
            "errors": errors,
            "average_sentiment": sum(r["analysis"].get("sentiment", {}).get("score", 0) for r in results) / len(results) if results else 0
        }

        logger.info(f"Batch analysis {batch_id} completed: {len(results)} success, {len(errors)} errors")
        return batch_result

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/news/{news_id}/analysis", response_model=Dict[str, Any])
async def get_news_analysis(
    news_id: int = Path(..., description="新闻ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取新闻的详细分析结果

    需要权限: read_news
    """
    require_permission(current_user, "read_news")

    try:
        result = await db.execute(
            select(News).where(News.id == news_id)
        )
        news_item = result.scalar_one_or_none()

        if not news_item:
            raise HTTPException(status_code=404, detail="News item not found")

        # 构建分析结果
        analysis_data = {
            "basic_analysis": {
                "sentiment_score": news_item.sentiment_score,
                "sentiment_confidence": news_item.sentiment_confidence,
                "keywords": news_item.keywords,
                "category": news_item.category,
                "location": news_item.location
            },
            "advanced_analysis": {
                "sentiment_details": news_item.sentiment_details,
                "entities": news_item.entities,
                "relations": news_item.relations,
                "emotions": news_item.emotions
            },
            "prediction": {
                "sentiment_trend": news_item.sentiment_trend,
                "trend_confidence": news_item.trend_confidence,
                "trend_horizon": news_item.trend_horizon,
                "trend_factors": news_item.trend_factors
            },
            "metadata": {
                "text_length": news_item.text_length,
                "language": news_item.language,
                "readability_score": news_item.readability_score,
                "analysis_quality": news_item.analysis_quality,
                "analysis_version": news_item.analysis_version,
                "analysis_time": news_item.analysis_time
            },
            "raw_data": news_item.raw_analysis_data
        }

        return {
            "news_id": news_id,
            "title": news_item.title,
            "analysis": analysis_data
        }

    except Exception as e:
        logger.error(f"Failed to get news analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")


async def _process_single_news_item(item: Dict[str, Any], options: Dict[str, bool]) -> Dict[str, Any]:
    """处理单个新闻项目的分析"""
    title = item.get("title", "")
    content = item.get("content", "")

    if not title or not content:
        raise ValueError("Title and content are required")

    # 根据选项执行相应的分析
    results = {}

    if options.get("sentiment", True):
        sentiment_score, sentiment_details = await advanced_nlp_analyzer.analyze_sentiment_multi_model(
            title, content
        )
        results["sentiment"] = {
            "score": sentiment_score,
            "details": sentiment_details
        }

    if options.get("entities", True):
        entities = await advanced_nlp_analyzer.extract_entities_advanced(title, content)
        results["entities"] = [
            {
                "text": entity.text,
                "type": entity.type.value,
                "confidence": entity.confidence
            }
            for entity in entities
        ]

    if options.get("relations", True) and results.get("entities"):
        relations = await advanced_nlp_analyzer.extract_relations(
            title, content, entities
        )
        results["relations"] = [
            {
                "subject": relation.subject,
                "predicate": relation.predicate,
                "object": relation.object,
                "confidence": relation.confidence
            }
            for relation in relations
        ]

    if options.get("prediction", True):
        prediction = await advanced_nlp_analyzer.predict_sentiment_trend(title, content)
        results["prediction"] = {
            "trend": prediction.predicted_trend,
            "confidence": prediction.trend_confidence,
            "horizon": prediction.prediction_horizon,
            "factors": prediction.key_factors
        }

    return results


async def _update_news_with_advanced_analysis(
    db: AsyncSession, news_id: int, analysis_results: Dict[str, Any], processing_time: float
):
    """更新新闻记录的高级分析结果"""
    try:
        # 获取新闻记录
        result = await db.execute(
            select(News).where(News.id == news_id)
        )
        news_item = result.scalar_one_or_one()

        if not news_item:
            return

        # 更新基础分析字段
        if "sentiment" in analysis_results:
            sentiment_data = analysis_results["sentiment"]
            news_item.sentiment_score = sentiment_data.get("score")
            news_item.sentiment_confidence = sentiment_data.get("details", {}).get("llm_based", {}).get("confidence", 0.8)
            news_item.sentiment_details = sentiment_data.get("details")

        # 更新高级分析字段
        if "entities" in analysis_results:
            news_item.entities = analysis_results["entities"]

        if "relations" in analysis_results:
            news_item.relations = analysis_results["relations"]

        # 更新预测字段
        if "prediction" in analysis_results:
            prediction_data = analysis_results["prediction"]
            news_item.sentiment_trend = prediction_data.get("trend")
            news_item.trend_confidence = prediction_data.get("confidence")
            news_item.trend_horizon = prediction_data.get("horizon")
            news_item.trend_factors = prediction_data.get("factors")

        # 更新元数据
        news_item.keywords = analysis_results.get("keywords")
        news_item.analysis_version = "1.0"
        news_item.analysis_time = processing_time
        news_item.raw_analysis_data = analysis_results

        # 计算分析质量分数
        quality_score = _calculate_analysis_quality(analysis_results)
        news_item.analysis_quality = quality_score

        await db.commit()
        logger.info(f"Updated news {news_id} with advanced analysis results")

    except Exception as e:
        logger.error(f"Failed to update news with analysis results: {e}")
        await db.rollback()


def _calculate_analysis_quality(analysis_results: Dict[str, Any]) -> float:
    """计算分析质量分数"""
    quality_score = 0.0
    max_score = 0.0

    # 情感分析质量
    if "sentiment" in analysis_results:
        sentiment = analysis_results["sentiment"]
        if "details" in sentiment and sentiment["details"]:
            # 检查是否有多个模型的结果
            model_count = len(sentiment["details"])
            quality_score += min(model_count / 3.0, 1.0) * 0.3  # 最多30%权重
        max_score += 0.3

    # 实体识别质量
    if "entities" in analysis_results:
        entities = analysis_results["entities"]
        if len(entities) > 0:
            # 检查实体置信度
            avg_confidence = sum(e.get("confidence", 0) for e in entities) / len(entities)
            quality_score += avg_confidence * 0.3  # 30%权重
        max_score += 0.3

    # 关系识别质量
    if "relations" in analysis_results:
        relations = analysis_results["relations"]
        if len(relations) > 0:
            quality_score += 0.2  # 20%权重
        max_score += 0.2

    # 预测质量
    if "prediction" in analysis_results:
        prediction = analysis_results["prediction"]
        if prediction.get("confidence", 0) > 0.5:
            quality_score += prediction["confidence"] * 0.2  # 20%权重
        max_score += 0.2

    return quality_score / max_score if max_score > 0 else 0.0