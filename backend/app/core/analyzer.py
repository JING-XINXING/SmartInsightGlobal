from typing import Dict, Optional, List
import json
import re
from app.core.llm_client import llm_client
from app.core.logger import logger

import random

class NewsAnalyzer:
    """
    Analyze news articles using LLM for sentiment analysis and keyword extraction.
    """
    
    async def analyze_sentiment(self, title: str, content: str) -> Optional[int]:
        """
        Analyze sentiment of news article.
        
        Returns:
            Sentiment score from -100 (very negative) to 100 (very positive)
            0 is neutral
        """
        # Select a random provider
        providers = llm_client.get_available_providers()
        provider = random.choice(providers)
        
        prompt = f"""分析以下新闻的情感倾向，并给出一个-100到100之间的分数：
- -100表示极度负面（如灾难、战争、死亡）
- 0表示中性
- 100表示极度正面（如和平、成功、喜悦）

新闻标题：{title}
新闻内容：{content[:500]}

请只返回一个整数分数，不要有其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻情感分析助手。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.3,
                max_tokens=10
            )
            
            if response:
                # Extract number from response
                match = re.search(r'-?\d+', response)
                if match:
                    score = int(match.group())
                    # Clamp to range
                    score = max(-100, min(100, score))
                    logger.info(f"Sentiment analysis completed: {score}")
                    return score
                    
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}", exc_info=True)
        
        return None
    
    async def extract_keywords(self, title: str, content: str) -> Optional[List[str]]:
        """
        Extract key topics/keywords from news article.
        
        Returns:
            List of keywords (3-5 keywords)
        """
        prompt = f"""从以下新闻中提取3-5个关键词或主题标签。

新闻标题：{title}
新闻内容：{content[:500]}

请以JSON数组格式返回，例如：["关键词1", "关键词2", "关键词3"]
只返回JSON数组，不要有其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻关键词提取助手。"},
            {"role": "user", "content": prompt}
        ]
        
        # Select a random provider
        providers = llm_client.get_available_providers()
        provider = random.choice(providers)
        
        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.3,
                max_tokens=100
            )
            
            if response:
                # Try to parse JSON
                # Find JSON array in response
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    keywords = json.loads(match.group())
                    if isinstance(keywords, list):
                        logger.info(f"Extracted {len(keywords)} keywords")
                        return keywords[:5]  # Limit to 5
                        
        except Exception as e:
            logger.error(f"Error in keyword extraction: {e}", exc_info=True)
        
        return None
    
    async def categorize_news(self, title: str, content: str) -> Optional[str]:
        """
        Categorize news into predefined categories.
        
        Returns:
            Category name
        """
        categories = [
            "政治", "经济", "军事", "科技", "社会", "文化", 
            "体育", "健康", "环境", "灾难", "国际关系", "其他"
        ]
        
        prompt = f"""将以下新闻分类到最合适的类别中。

可选类别：{', '.join(categories)}

新闻标题：{title}
新闻内容：{content[:300]}

请只返回一个类别名称，不要有其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻分类助手。"},
            {"role": "user", "content": prompt}
        ]
        
        # Select a random provider
        providers = llm_client.get_available_providers()
        provider = random.choice(providers)
        
        try:
            response = await llm_client.chat_completion(
                messages=messages,
                provider=provider,
                temperature=0.2,
                max_tokens=10
            )
            
            if response:
                # Find matching category
                for cat in categories:
                    if cat in response:
                        logger.info(f"News categorized as: {cat}")
                        return cat
                        
        except Exception as e:
            logger.error(f"Error in categorization: {e}", exc_info=True)
        
        return "其他"
    
    async def analyze_news_full(self, title: str, content: str) -> Dict:
        """
        Perform full analysis: sentiment + keywords + category.
        
        Returns:
            Dict with analysis results
        """
        logger.info(f"Starting full analysis for: {title[:50]}...")
        
        results = {
            "sentiment_score": None,
            "keywords": None,
            "category": None
        }
        
        # Run analyses in parallel for efficiency
        import asyncio
        sentiment_task = self.analyze_sentiment(title, content)
        keywords_task = self.extract_keywords(title, content)
        category_task = self.categorize_news(title, content)
        
        sentiment, keywords, category = await asyncio.gather(
            sentiment_task,
            keywords_task,
            category_task,
            return_exceptions=True
        )
        
        if not isinstance(sentiment, Exception):
            results["sentiment_score"] = sentiment
        if not isinstance(keywords, Exception):
            results["keywords"] = keywords
        if not isinstance(category, Exception):
            results["category"] = category
        
        logger.info(f"Full analysis completed: {results}")
        return results

# Global instance
news_analyzer = NewsAnalyzer()
