"""
国际化(i18n)API端点
提供多语言支持和翻译功能
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.i18n import i18n_manager, Language, TranslationDomain, get_current_language
from app.api.api_v1.endpoints.auth import get_current_user, require_permission
from app.models.user import User

router = APIRouter()


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    key: str = Field(..., description="翻译键")
    language: Optional[str] = Field(None, description="目标语言代码")
    domain: Optional[str] = Field("api_responses", description="翻译域")
    parameters: Optional[Dict[str, Any]] = Field(None, description="格式化参数")


class TranslationResponse(BaseModel):
    """翻译响应模型"""
    key: str
    translated_text: str
    language: str
    domain: str


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

    Returns:
        可用语言信息列表
    """
    return i18n_manager.get_available_languages()


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    http_request: Request = None
):
    """
    翻译文本

    Args:
        request: 翻译请求
        http_request: HTTP请求对象

    Returns:
        翻译结果
    """
    try:
        # 解析语言
        language = None
        if request.language:
            try:
                language = i18n_manager.validate_language(request.language)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")

        # 解析域
        try:
            domain = TranslationDomain(request.domain) if request.domain else TranslationDomain.API_RESPONSES
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {request.domain}")

        # 如果未指定语言，从请求中检测
        if not language and http_request:
            headers = dict(http_request.headers)
            query_params = dict(http_request.query_params)
            language = get_current_language(headers, query_params)

        # 执行翻译
        parameters = request.parameters or {}
        translated_text = i18n_manager.translate(
            key=request.key,
            language=language,
            domain=domain,
            **parameters
        )

        return TranslationResponse(
            key=request.key,
            translated_text=translated_text,
            language=language.value if language else i18n_manager.default_language.value,
            domain=domain.value
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/translate")
async def translate_get(
    key: str = Query(..., description="翻译键"),
    language: Optional[str] = Query(None, description="目标语言代码"),
    domain: str = Query("api_responses", description="翻译域"),
    http_request: Request = None
):
    """
    翻译文本（GET方式）

    Args:
        key: 翻译键
        language: 目标语言代码
        domain: 翻译域
        http_request: HTTP请求对象

    Returns:
        翻译结果
    """
    try:
        # 解析语言
        target_language = None
        if language:
            try:
                target_language = i18n_manager.validate_language(language)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

        # 解析域
        try:
            target_domain = TranslationDomain(domain)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

        # 如果未指定语言，从请求中检测
        if not target_language and http_request:
            headers = dict(http_request.headers)
            query_params = dict(http_request.query_params)
            target_language = get_current_language(headers, query_params)

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/translations/{language}")
async def get_language_translations(
    language: str,
    domain: Optional[str] = Query(None, description="翻译域"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定语言的翻译数据

    Args:
        language: 语言代码
        domain: 翻译域（可选）
        current_user: 当前用户

    Returns:
        翻译数据字典
    """
    try:
        # 验证语言
        target_language = i18n_manager.validate_language(language)

        # 解析域
        target_domain = None
        if domain:
            try:
                target_domain = TranslationDomain(domain)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

        # 获取翻译数据
        translations = i18n_manager.get_translation_keys(target_language, target_domain)

        return {
            "language": language,
            "domain": domain,
            "translations": translations
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get translations: {str(e)}")


@router.get("/categories/localized")
async def get_localized_categories(
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    获取本地化的新闻类别

    Args:
        language: 语言代码

    Returns:
        本地化的新闻类别
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get localized categories: {str(e)}")


@router.get("/sentiment/labels")
async def get_localized_sentiment_labels(
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    获取本地化的情感标签

    Args:
        language: 语言代码

    Returns:
        本地化的情感标签
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get localized sentiment labels: {str(e)}")


@router.get("/format/currency")
async def format_currency(
    amount: float = Query(..., description="金额"),
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    格式化货币

    Args:
        amount: 金额
        language: 语言代码

    Returns:
        格式化的货币字符串
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to format currency: {str(e)}")


@router.get("/format/number")
async def format_number(
    number: float = Query(..., description="数字"),
    language: Optional[str] = Query(None, description="语言代码")
):
    """
    格式化数字

    Args:
        number: 数字
        language: 语言代码

    Returns:
        格式化的数字字符串
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to format number: {str(e)}")


@router.post("/add-translation")
async def add_translation(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    添加翻译（需要管理员权限）

    Args:
        request: 翻译请求
        current_user: 当前用户

    Returns:
        添加结果
    """
    require_permission(current_user, "manage_system")

    try:
        # 解析语言
        language = i18n_manager.validate_language(request.language or i18n_manager.default_language.value)

        # 解析域
        domain = TranslationDomain(request.domain or "api_responses")

        # 添加翻译
        i18n_manager.add_translation(
            key=request.key,
            value=request.parameters.get("value", request.key) if request.parameters else request.key,
            language=language,
            domain=domain
        )

        return {
            "success": True,
            "message": f"Translation added successfully for {request.key} in {language.value}",
            "key": request.key,
            "language": language.value,
            "domain": domain.value
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add translation: {str(e)}")


@router.get("/export/{language}")
async def export_translations(
    language: str,
    domain: Optional[str] = Query(None, description="翻译域"),
    current_user: User = Depends(get_current_user)
):
    """
    导出翻译数据（需要管理员权限）

    Args:
        language: 语言代码
        domain: 翻译域（可选）
        current_user: 当前用户

    Returns:
        翻译数据
    """
    require_permission(current_user, "manage_system")

    try:
        # 验证语言
        target_language = i18n_manager.validate_language(language)

        # 解析域
        target_domain = None
        if domain:
            try:
                target_domain = TranslationDomain(domain)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")

        # 导出翻译数据
        translations = i18n_manager.export_translations(target_language, target_domain)

        return JSONResponse(
            content={
                "language": language,
                "domain": domain,
                "exported_at": i18n_manager.translate("common.now", target_language),
                "total_keys": len(translations) if isinstance(translations, dict) else 0,
                "translations": translations
            },
            headers={
                "Content-Disposition": f"attachment; filename=translations_{language}.json"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export translations: {str(e)}")


@router.get("/detect-language")
async def detect_language(
    request: Request
):
    """
    从请求中检测语言

    Args:
        request: HTTP请求对象

    Returns:
        检测到的语言信息
    """
    try:
        headers = dict(request.headers)
        query_params = dict(request.query_params)

        detected_language = get_current_language(headers, query_params)

        return {
            "detected_language": detected_language.value,
            "default_language": i18n_manager.default_language.value,
            "accept_language": headers.get("Accept-Language", ""),
            "query_language": query_params.get("lang"),
            "supported_languages": [lang.value for lang in i18n_manager.supported_languages]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")