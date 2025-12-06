"""
高级NLP分析器
支持多模型情感分析、情感预测、实体识别、关系抽取等高级功能
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
import json
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from app.core.llm_client import llm_client
from app.core.logger import logger


class EmotionType(str, Enum):
    """情感类型枚举"""
    JOY = "joy"  # 喜悦
    SADNESS = "sadness"  # 悲伤
    ANGER = "anger"  # 愤怒
    FEAR = "fear"  # 恐惧
    SURPRISE = "surprise"  # 惊讶
    DISGUST = "disgust"  # 厌恶
    NEUTRAL = "neutral"  # 中性


class EntityType(str, Enum):
    """实体类型枚举"""
    PERSON = "person"  # 人物
    ORGANIZATION = "organization"  # 组织
    LOCATION = "location"  # 地理位置
    EVENT = "event"  # 事件
    PRODUCT = "product"  # 产品
    DATE = "date"  # 日期
    MONEY = "money"  # 金额
    PERCENT = "percent"  # 百分比
    OTHER = "other"  # 其他


@dataclass
class EmotionScore:
    """情感分数"""
    emotion: EmotionType
    score: float  # 0-1
    confidence: float  # 0-1


@dataclass
class Entity:
    """命名实体"""
    text: str
    type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    metadata: Dict[str, Any] = None


@dataclass
class Relation:
    """实体关系"""
    subject: str
    predicate: str
    object: str
    confidence: float


@dataclass
class SentimentPrediction:
    """情感预测结果"""
    current_sentiment: float  # -100 to 100
    predicted_trend: str  # "improving", "declining", "stable"
    trend_confidence: float  # 0-1
    prediction_horizon: str  # "short_term", "medium_term", "long_term"
    key_factors: List[str]  # 影响因素


class AdvancedNLPAnalyzer:
    """
    高级NLP分析器
    支持多模型情感分析、情感预测、实体识别、关系抽取等
    """

    def __init__(self):
        self.sentiment_keywords = {
            "positive": {
                "zh": ["好", "优秀", "成功", "增长", "提升", "改善", "积极", "乐观", "机遇", "突破"],
                "en": ["good", "excellent", "success", "growth", "improve", "positive", "optimistic", "opportunity", "breakthrough"]
            },
            "negative": {
                "zh": ["坏", "失败", "下降", "危机", "风险", "担忧", "悲观", "困难", "挑战", "问题"],
                "en": ["bad", "fail", "decline", "crisis", "risk", "worry", "pessimistic", "difficulty", "challenge", "problem"]
            }
        }

        # 情感强度调节词
        self.intensity_modifiers = {
            "strong": {"zh": ["非常", "极其", "特别", "十分"], "en": ["very", "extremely", "particularly", "highly"]},
            "weak": {"zh": ["稍微", "略微", "有点", "比较"], "en": ["slightly", "somewhat", "rather", "relatively"]}
        }

        # 实体识别关键词模式
        self.entity_patterns = {
            EntityType.PERSON: [
                r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+',
                r'\b(?:[A-Z][a-z]+\s+[A-Z][a-z]+)\b(?=\s+(?:said|announced|reported|confirmed))',
                r'[\u4e00-\u9fff]{2,4}(?:先生|女士|教授|博士|部长|总裁|总理|主席)'
            ],
            EntityType.ORGANIZATION: [
                r'\b(?:[A-Z][a-z]+\s+(?:Inc|Corp|LLC|Ltd|Co|Group|Company|Organization))\b',
                r'[\u4e00-\u9fff]*(?:公司|集团|企业|机构|组织|部门|委员会)'
            ],
            EntityType.LOCATION: [
                r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b(?=\s+(?:city|state|country|province))',
                r'[\u4e00-\u9fff]*(?:市|省|国家|地区|州|县|区)'
            ]
        }

    async def analyze_sentiment_multi_model(self, title: str, content: str) -> Tuple[float, Dict[str, Any]]:
        """
        多模型情感分析
        结合多种方法进行情感分析，提高准确性

        Returns:
            Tuple[average_sentiment_score, model_details]
        """
        models_results = {}

        # 模型1: 基于关键词的分析
        keyword_sentiment = await self._sentiment_analysis_keywords(title, content)
        models_results["keyword_based"] = {
            "score": keyword_sentiment,
            "confidence": 0.7,
            "method": "keyword_matching"
        }

        # 模型2: LLM情感分析
        llm_sentiment = await self._sentiment_analysis_llm(title, content)
        models_results["llm_based"] = {
            "score": llm_sentiment,
            "confidence": 0.85,
            "method": "llm_analysis"
        }

        # 模型3: 语义规则分析
        rule_sentiment = await self._sentiment_analysis_rules(title, content)
        models_results["rule_based"] = {
            "score": rule_sentiment,
            "confidence": 0.6,
            "method": "semantic_rules"
        }

        # 模型4: 情感细粒度分析
        emotion_scores = await self._analyze_emotions(title, content)
        models_results["emotion_based"] = {
            "score": emotion_scores["overall_sentiment"],
            "confidence": 0.8,
            "method": "emotion_analysis",
            "emotions": emotion_scores["emotions"]
        }

        # 计算加权平均分数
        weighted_scores = []
        total_weight = 0

        for model, result in models_results.items():
            weight = result["confidence"]
            score = result["score"]
            weighted_scores.append(score * weight)
            total_weight += weight

        average_sentiment = sum(weighted_scores) / total_weight if total_weight > 0 else 0

        # 限制范围到 -100 到 100
        average_sentiment = max(-100, min(100, average_sentiment))

        return average_sentiment, models_results

    async def _sentiment_analysis_keywords(self, title: str, content: str) -> float:
        """基于关键词的情感分析"""
        text = (title + " " + content).lower()
        sentiment_score = 0

        # 统计积极和消极词汇
        positive_count = 0
        negative_count = 0

        for lang in ["zh", "en"]:
            for keyword in self.sentiment_keywords["positive"][lang]:
                positive_count += text.count(keyword.lower())
            for keyword in self.sentiment_keywords["negative"][lang]:
                negative_count += text.count(keyword.lower())

        # 计算基础分数
        total_words = positive_count + negative_count
        if total_words > 0:
            net_positive = (positive_count - negative_count) / total_words
            sentiment_score = net_positive * 100

            # 应用强度调节
            for intensity_type, modifiers in self.intensity_modifiers.items():
                for lang in ["zh", "en"]:
                    for modifier in modifiers[lang]:
                        count = text.count(modifier.lower())
                        if count > 0:
                            if intensity_type == "strong":
                                sentiment_score *= 1.2
                            elif intensity_type == "weak":
                                sentiment_score *= 0.8

        return max(-100, min(100, sentiment_score))

    async def _sentiment_analysis_llm(self, title: str, content: str) -> float:
        """基于LLM的情感分析"""
        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        prompt = f"""请对以下新闻进行精确的情感分析，返回-100到100之间的分数：

