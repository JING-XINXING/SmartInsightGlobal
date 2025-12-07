from typing import Dict, Optional, List
import json
import re
from app.core.llm_client import llm_client
from app.core.logger import logger

import random
import asyncio

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
    
    async def extract_location(self, title: str, content: str) -> Optional[Dict]:
        """
        从新闻中提取地理位置信息
        
        Returns:
            Dict with location info: {"country": "...", "city": "...", "lat": ..., "lng": ...}
            如果无法提取位置，返回 None
        """
        prompt = f"""分析以下新闻，提取其中提到的主要地理位置信息。

新闻标题：{title}
新闻内容：{content[:500]}

请以JSON格式返回，包含以下字段：
- country: 国家名称（英文）
- country_cn: 国家名称（中文）
- city: 城市名称（英文，如无明确城市可为空字符串）
- lat: 纬度（数字）
- lng: 经度（数字）

如果新闻中没有明确的地理位置，返回：{{"country": "", "country_cn": "", "city": "", "lat": 0, "lng": 0}}

只返回JSON对象，不要有其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个专业的地理位置提取助手，熟悉全球主要国家和城市的地理坐标。"},
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
                max_tokens=150
            )
            
            if response:
                # Try to parse JSON
                match = re.search(r'\{.*?\}', response, re.DOTALL)
                if match:
                    location = json.loads(match.group())
                    if isinstance(location, dict) and location.get("country"):
                        logger.info(f"Extracted location: {location.get('country')}, {location.get('city')}")
                        return location
                        
        except Exception as e:
            logger.error(f"Error in location extraction: {e}", exc_info=True)
        
        return None

    async def analyze_news_full(self, title: str, content: str, extract_location: bool = False) -> Dict:
        """
        Perform full analysis: sentiment + keywords + category + location.
        
        Args:
            title: 新闻标题
            content: 新闻内容
            extract_location: 是否提取地理位置（可选，默认否）
        
        Returns:
            Dict with analysis results
        """
        logger.info(f"Starting full analysis for: {title[:50]}...")
        
        results = {
            "sentiment_score": None,
            "keywords": None,
            "category": None,
            "location": None
        }
        
        # Run analyses in parallel for efficiency
        tasks = [
            self.analyze_sentiment(title, content),
            self.extract_keywords(title, content),
            self.categorize_news(title, content)
        ]
        
        if extract_location:
            tasks.append(self.extract_location(title, content))
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Unpack results
        if not isinstance(results_list[0], Exception):
            results["sentiment_score"] = results_list[0]
        if not isinstance(results_list[1], Exception):
            results["keywords"] = results_list[1]
        if not isinstance(results_list[2], Exception):
            results["category"] = results_list[2]
        if extract_location and len(results_list) > 3 and not isinstance(results_list[3], Exception):
            results["location"] = results_list[3]
        
        logger.info(f"Full analysis completed: {results}")
        return results

    async def batch_analyze(self, news_list: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Batch analyze news list.
        Args:
            news_list: List of dicts with 'title' and 'content' keys
            batch_size: Number of concurrent tasks
        Returns:
            List of analysis result dicts
        """
        results = []
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i : i + batch_size]
            tasks = [
                self.analyze_news_full(
                    item.get('title', ''), 
                    item.get('content', ''),
                    extract_location=item.get('extract_location', False)
                ) for item in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in batch_results:
                if isinstance(res, Exception):
                    logger.error(f"Batch analysis item failed: {res}")
                    results.append({
                        "sentiment_score": None, 
                        "keywords": None, 
                        "category": "其他", 
                        "location": None
                    })
                else:
                    results.append(res)
            
        return results

# Global instance
news_analyzer = NewsAnalyzer()
