from typing import Dict, Optional, List
import json
import re
from app.core.llm_client import llm_client
from app.core.logger import logger

import random
import asyncio

# 常见国家坐标映射（用于LLM提取失败时的回退）
COUNTRY_COORDINATES = {
    # 亚洲
    "China": {"lat": 35.0, "lng": 105.0, "country_cn": "中国"},
    "Japan": {"lat": 36.2, "lng": 138.3, "country_cn": "日本"},
    "South Korea": {"lat": 36.5, "lng": 127.8, "country_cn": "韩国"},
    "India": {"lat": 20.6, "lng": 79.0, "country_cn": "印度"},
    "Indonesia": {"lat": -2.5, "lng": 118.0, "country_cn": "印度尼西亚"},
    "Thailand": {"lat": 15.0, "lng": 101.0, "country_cn": "泰国"},
    "Vietnam": {"lat": 16.0, "lng": 108.0, "country_cn": "越南"},
    "Philippines": {"lat": 12.0, "lng": 122.0, "country_cn": "菲律宾"},
    "Singapore": {"lat": 1.3, "lng": 103.8, "country_cn": "新加坡"},
    "Malaysia": {"lat": 4.0, "lng": 109.5, "country_cn": "马来西亚"},
    "Pakistan": {"lat": 30.0, "lng": 70.0, "country_cn": "巴基斯坦"},
    "Bangladesh": {"lat": 24.0, "lng": 90.0, "country_cn": "孟加拉国"},
    "Iran": {"lat": 32.0, "lng": 53.0, "country_cn": "伊朗"},
    "Iraq": {"lat": 33.0, "lng": 44.0, "country_cn": "伊拉克"},
    "Saudi Arabia": {"lat": 24.0, "lng": 45.0, "country_cn": "沙特阿拉伯"},
    "Israel": {"lat": 31.0, "lng": 35.0, "country_cn": "以色列"},
    "Turkey": {"lat": 39.0, "lng": 35.0, "country_cn": "土耳其"},
    "UAE": {"lat": 24.0, "lng": 54.0, "country_cn": "阿联酋"},
    "United Arab Emirates": {"lat": 24.0, "lng": 54.0, "country_cn": "阿联酋"},
    "Taiwan": {"lat": 23.7, "lng": 121.0, "country_cn": "台湾"},
    "Hong Kong": {"lat": 22.3, "lng": 114.2, "country_cn": "香港"},
    # 欧洲
    "United Kingdom": {"lat": 54.0, "lng": -2.0, "country_cn": "英国"},
    "UK": {"lat": 54.0, "lng": -2.0, "country_cn": "英国"},
    "Germany": {"lat": 51.0, "lng": 9.0, "country_cn": "德国"},
    "France": {"lat": 46.0, "lng": 2.0, "country_cn": "法国"},
    "Italy": {"lat": 42.0, "lng": 12.5, "country_cn": "意大利"},
    "Spain": {"lat": 40.0, "lng": -4.0, "country_cn": "西班牙"},
    "Russia": {"lat": 60.0, "lng": 100.0, "country_cn": "俄罗斯"},
    "Ukraine": {"lat": 49.0, "lng": 32.0, "country_cn": "乌克兰"},
    "Poland": {"lat": 52.0, "lng": 19.0, "country_cn": "波兰"},
    "Netherlands": {"lat": 52.0, "lng": 5.5, "country_cn": "荷兰"},
    "Belgium": {"lat": 50.5, "lng": 4.0, "country_cn": "比利时"},
    "Switzerland": {"lat": 47.0, "lng": 8.0, "country_cn": "瑞士"},
    "Sweden": {"lat": 62.0, "lng": 15.0, "country_cn": "瑞典"},
    "Norway": {"lat": 62.0, "lng": 10.0, "country_cn": "挪威"},
    "Denmark": {"lat": 56.0, "lng": 10.0, "country_cn": "丹麦"},
    "Finland": {"lat": 64.0, "lng": 26.0, "country_cn": "芬兰"},
    "Austria": {"lat": 47.5, "lng": 14.5, "country_cn": "奥地利"},
    "Greece": {"lat": 39.0, "lng": 22.0, "country_cn": "希腊"},
    "Portugal": {"lat": 39.5, "lng": -8.0, "country_cn": "葡萄牙"},
    "Ireland": {"lat": 53.0, "lng": -8.0, "country_cn": "爱尔兰"},
    "Czech Republic": {"lat": 50.0, "lng": 15.5, "country_cn": "捷克"},
    "Hungary": {"lat": 47.0, "lng": 20.0, "country_cn": "匈牙利"},
    "Romania": {"lat": 46.0, "lng": 25.0, "country_cn": "罗马尼亚"},
    # 北美洲
    "United States": {"lat": 38.0, "lng": -97.0, "country_cn": "美国"},
    "USA": {"lat": 38.0, "lng": -97.0, "country_cn": "美国"},
    "US": {"lat": 38.0, "lng": -97.0, "country_cn": "美国"},
    "Canada": {"lat": 60.0, "lng": -95.0, "country_cn": "加拿大"},
    "Mexico": {"lat": 23.0, "lng": -102.0, "country_cn": "墨西哥"},
    # 南美洲
    "Brazil": {"lat": -10.0, "lng": -55.0, "country_cn": "巴西"},
    "Argentina": {"lat": -34.0, "lng": -64.0, "country_cn": "阿根廷"},
    "Chile": {"lat": -30.0, "lng": -71.0, "country_cn": "智利"},
    "Colombia": {"lat": 4.0, "lng": -72.0, "country_cn": "哥伦比亚"},
    "Peru": {"lat": -10.0, "lng": -76.0, "country_cn": "秘鲁"},
    "Venezuela": {"lat": 8.0, "lng": -66.0, "country_cn": "委内瑞拉"},
    # 非洲
    "Egypt": {"lat": 27.0, "lng": 30.0, "country_cn": "埃及"},
    "South Africa": {"lat": -29.0, "lng": 24.0, "country_cn": "南非"},
    "Nigeria": {"lat": 10.0, "lng": 8.0, "country_cn": "尼日利亚"},
    "Kenya": {"lat": 1.0, "lng": 38.0, "country_cn": "肯尼亚"},
    "Morocco": {"lat": 32.0, "lng": -5.0, "country_cn": "摩洛哥"},
    "Ethiopia": {"lat": 9.0, "lng": 40.0, "country_cn": "埃塞俄比亚"},
    # 大洋洲
    "Australia": {"lat": -25.0, "lng": 133.0, "country_cn": "澳大利亚"},
    "New Zealand": {"lat": -42.0, "lng": 174.0, "country_cn": "新西兰"},
}

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
        
        使用LLM提取，并使用预定义坐标库作为回退验证
        
        Returns:
            Dict with location info: {"country": "...", "country_cn": "...", "city": "...", "lat": ..., "lng": ...}
            如果无法提取位置，返回 None
        """
        prompt = f"""分析以下新闻，提取其中提到的主要地理位置信息。