评分标准：
- -100: 极度负面（重大灾难、战争、危机）
- -50: 负面（困难、挑战、损失）
- 0: 中性（客观报道、数据陈述）
- 50: 正面（改善、机会、成就）
- 100: 极度正面（重大突破、历史性成就）

新闻标题：{title}
新闻内容：{content[:800]}

请只返回一个数字分数，不要任何解释。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻情感分析专家，能够准确评估文本的情感倾向。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.1,  # 降低温度以获得更一致的结果
                max_tokens=10
            )

            if response:
                match = re.search(r'-?\d+\.?\d*', response)
                if match:
                    score = float(match.group())
                    return max(-100, min(100, score))

        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}")

        return 0  # 默认中性

    async def _sentiment_analysis_rules(self, title: str, content: str) -> float:
        """基于语义规则的情感分析"""
        text = (title + " " + content).lower()
        sentiment_score = 0

        # 规则1: 问号和感叹号的影响
        question_marks = text.count('?') + text.count('？')
        exclamation_marks = text.count('!') + text.count('！')

        # 过多的问号通常表示不确定性或担忧
        if question_marks > 2:
            sentiment_score -= 10

        # 感叹号可能表示强烈的情感（正面或负面）
        if exclamation_marks > 0:
            sentiment_score += exclamation_marks * 5

        # 规则2: 财经相关词汇的影响
        financial_positive = ["上涨", "增长", "盈利", "收益", "bullish", "rally", "surge", "gain"]
        financial_negative = ["下跌", "亏损", "损失", "debt", "crash", "plummet", "decline", "loss"]

        for word in financial_positive:
            sentiment_score += text.count(word) * 10
        for word in financial_negative:
            sentiment_score -= text.count(word) * 10

        # 规则3: 否定词的影响
        negation_words = ["不", "没", "无", "非", "not", "no", "never", "none"]
        negation_count = sum(text.count(word) for word in negation_words)

        if negation_count > 0:
            sentiment_score *= 0.8  # 稍微降低情感强度

        return max(-100, min(100, sentiment_score))

    async def _analyze_emotions(self, title: str, content: str) -> Dict[str, Any]:
        """分析细粒度情感"""
        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        prompt = f"""请分析以下新闻中的情感成分，为每种情感类型提供0-1的分数：

情感类型：
- joy (喜悦): 快乐、满足、兴奋
- sadness (悲伤): 失望、伤心、痛苦
- anger (愤怒): 生气、不满、愤慨
- fear (恐惧): 担心、害怕、焦虑
- surprise (惊讶): 震惊、意外、惊奇
- disgust (厌恶): 反感、厌恶、鄙视
- neutral (中性): 客观、平静、无情感色彩

新闻标题：{title}
新闻内容：{content[:600]}

请以JSON格式返回：
{{"joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0, "surprise": 0.0, "disgust": 0.0, "neutral": 0.0}}"""

        messages = [
            {"role": "system", "content": "你是一个专业的情感分析专家，能够准确识别文本中的各种情感成分。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.2,
                max_tokens=200
            )

            if response:
                match = re.search(r'\{.*?\}', response, re.DOTALL)
                if match:
                    emotions_data = json.loads(match.group())

                    # 计算综合情感分数
                    positive_emotions = emotions_data.get("joy", 0) + emotions_data.get("surprise", 0) * 0.5
                    negative_emotions = (
                        emotions_data.get("sadness", 0) + emotions_data.get("anger", 0) +
                        emotions_data.get("fear", 0) + emotions_data.get("disgust", 0)
                    )

                    net_sentiment = (positive_emotions - negative_emotions) * 100

                    return {
                        "emotions": emotions_data,
                        "overall_sentiment": net_sentiment
                    }

        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")

        return {
            "emotions": {e.value: 0.0 for e in EmotionType},
            "overall_sentiment": 0
        }

    async def extract_entities_advanced(self, title: str, content: str) -> List[Entity]:
        """
        高级实体识别
        结合规则和LLM进行实体识别
        """
        text = title + " " + content
        entities = []

        # 规则基础的实体识别
        entities.extend(self._extract_entities_rules(text))

        # LLM增强的实体识别
        llm_entities = await self._extract_entities_llm(text)
        entities.extend(llm_entities)

        # 去重和合并
        unique_entities = self._merge_entities(entities)

        return unique_entities

    def _extract_entities_rules(self, text: str) -> List[Entity]:
        """基于规则的实体识别"""
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity = Entity(
                        text=match.group(),
                        type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.7,
                        metadata={"extraction_method": "rule_based"}
                    )
                    entities.append(entity)

        return entities

    async def _extract_entities_llm(self, text: str) -> List[Entity]:
        """基于LLM的实体识别"""
        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        prompt = f"""请从以下文本中提取命名实体，包括人物、组织、地点、事件等。

文本内容：{text[:800]}

请以JSON格式返回，格式如下：
[
  {{"text": "实体名称", "type": "person|organization|location|event|product|date|money|percent|other", "confidence": 0.9}},
  ...
]
只返回JSON数组，不要其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的命名实体识别专家，能够准确识别文本中的各种实体类型。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.1,
                max_tokens=500
            )

            if response:
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    entities_data = json.loads(match.group())
                    entities = []

                    for entity_data in entities_data:
                        entity = Entity(
                            text=entity_data.get("text", ""),
                            type=EntityType(entity_data.get("type", "other")),
                            start_pos=text.find(entity_data.get("text", "")),
                            end_pos=text.find(entity_data.get("text", "")) + len(entity_data.get("text", "")),
                            confidence=entity_data.get("confidence", 0.8),
                            metadata={"extraction_method": "llm_based"}
                        )
                        entities.append(entity)

                    return entities

        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")

        return []

    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并和去重实体"""
        unique_entities = []
        seen_texts = set()

        for entity in entities:
            key = (entity.text.lower(), entity.type)
            if key not in seen_texts:
                unique_entities.append(entity)
                seen_texts.add(key)

        return unique_entities

    async def extract_relations(self, title: str, content: str, entities: List[Entity]) -> List[Relation]:
        """
        实体关系抽取
        识别实体之间的关系
        """
        if len(entities) < 2:
            return []

        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        # 准备实体信息
        entity_texts = [e.text for e in entities[:10]]  # 限制实体数量

        prompt = f"""请分析以下新闻中实体之间的关系。

新闻标题：{title}
新闻内容：{content[:600]}
相关实体：{', '.join(entity_texts)}

请识别实体之间的关系，例如：
- 人物与组织的关系（雇佣、领导、成员）
- 组织与地点的关系（总部、分部）
- 事件与人物的关系（参与、影响）
- 产品与组织的关系（生产、发布）

请以JSON格式返回：
[
  {{"subject": "主体实体", "predicate": "关系", "object": "客体实体", "confidence": 0.8}},
  ...
]
只返回JSON数组，不要其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的实体关系抽取专家，能够准确识别实体之间的语义关系。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.2,
                max_tokens=400
            )

            if response:
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    relations_data = json.loads(match.group())
                    relations = []

                    for rel_data in relations_data:
                        relation = Relation(
                            subject=rel_data.get("subject", ""),
                            predicate=rel_data.get("predicate", ""),
                            object=rel_data.get("object", ""),
                            confidence=rel_data.get("confidence", 0.7)
                        )
                        relations.append(relation)

                    return relations

        except Exception as e:
            logger.error(f"Relation extraction failed: {e}")

        return []

    async def predict_sentiment_trend(self, title: str, content: str,
                                    historical_sentiments: List[float] = None) -> SentimentPrediction:
        """
        情感趋势预测
        基于当前内容预测情感趋势
        """
        current_sentiment, model_details = await self.analyze_sentiment_multi_model(title, content)

        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        # 准备历史情感数据
        context_data = ""
        if historical_sentiments and len(historical_sentiments) > 0:
            avg_sentiment = sum(historical_sentiments) / len(historical_sentiments)
            trend_desc = "上升" if avg_sentiment > current_sentiment else "下降" if avg_sentiment < current_sentiment else "稳定"
            context_data = f"近期相关新闻平均情感分数：{avg_sentiment:.1f}，趋势：{trend_desc}\n"

        prompt = f"""请基于以下新闻信息预测情感趋势：

{context_data}
当前新闻标题：{title}
当前新闻内容：{content[:600]}
当前情感分数：{current_sentiment:.1f}

请分析并预测：
1. 短期趋势（未来1-3天）
2. 中期趋势（未来1-2周）
3. 影响情感的关键因素

请以JSON格式返回：
{{
  "trend_direction": "improving|declining|stable",
  "confidence": 0.8,
  "prediction_horizon": "short_term|medium_term|long_term",
  "key_factors": ["因素1", "因素2", "因素3"],
  "analysis": "简要分析说明"
}}"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻情感趋势预测专家，能够准确预测新闻情感的发展趋势。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.3,
                max_tokens=300
            )

            if response:
                match = re.search(r'\{.*?\}', response, re.DOTALL)
                if match:
                    prediction_data = json.loads(match.group())

                    return SentimentPrediction(
                        current_sentiment=current_sentiment,
                        predicted_trend=prediction_data.get("trend_direction", "stable"),
                        trend_confidence=prediction_data.get("confidence", 0.5),
                        prediction_horizon=prediction_data.get("prediction_horizon", "short_term"),
                        key_factors=prediction_data.get("key_factors", [])
                    )

        except Exception as e:
            logger.error(f"Sentiment trend prediction failed: {e}")

        # 默认预测
        return SentimentPrediction(
            current_sentiment=current_sentiment,
            predicted_trend="stable",
            trend_confidence=0.5,
            prediction_horizon="short_term",
            key_factors=["信息不足"]
        )

    async def analyze_comprehensive(self, title: str, content: str,
                                  historical_sentiments: List[float] = None) -> Dict[str, Any]:
        """
        综合分析
        执行所有高级NLP分析功能
        """
        logger.info(f"Starting comprehensive NLP analysis: {title[:50]}...")

        # 并行执行各项分析
        tasks = [
            self.analyze_sentiment_multi_model(title, content),
            self.extract_entities_advanced(title, content),
            self.extract_keywords_advanced(title, content),
            self.categorize_news_advanced(title, content)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 解析结果
        sentiment_score, sentiment_details = results[0] if not isinstance(results[0], Exception) else (0, {})
        entities = results[1] if not isinstance(results[1], Exception) else []
        keywords = results[2] if not isinstance(results[2], Exception) else []
        category = results[3] if not isinstance(results[3], Exception) else "其他"

        # 后续分析（依赖前面的结果）
        relations = await self.extract_relations(title, content, entities)
        sentiment_prediction = await self.predict_sentiment_trend(title, content, historical_sentiments)

        # 构建综合分析结果
        comprehensive_result = {
            "sentiment": {
                "score": sentiment_score,
                "details": sentiment_details,
                "prediction": {
                    "trend": sentiment_prediction.predicted_trend,
                    "confidence": sentiment_prediction.trend_confidence,
                    "horizon": sentiment_prediction.prediction_horizon,
                    "factors": sentiment_prediction.key_factors
                }
            },
            "entities": [
                {
                    "text": entity.text,
                    "type": entity.type.value,
                    "confidence": entity.confidence,
                    "metadata": entity.metadata
                }
                for entity in entities
            ],
            "relations": [
                {
                    "subject": relation.subject,
                    "predicate": relation.predicate,
                    "object": relation.object,
                    "confidence": relation.confidence
                }
                for relation in relations
            ],
            "keywords": keywords,
            "category": category,
            "analysis_metadata": {
                "analysis_time": datetime.now(timezone.utc).isoformat(),
                "text_length": len(title) + len(content),
                "models_used": list(sentiment_details.keys()) if sentiment_details else [],
                "entity_count": len(entities),
                "relation_count": len(relations),
                "keyword_count": len(keywords)
            }
        }

        logger.info(f"Comprehensive analysis completed with {len(entities)} entities, {len(relations)} relations")
        return comprehensive_result

    async def extract_keywords_advanced(self, title: str, content: str) -> List[str]:
        """高级关键词提取"""
        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        prompt = f"""请从以下新闻中提取5-8个最重要的关键词。

要求：
1. 包含核心主题和概念
2. 涵盖主要实体和事件
3. 体现新闻的价值和影响
4. 按重要性排序

新闻标题：{title}
新闻内容：{content[:800]}

请以JSON数组格式返回：["关键词1", "关键词2", ...]
只返回JSON数组，不要其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻关键词提取专家，能够准确识别文本中的核心概念和重要信息。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.2,
                max_tokens=150
            )

            if response:
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    keywords = json.loads(match.group())
                    if isinstance(keywords, list) and len(keywords) > 0:
                        return keywords[:8]

        except Exception as e:
            logger.error(f"Advanced keyword extraction failed: {e}")

        return []

    async def categorize_news_advanced(self, title: str, content: str) -> str:
        """高级新闻分类"""
        providers = llm_client.get_available_providers()
        provider = providers[0] if providers else "default"

        categories = [
            "政治", "经济", "军事", "科技", "社会", "文化",
            "体育", "健康", "环境", "灾难", "国际关系", "教育",
            "娱乐", "法律", "交通", "能源", "农业", "其他"
        ]

        prompt = f"""请将以下新闻准确分类到最合适的类别中。

可选类别：{', '.join(categories)}

分类标准：
- 政治：政府政策、选举、外交事务
- 经济：市场、金融、贸易、产业
- 军事：国防、军队、武器、冲突
- 科技：创新、研究、互联网、人工智能
- 社会：民生、社会问题、公共服务
- 文化：艺术、传统文化、现代文化
- 体育：竞技体育、运动员、赛事
- 健康：医疗、疾病、健康生活
- 环境：气候、污染、生态保护
- 灾难：自然灾害、事故灾害
- 国际关系：国际合作、国际冲突
- 教育：学校、教育政策、学术研究
- 娱乐：影视、音乐、游戏
- 法律：立法、司法、法律案件
- 交通：交通基础设施、交通安全
- 能源：传统能源、新能源
- 农业：农业生产、农村发展
- 其他：无法归入以上类别

新闻标题：{title}
新闻内容：{content[:600]}

请只返回一个最合适的类别名称，不要其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻分类专家，能够准确判断新闻的主题类别。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.1,
                max_tokens=20
            )

            if response:
                response_clean = response.strip()
                for cat in categories:
                    if cat in response_clean:
                        return cat

        except Exception as e:
            logger.error(f"Advanced news categorization failed: {e}")

        return "其他"


# 全局实例
advanced_nlp_analyzer = AdvancedNLPAnalyzer()