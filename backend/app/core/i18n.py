"""
国际化(i18n)模块
支持中文和英文的多语言功能
"""
import json
import os
from typing import Dict, Optional, Any, List
from enum import Enum
from functools import lru_cache
from pathlib import Path

from app.core.logger import logger


class Language(str, Enum):
    """支持的语言"""
    CHINESE = "zh-CN"
    ENGLISH = "en-US"


class TranslationDomain(str, Enum):
    """翻译域"""
    API_RESPONSES = "api_responses"
    ERROR_MESSAGES = "error_messages"
    UI_LABELS = "ui_labels"
    CATEGORIES = "categories"
    ANALYSIS = "analysis"
    MAP = "map"
    AUTH = "auth"


class I18nManager:
    """
    国际化管理器
    提供多语言翻译和文化本地化功能
    """

    def __init__(self):
        self.supported_languages = list(Language)
        self.default_language = Language.CHINESE
        self.translations = {}
        self.fallback_language = Language.ENGLISH

        # 加载翻译文件
        self._load_translations()

    def _load_translations(self):
        """加载所有翻译文件"""
        try:
            # 获取翻译文件目录
            translations_dir = Path(__file__).parent.parent / "translations"

            for language in self.supported_languages:
                language_dir = translations_dir / language.value
                self.translations[language.value] = {}

                if language_dir.exists():
                    # 加载各个域的翻译文件
                    for domain in TranslationDomain:
                        translation_file = language_dir / f"{domain.value}.json"
                        if translation_file.exists():
                            with open(translation_file, 'r', encoding='utf-8') as f:
                                self.translations[language.value][domain.value] = json.load(f)
                        else:
                            self.translations[language.value][domain.value] = {}
                            logger.warning(f"Translation file not found: {translation_file}")
                else:
                    logger.warning(f"Translation directory not found: {language_dir}")

            logger.info(f"Loaded translations for {len(self.supported_languages)} languages")

        except Exception as e:
            logger.error(f"Failed to load translations: {e}")

    @lru_cache(maxsize=1000)
    def translate(self, key: str, language: Language = None, domain: TranslationDomain = TranslationDomain.API_RESPONSES, **kwargs) -> str:
        """
        获取翻译文本

        Args:
            key: 翻译键
            language: 目标语言
            domain: 翻译域
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        if language is None:
            language = self.default_language

        # 尝试获取翻译
        translation = self._get_translation(key, language, domain)

        # 如果找不到翻译，尝试fallback语言
        if translation is None and language != self.fallback_language:
            translation = self._get_translation(key, self.fallback_language, domain)

        # 如果仍然找不到，返回键本身
        if translation is None:
            logger.warning(f"Translation not found: {language.value}.{domain.value}.{key}")
            return key

        # 格式化翻译
        try:
            if kwargs:
                return translation.format(**kwargs)
            return translation
        except (KeyError, ValueError) as e:
            logger.error(f"Translation formatting error: {e}")
            return translation

    def _get_translation(self, key: str, language: Language, domain: TranslationDomain) -> Optional[str]:
        """获取指定语言和域的翻译"""
        try:
            # 支持嵌套键，如 "error.validation.required"
            key_parts = key.split('.')
            current_dict = self.translations.get(language.value, {}).get(domain.value, {})

            for part in key_parts:
                if isinstance(current_dict, dict) and part in current_dict:
                    current_dict = current_dict[part]
                else:
                    return None

            return current_dict if isinstance(current_dict, str) else None

        except Exception as e:
            logger.error(f"Error getting translation: {e}")
            return None

    def get_translation_keys(self, language: Language, domain: TranslationDomain = None) -> Dict[str, Any]:
        """
        获取指定语言的所有翻译键

        Args:
            language: 语言
            domain: 域（可选）

        Returns:
            翻译字典
        """
        if domain:
            return self.translations.get(language.value, {}).get(domain.value, {})
        else:
            return self.translations.get(language.value, {})

    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        获取可用语言列表

        Returns:
            语言信息列表
        """
        return [
            {
                "code": lang.value,
                "name": self.translate(f"language.{lang.value}", lang),
                "native_name": self.translate(f"language.native.{lang.value}", lang),
                "flag": self._get_language_flag(lang)
            }
            for lang in self.supported_languages
        ]

    def _get_language_flag(self, language: Language) -> str:
        """获取语言标志"""
        flags = {
            Language.CHINESE: "🇨🇳",
            Language.ENGLISH: "🇺🇸"
        }
        return flags.get(language, "🌐")

    def format_currency(self, amount: float, language: Language = None) -> str:
        """
        格式化货币

        Args:
            amount: 金额
            language: 语言

        Returns:
            格式化的货币字符串
        """
        if language is None:
            language = self.default_language

        if language == Language.CHINESE:
            return f"¥{amount:,.2f}"
        else:  # ENGLISH
            return f"${amount:,.2f}"

    def format_date(self, date_obj, language: Language = None, format_type: str = "medium") -> str:
        """
        格式化日期

        Args:
            date_obj: 日期对象
            language: 语言
            format_type: 格式类型 ("short", "medium", "long")

        Returns:
            格式化的日期字符串
        """
        if language is None:
            language = self.default_language

        if language == Language.CHINESE:
            formats = {
                "short": "%Y-%m-%d",
                "medium": "%Y年%m月%d日",
                "long": "%Y年%m月%d日 %H:%M:%S"
            }
        else:  # ENGLISH
            formats = {
                "short": "%Y-%m-%d",
                "medium": "%B %d, %Y",
                "long": "%B %d, %Y %I:%M:%S %p"
            }

        date_format = formats.get(format_type, formats["medium"])
        return date_obj.strftime(date_format)

    def format_number(self, number: float, language: Language = None) -> str:
        """
        格式化数字

        Args:
            number: 数字
            language: 语言

        Returns:
            格式化的数字字符串
        """
        if language is None:
            language = self.default_language

        if language == Language.CHINESE:
            if number >= 100000000:  # 1亿
                return f"{number/100000000:.1f}亿"
            elif number >= 10000:  # 1万
                return f"{number/10000:.1f}万"
            else:
                return f"{number:,}"
        else:  # ENGLISH
            if number >= 1000000:  # 1 million
                return f"{number/1000000:.1f}M"
            elif number >= 1000:  # 1 thousand
                return f"{number/1000:.1f}K"
            else:
                return f"{number:,}"

    def detect_language_from_request(self, headers: Dict[str, str], query_params: Dict[str, str] = None) -> Language:
        """
        从HTTP请求中检测语言

        Args:
            headers: HTTP头部
            query_params: 查询参数

        Returns:
            检测到的语言
        """
        # 1. 检查查询参数中的lang参数
        if query_params and "lang" in query_params:
            lang_code = query_params["lang"]
            for lang in self.supported_languages:
                if lang.value.lower().startswith(lang_code.lower()):
                    return lang

        # 2. 检查Accept-Language头
        accept_language = headers.get("Accept-Language", "")
        if accept_language:
            # 解析Accept-Language头
            languages = [lang.split(";")[0].strip() for lang in accept_language.split(",")]
            for lang_code in languages:
                for lang in self.supported_languages:
                    if lang.value.lower().startswith(lang_code.lower()):
                        return lang

        # 3. 返回默认语言
        return self.default_language

    def get_localized_categories(self, language: Language = None) -> Dict[str, str]:
        """
        获取本地化的新闻类别

        Args:
            language: 语言

        Returns:
            本地化的类别字典
        """
        if language is None:
            language = self.default_language

        categories = {
            "政治": "politics",
            "经济": "economy",
            "军事": "military",
            "科技": "technology",
            "社会": "society",
            "文化": "culture",
            "体育": "sports",
            "健康": "health",
            "环境": "environment",
            "灾难": "disaster",
            "国际关系": "international",
            "其他": "other"
        }

        localized_categories = {}
        for chinese_name, english_key in categories.items():
            if language == Language.CHINESE:
                localized_categories[english_key] = chinese_name
            else:
                localized_categories[english_key] = self.translate(f"category.{english_key}", language)

        return localized_categories

    def get_localized_sentiment_labels(self, language: Language = None) -> Dict[str, str]:
        """
        获取本地化的情感标签

        Args:
            language: 语言

        Returns:
            本地化的情感标签字典
        """
        if language is None:
            language = self.default_language

        return {
            "very_positive": self.translate("sentiment.very_positive", language),
            "positive": self.translate("sentiment.positive", language),
            "neutral": self.translate("sentiment.neutral", language),
            "negative": self.translate("sentiment.negative", language),
            "very_negative": self.translate("sentiment.very_negative", language)
        }

    def create_translated_response(self, data: Dict[str, Any], language: Language = None,
                                 translate_keys: List[str] = None) -> Dict[str, Any]:
        """
        创建翻译的响应数据

        Args:
            data: 原始数据
            language: 目标语言
            translate_keys: 需要翻译的键列表

        Returns:
            翻译后的数据
        """
        if language is None:
            language = self.default_language

        if not translate_keys:
            return data

        translated_data = data.copy()

        for key in translate_keys:
            if key in translated_data and isinstance(translated_data[key], str):
                # 尝试翻译
                translated_value = self.translate(f"response.{key}", language, default=translated_data[key])
                translated_data[f"{key}_translated"] = translated_value

        return translated_data

    def validate_language(self, language_code: str) -> Language:
        """
        验证语言代码

        Args:
            language_code: 语言代码

        Returns:
            有效的语言对象

        Raises:
            ValueError: 无效的语言代码
        """
        for lang in self.supported_languages:
            if lang.value == language_code or lang.value.startswith(language_code):
                return lang

        raise ValueError(f"Unsupported language: {language_code}")

    def add_translation(self, key: str, value: str, language: Language,
                       domain: TranslationDomain = TranslationDomain.API_RESPONSES):
        """
        添加翻译（运行时）

        Args:
            key: 翻译键
            value: 翻译值
            language: 语言
            domain: 域
        """
        if language.value not in self.translations:
            self.translations[language.value] = {}

        if domain.value not in self.translations[language.value]:
            self.translations[language.value][domain.value] = {}

        # 支持嵌套键
        key_parts = key.split('.')
        current_dict = self.translations[language.value][domain.value]

        for part in key_parts[:-1]:
            if part not in current_dict:
                current_dict[part] = {}
            current_dict = current_dict[part]

        current_dict[key_parts[-1]] = value

        # 清除缓存
        self.translate.cache_clear()

    def export_translations(self, language: Language, domain: TranslationDomain = None) -> Dict[str, Any]:
        """
        导出翻译数据

        Args:
            language: 语言
            domain: 域（可选）

        Returns:
            翻译数据
        """
        if domain:
            return self.translations.get(language.value, {}).get(domain.value, {})
        else:
            return self.translations.get(language.value, {})


# 全局实例
i18n_manager = I18nManager()


# 便捷函数
def t(key: str, language: Language = None, domain: TranslationDomain = TranslationDomain.API_RESPONSES, **kwargs) -> str:
    """
    翻译函数的便捷别名

    Args:
        key: 翻译键
        language: 语言
        domain: 域
        **kwargs: 格式化参数

    Returns:
        翻译后的文本
    """
    return i18n_manager.translate(key, language, domain, **kwargs)


def get_current_language(headers: Dict[str, str] = None, query_params: Dict[str, str] = None) -> Language:
    """
    获取当前请求的语言

    Args:
        headers: HTTP头部
        query_params: 查询参数

    Returns:
        当前语言
    """
    return i18n_manager.detect_language_from_request(headers or {}, query_params or {})


# FastAPI依赖函数
async def get_language_from_request(
    headers: Dict[str, str] = None,
    query_params: Dict[str, str] = None
) -> Language:
    """
    从FastAPI请求中获取语言
    """
    return get_current_language(headers, query_params)