新闻标题：{title}
新闻内容：{content[:500]}

请以JSON格式返回，包含以下字段：
- country: 国家名称（英文，首字母大写）
- country_cn: 国家名称（中文）
- city: 城市名称（英文，如无明确城市可为空字符串）
- lat: 纬度（数字，-90到90之间）
- lng: 经度（数字，-180到180之间）

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
                max_tokens=200
            )
            
            if response:
                location = self._parse_location_response(response)
                if location:
                    logger.info(f"Extracted location: {location.get('country')}, {location.get('city')}")
                    return location
                        
        except Exception as e:
            logger.error(f"Error in location extraction: {e}", exc_info=True)
        
        return None
    
    def _parse_location_response(self, response: str) -> Optional[Dict]:
        """
        解析LLM响应的位置信息
        
        Args:
            response: LLM返回的响应文本
            
        Returns:
            解析后的位置字典，如无效则返回None
        """
        try:
            # 尝试找到JSON对象（处理可能的嵌套花括号）
            # 使用更精确的正则表达式
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if not match:
                # 备用：尝试简单匹配
                match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if not match:
                logger.warning(f"No JSON found in response: {response[:100]}")
                return None
                
            location = json.loads(match.group())
            
            if not isinstance(location, dict):
                return None
            
            country = location.get("country", "").strip()
            
            # 如果没有国家名称，返回None
            if not country:
                return None
            
            # 验证和修正坐标
            lat = location.get("lat", 0)
            lng = location.get("lng", 0)
            country_cn = location.get("country_cn", "")
            city = location.get("city", "")
            
            # 确保lat和lng是数字
            try:
                lat = float(lat) if lat else 0
                lng = float(lng) if lng else 0
            except (ValueError, TypeError):
                lat, lng = 0, 0
            
            # 验证坐标是否在有效范围内
            valid_coords = (-90 <= lat <= 90) and (-180 <= lng <= 180) and (lat != 0 or lng != 0)
            
            # 如果坐标无效，尝试从预定义库中获取
            if not valid_coords:
                fallback = self._get_country_coordinates(country)
                if fallback:
                    lat = fallback["lat"]
                    lng = fallback["lng"]
                    # 如果LLM没有返回中文名，使用预定义的
                    if not country_cn:
                        country_cn = fallback.get("country_cn", "")
                    logger.info(f"Using fallback coordinates for {country}: ({lat}, {lng})")
                else:
                    # 无法获取有效坐标
                    logger.warning(f"Invalid coordinates for {country} and no fallback available")
                    return None
            
            return {
                "country": country,
                "country_cn": country_cn or country,
                "city": city,
                "lat": lat,
                "lng": lng
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}, response: {response[:100]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing location: {e}")
            return None
    
    def _get_country_coordinates(self, country_name: str) -> Optional[Dict]:
        """
        从预定义库中获取国家坐标
        
        Args:
            country_name: 国家名称（英文）
            
        Returns:
            包含lat, lng, country_cn的字典，如未找到返回None
        """
        # 直接匹配
        if country_name in COUNTRY_COORDINATES:
            return COUNTRY_COORDINATES[country_name]
        
        # 不区分大小写匹配
        country_lower = country_name.lower()
        for key, value in COUNTRY_COORDINATES.items():
            if key.lower() == country_lower:
                return value
        
        # 部分匹配（处理如 "United States of America" -> "United States"）
        for key, value in COUNTRY_COORDINATES.items():
            if key.lower() in country_lower or country_lower in key.lower():
                return value
        
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
