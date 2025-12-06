"""
国际化(i18n)API端点 - 简化版本
提供多语言支持和翻译功能
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.i18n import i18n_manager, Language

router = APIRouter()


class LanguageInfo(BaseModel):
    """语言信息模型"""
    code: str
    name: str
    native_name: str
    flag: str


@router.get("/languages", response_model=List[LanguageInfo])
async def get_available_languages():
    """
    获取可用语言列表
    """
    return i18n_manager.get_available_languages()


@router.get("/translate")
async def translate_text(
    key: str = Query(..., description="翻译键"),
    language: Optional[str] = Query(None, description="目标语言代码"),
    domain: str = Query("api_responses", description="翻译域")
):
    """
    翻译文本（GET方式）
    """
    try:
        # 解析语言
        target_language = None
        if language:
            try:
                target_language = i18n_manager.validate_language(language)
            except ValueError:
                return {"error": f"Unsupported language: {language}"}

        # 解析域
        try:
            from app.core.i18n import TranslationDomain
            target_domain = TranslationDomain(domain)
        except ValueError:
            return {"error": f"Invalid domain: {domain}"}

        # 执行翻译
        translated_text = i18n_manager.translate(
            key=key,
            language=target_language,
            domain=target_domain
        )

        return {
            "key": key,
            "translated_text": translated_text,
            "language": target_language.value if target_language else i18n_manager.default_language.value,
            "domain": target_domain.value
        }

    except Exception as e:
        return {"error": f"Translation failed: {str(e)}"}


@router.get("/categories/localized")
async def get_localized_categories(
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    获取本地化的新闻类别
    """
    try:
        target_language = None
        if language:
            target_language = i18n_manager.validate_language(language)

        categories = i18n_manager.get_localized_categories(target_language)

        return {
            "language": target_language.value if target_language else i18n_manager.default_language.value,
            "categories": categories
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get localized categories: {str(e)}"}


@router.get("/sentiment/labels")
async def get_localized_sentiment_labels(
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    获取本地化的情感标签
    """
    try:
        target_language = None
        if language:
            target_language = i18n_manager.validate_language(language)

        sentiment_labels = i18n_manager.get_localized_sentiment_labels(target_language)

        return {
            "language": target_language.value if target_language else i18n_manager.default_language.value,
            "sentiment_labels": sentiment_labels
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get localized sentiment labels: {str(e)}"}


@router.get("/format/currency")
async def format_currency(
    amount: float = Query(..., description="金额"),
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    格式化货币
    """
    try:
        target_language = None
        if language:
            target_language = i18n_manager.validate_language(language)

        formatted_currency = i18n_manager.format_currency(amount, target_language)

        return {
            "amount": amount,
            "formatted_currency": formatted_currency,
            "language": target_language.value if target_language else i18n_manager.default_language.value
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to format currency: {str(e)}"}


@router.get("/format/number")
async def format_number(
    number: float = Query(..., description="数字"),
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    格式化数字
    """
    try:
        target_language = None
        if language:
            target_language = i18n_manager.validate_language(language)

        formatted_number = i18n_manager.format_number(number, target_language)

        return {
            "number": number,
            "formatted_number": formatted_number,
            "language": target_language.value if target_language else i18n_manager.default_language.value
        }

    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to format number: {str(e)}"}


@router.get("/status")
async def get_i18n_status():
    """
    获取国际化状态
    """
    return {
        "success": True,
        "status": {
            "default_language": i18n_manager.default_language.value,
            "supported_languages": [lang.value for lang in i18n_manager.supported_languages],
            "translation_domains": ["api_responses", "error_messages", "ui_labels", "categories", "analysis", "map", "auth"]
        }
    }