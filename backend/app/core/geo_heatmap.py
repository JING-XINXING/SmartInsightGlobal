"""
地理热力图增强系统
提供实时热力图、时间序列分析、高级聚类等功能
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from app.models.news import News
from app.core.logger import logger


class HeatmapIntensity(str, Enum):
    """热力图强度级别"""
    LOW = "low"      # 低强度 (0-33%)
    MEDIUM = "medium" # 中强度 (33-66%)
    HIGH = "high"    # 高强度 (66-100%)


class TimeRange(str, Enum):
    """时间范围"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class GeoPoint:
    """地理坐标点"""
    lat: float
    lng: float
    weight: float = 1.0

    def distance_to(self, other: 'GeoPoint') -> float:
        """计算到另一点的距离（公里）"""
        R = 6371  # 地球半径(公里)
        lat1_rad = math.radians(self.lat)
        lat2_rad = math.radians(other.lat)
        delta_lat = math.radians(other.lat - self.lat)
        delta_lng = math.radians(other.lng - self.lng)

        a = (math.sin(delta_lat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c


@dataclass
class HeatmapCell:
    """热力图单元格"""
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float
    center_lat: float
    center_lng: float
    intensity: float
    news_count: int
    avg_sentiment: float
    categories: Dict[str, int]
    time_range: Tuple[datetime, datetime]


@dataclass
class HotspotRegion:
    """热点区域"""
    center_lat: float
    center_lng: float
    radius: float  # 公里
    intensity: float
    news_count: int
    avg_sentiment: float
    dominant_category: str
    trend: str  # "increasing", "decreasing", "stable"
    time_series: List[Dict[str, Any]]


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    timestamp: datetime
    location_count: int
    avg_intensity: float
    avg_sentiment: float
    top_categories: List[str]


class AdvancedGeoHeatmapAnalyzer:
    """
    高级地理热力图分析器
    提供实时热力图、聚类分析、时间序列等功能
    """

    def __init__(self):
        # 地理网格配置
        self.grid_config = {
            "global": {"lat_step": 5.0, "lng_step": 5.0},      # 全球网格
            "regional": {"lat_step": 1.0, "lng_step": 1.0},    # 区域网格
            "city": {"lat_step": 0.1, "lng_step": 0.1}         # 城市网格
        }

        # 热力图权重配置
        self.weight_config = {
            "recency": {"hours": 24, "weight": 2.0},      # 最近24小时权重2.0
            "sentiment": {"positive_weight": 1.5, "negative_weight": 1.2},  # 情感权重
            "category": {"high_impact": ["军事", "灾难", "政治"], "weight": 1.8}  # 高影响类别权重
        }

    async def generate_realtime_heatmap(
        self,
        db: AsyncSession,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        time_range: TimeRange = TimeRange.DAY,
        grid_type: str = "global",
        sentiment_filter: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        生成实时热力图数据

        Args:
            db: 数据库会话
            bbox: 边界框 (min_lat, min_lng, max_lat, max_lng)
            time_range: 时间范围
            grid_type: 网格类型 ("global", "regional", "city")
            sentiment_filter: 情感分数范围 (min, max)

        Returns:
            热力图数据字典
        """
        start_time = datetime.now(timezone.utc)

        # 计算时间范围
        time_threshold = self._get_time_threshold(time_range)

        # 构建查询
        query = select(News).where(
            and_(
                News.location.isnot(None),
                News.publish_date >= time_threshold
            )
        )

        # 添加地理边界筛选
        if bbox:
            min_lat, min_lng, max_lat, max_lng = bbox
            location_condition = (
                func.json_extract(News.location, '$.lat').between(min_lat, max_lat) &
                func.json_extract(News.location, '$.lng').between(min_lng, max_lng)
            )
            query = query.where(location_condition)

        # 添加情感筛选
        if sentiment_filter:
            min_sent, max_sent = sentiment_filter
            query = query.where(News.sentiment_score.between(min_sent, max_sent))

        # 执行查询
        result = await db.execute(query.order_by(News.publish_date.desc()))
        news_items = result.scalars().all()

        # 生成网格热力图
        grid_cells = await self._generate_grid_heatmap(
            news_items, grid_type, time_threshold
        )

        # 计算热点区域
        hotspots = await self._identify_hotspots(news_items)

        # 生成时间序列数据
        time_series = await self._generate_time_series(db, time_range)

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        heatmap_data = {
            "metadata": {
                "generated_at": start_time.isoformat(),
                "processing_time": processing_time,
                "time_range": time_range.value,
                "grid_type": grid_type,
                "total_news": len(news_items),
                "bbox": bbox
            },
            "grid_cells": [
                {
                    "bounds": [cell.lat_min, cell.lng_min, cell.lat_max, cell.lng_max],
                    "center": [cell.center_lat, cell.center_lng],
                    "intensity": cell.intensity,
                    "news_count": cell.news_count,
                    "avg_sentiment": cell.avg_sentiment,
                    "categories": cell.categories
                }
                for cell in grid_cells
            ],
            "hotspots": [
                {
                    "center": [spot.center_lat, spot.center_lng],
                    "radius": spot.radius,
                    "intensity": spot.intensity,
                    "news_count": spot.news_count,
                    "avg_sentiment": spot.avg_sentiment,
                    "dominant_category": spot.dominant_category,
                    "trend": spot.trend
                }
                for spot in hotspots
            ],
            "time_series": time_series,
            "statistics": self._calculate_heatmap_statistics(news_items, grid_cells)
        }

        logger.info(f"Generated realtime heatmap with {len(grid_cells)} cells, {len(hotspots)} hotspots")
        return heatmap_data

    async def _generate_grid_heatmap(
        self,
        news_items: List[News],
        grid_type: str,
        time_threshold: datetime
    ) -> List[HeatmapCell]:
        """生成网格热力图"""
        grid_config = self.grid_config[grid_type]
        lat_step = grid_config["lat_step"]
        lng_step = grid_config["lng_step"]

        # 创建网格
        grid_cells = {}

        for news in news_items:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")

            if not lat or not lng:
                continue

            # 计算网格坐标
            lat_idx = int((lat + 90) / lat_step)
            lng_idx = int((lng + 180) / lng_step)
            grid_key = (lat_idx, lng_idx)

            # 初始化网格单元
            if grid_key not in grid_cells:
                lat_min = -90 + lat_idx * lat_step
                lat_max = lat_min + lat_step
                lng_min = -180 + lng_idx * lng_step
                lng_max = lng_min + lng_step

                grid_cells[grid_key] = HeatmapCell(
                    lat_min=lat_min,
                    lat_max=lat_max,
                    lng_min=lng_min,
                    lng_max=lng_max,
                    center_lat=(lat_min + lat_max) / 2,
                    center_lng=(lng_min + lng_max) / 2,
                    intensity=0.0,
                    news_count=0,
                    avg_sentiment=0.0,
                    categories={},
                    time_range=(time_threshold, datetime.now(timezone.utc))
                )

            # 更新网格单元数据
            cell = grid_cells[grid_key]
            cell.news_count += 1

            # 计算权重
            weight = self._calculate_news_weight(news)
            cell.intensity += weight

            # 更新情感分数
            if news.sentiment_score is not None:
                if cell.news_count == 1:
                    cell.avg_sentiment = news.sentiment_score
                else:
                    cell.avg_sentiment = (cell.avg_sentiment * (cell.news_count - 1) + news.sentiment_score) / cell.news_count

            # 更新类别统计
            if news.category:
                cell.categories[news.category] = cell.categories.get(news.category, 0) + 1

        # 标准化强度值
        if grid_cells:
            max_intensity = max(cell.intensity for cell in grid_cells.values())
            if max_intensity > 0:
                for cell in grid_cells.values():
                    cell.intensity = cell.intensity / max_intensity

        return list(grid_cells.values())

    async def _identify_hotspots(self, news_items: List[News]) -> List[HotspotRegion]:
        """识别热点区域"""
        if not news_items:
            return []

        # 提取所有地理位置点
        points = []
        for news in news_items:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")

            if lat and lng:
                weight = self._calculate_news_weight(news)
                points.append(GeoPoint(lat, lng, weight))

        if not points:
            return []

        # 使用DBSCAN算法进行聚类
        hotspots = self._dbscan_clustering(points)

        # 分析每个热点的趋势
        for hotspot in hotspots:
            hotspot.trend = await self._analyze_hotspot_trend(hotspot, news_items)

        # 按强度排序
        hotspots.sort(key=lambda x: x.intensity, reverse=True)

        return hotspots[:20]  # 返回前20个热点

    def _dbscan_clustering(self, points: List[GeoPoint], eps: float = 50.0, min_pts: int = 3) -> List[HotspotRegion]:
        """使用DBSCAN算法进行聚类"""
        if not points:
            return []

        visited = set()
        clusters = []

        for i, point in enumerate(points):
            if i in visited:
                continue

            # 获取邻居点
            neighbors = []
            for j, other_point in enumerate(points):
                if point.distance_to(other_point) <= eps:
                    neighbors.append(j)

            if len(neighbors) < min_pts:
                visited.add(i)
                continue

            # 创建新簇
            cluster = [i]
            visited.add(i)

            # 扩展簇
            queue = neighbors.copy()
            while queue:
                current_idx = queue.pop(0)
                if current_idx in visited:
                    continue

                visited.add(current_idx)
                cluster.append(current_idx)

                # 获取当前点的邻居
                current_neighbors = []
                for j, other_point in enumerate(points):
                    if points[current_idx].distance_to(other_point) <= eps:
                        current_neighbors.append(j)

                if len(current_neighbors) >= min_pts:
                    for neighbor_idx in current_neighbors:
                        if neighbor_idx not in visited:
                            queue.append(neighbor_idx)

            # 计算簇的中心和属性
            if len(cluster) >= min_pts:
                cluster_points = [points[idx] for idx in cluster]
                center_lat = sum(p.lat for p in cluster_points) / len(cluster_points)
                center_lng = sum(p.lng for p in cluster_points) / len(cluster_points)

                # 计算半径（最大距离）
                max_distance = max(
                    GeoPoint(center_lat, center_lng).distance_to(p)
                    for p in cluster_points
                )

                # 计算强度（总权重）
                intensity = sum(p.weight for p in cluster_points)

                clusters.append(HotspotRegion(
                    center_lat=center_lat,
                    center_lng=center_lng,
                    radius=max_distance,
                    intensity=intensity,
                    news_count=len(cluster_points),
                    avg_sentiment=0.0,  # 需要从新闻数据计算
                    dominant_category="",  # 需要从新闻数据计算
                    trend="stable",
                    time_series=[]
                ))

        return clusters

    async def _analyze_hotspot_trend(self, hotspot: HotspotRegion, news_items: List[News]) -> str:
        """分析热点趋势"""
        # 获取热点区域内的新闻
        nearby_news = []
        for news in news_items:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")

            if lat and lng:
                distance = GeoPoint(hotspot.center_lat, hotspot.center_lng).distance_to(
                    GeoPoint(lat, lng)
                )
                if distance <= hotspot.radius * 2:  # 使用2倍半径
                    nearby_news.append(news)

        if len(nearby_news) < 5:
            return "insufficient_data"

        # 按时间分组分析趋势
        nearby_news.sort(key=lambda x: x.publish_date or datetime.min)

        # 分成前后两半比较
        mid_point = len(nearby_news) // 2
        first_half = nearby_news[:mid_point]
        second_half = nearby_news[mid_point:]

        # 计算平均强度
        first_intensity = sum(self._calculate_news_weight(news) for news in first_half) / len(first_half)
        second_intensity = sum(self._calculate_news_weight(news) for news in second_half) / len(second_half)

        # 判断趋势
        if second_intensity > first_intensity * 1.2:
            return "increasing"
        elif second_intensity < first_intensity * 0.8:
            return "decreasing"
        else:
            return "stable"

    async def _generate_time_series(self, db: AsyncSession, time_range: TimeRange) -> List[Dict[str, Any]]:
        """生成时间序列数据"""
        # 根据时间范围确定时间间隔
        if time_range == TimeRange.HOUR:
            interval = timedelta(minutes=10)
            points = 6  # 1小时内的6个点
        elif time_range == TimeRange.DAY:
            interval = timedelta(hours=2)
            points = 12  # 1天内的12个点
        elif time_range == TimeRange.WEEK:
            interval = timedelta(days=1)
            points = 7  # 1周内的7个点
        else:  # MONTH
            interval = timedelta(days=3)
            points = 10  # 1月内的10个点

        end_time = datetime.now(timezone.utc)
        start_time = end_time - interval * points

        time_series = []
        current_time = start_time

        while current_time < end_time:
            next_time = current_time + interval

            # 查询该时间段内的新闻
            result = await db.execute(
                select(News).where(
                    and_(
                        News.location.isnot(None),
                        News.publish_date >= current_time,
                        News.publish_date < next_time
                    )
                )
            )
            news_in_period = result.scalars().all()

            # 计算统计信息
            location_count = len([n for n in news_in_period if n.location])
            avg_intensity = sum(self._calculate_news_weight(n) for n in news_in_period) / len(news_in_period) if news_in_period else 0
            avg_sentiment = sum(n.sentiment_score or 0 for n in news_in_period) / len(news_in_period) if news_in_period else 0

            # 统计热门类别
            category_counts = {}
            for news in news_in_period:
                if news.category:
                    category_counts[news.category] = category_counts.get(news.category, 0) + 1

            top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            time_series.append({
                "timestamp": current_time.isoformat(),
                "location_count": location_count,
                "avg_intensity": avg_intensity,
                "avg_sentiment": avg_sentiment,
                "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
                "total_news": len(news_in_period)
            })

            current_time = next_time

        return time_series

    def _calculate_news_weight(self, news: News) -> float:
        """计算新闻的权重"""
        weight = 1.0

        # 时间权重
        if news.publish_date:
            hours_ago = (datetime.now(timezone.utc) - news.publish_date).total_seconds() / 3600
            if hours_ago <= self.weight_config["recency"]["hours"]:
                time_weight = self.weight_config["recency"]["weight"]
                # 指数衰减
                decay_factor = math.exp(-hours_ago / 24)
                weight *= time_weight * decay_factor

        # 情感权重
        if news.sentiment_score is not None:
            if news.sentiment_score > 50:
                weight *= self.weight_config["sentiment"]["positive_weight"]
            elif news.sentiment_score < -50:
                weight *= self.weight_config["sentiment"]["negative_weight"]

        # 类别权重
        if news.category in self.weight_config["category"]["high_impact"]:
            weight *= self.weight_config["category"]["weight"]

        return weight

    def _get_time_threshold(self, time_range: TimeRange) -> datetime:
        """获取时间阈值"""
        now = datetime.now(timezone.utc)

        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        else:  # MONTH
            return now - timedelta(days=30)

    def _calculate_heatmap_statistics(
        self, news_items: List[News], grid_cells: List[HeatmapCell]
    ) -> Dict[str, Any]:
        """计算热力图统计信息"""
        total_news = len(news_items)
        news_with_location = len([n for n in news_items if n.location])

        # 计算情感统计
        sentiment_scores = [n.sentiment_score for n in news_items if n.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # 计算类别分布
        category_counts = {}
        for news in news_items:
            if news.category:
                category_counts[news.category] = category_counts.get(news.category, 0) + 1

        # 计算地理覆盖范围
        lats = []
        lngs = []
        for news in news_items:
            loc = news.location or {}
            if loc.get("lat") and loc.get("lng"):
                lats.append(loc["lat"])
                lngs.append(loc["lng"])

        geo_coverage = {}
        if lats and lngs:
            geo_coverage = {
                "lat_range": [min(lats), max(lats)],
                "lng_range": [min(lngs), max(lngs)],
                "center_lat": (min(lats) + max(lats)) / 2,
                "center_lng": (min(lngs) + max(lngs)) / 2
            }

        return {
            "total_news": total_news,
            "news_with_location": news_with_location,
            "location_coverage_rate": news_with_location / total_news if total_news > 0 else 0,
            "avg_sentiment": round(avg_sentiment, 2),
            "category_distribution": category_counts,
            "grid_statistics": {
                "total_cells": len(grid_cells),
                "active_cells": len([c for c in grid_cells if c.intensity > 0]),
                "max_intensity": max((c.intensity for c in grid_cells), default=0),
                "avg_cell_intensity": sum(c.intensity for c in grid_cells) / len(grid_cells) if grid_cells else 0
            },
            "geographic_coverage": geo_coverage
        }

    async def analyze_geographic_patterns(
        self,
        db: AsyncSession,
        region: Optional[str] = None,
        time_range: TimeRange = TimeRange.WEEK
    ) -> Dict[str, Any]:
        """
        分析地理模式

        Args:
            db: 数据库会话
            region: 特定地区筛选
            time_range: 时间范围

        Returns:
            地理模式分析结果
        """
        time_threshold = self._get_time_threshold(time_range)

        # 构建查询
        query = select(News).where(
            and_(
                News.location.isnot(None),
                News.publish_date >= time_threshold
            )
        )

        if region:
            query = query.where(
                func.json_extract(News.location, '$.country').ilike(f'%{region}%')
            )

        result = await db.execute(query.order_by(News.publish_date.desc()))
        news_items = result.scalars().all()

        # 分析模式
        patterns = {
            "temporal_patterns": await self._analyze_temporal_patterns(news_items),
            "sentiment_patterns": await self._analyze_sentiment_patterns(news_items),
            "category_patterns": await self._analyze_category_patterns(news_items),
            "geographic_clusters": await self._analyze_geographic_clusters(news_items),
            "event_correlations": await self._analyze_event_correlations(news_items)
        }

        return {
            "region": region,
            "time_range": time_range.value,
            "total_news_analyzed": len(news_items),
            "patterns": patterns
        }

    async def _analyze_temporal_patterns(self, news_items: List[News]) -> Dict[str, Any]:
        """分析时间模式"""
        # 按小时统计
        hourly_counts = {}
        for news in news_items:
            if news.publish_date:
                hour = news.publish_date.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        # 按星期统计
        weekly_counts = {}
        for news in news_items:
            if news.publish_date:
                weekday = news.publish_date.weekday()
                weekly_counts[weekday] = weekly_counts.get(weekday, 0) + 1

        return {
            "hourly_distribution": hourly_counts,
            "weekly_distribution": weekly_counts,
            "peak_hour": max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
            "peak_weekday": max(weekly_counts.items(), key=lambda x: x[1])[0] if weekly_counts else None
        }

    async def _analyze_sentiment_patterns(self, news_items: List[News]) -> Dict[str, Any]:
        """分析情感模式"""
        # 按地区分析情感
        region_sentiments = {}
        for news in news_items:
            if news.sentiment_score is not None and news.location:
                country = news.location.get("country", "Unknown")
                if country not in region_sentiments:
                    region_sentiments[country] = []
                region_sentiments[country].append(news.sentiment_score)

        # 计算平均情感
        region_avg_sentiments = {}
        for country, sentiments in region_sentiments.items():
            region_avg_sentiments[country] = sum(sentiments) / len(sentiments)

        return {
            "regional_sentiments": region_avg_sentiments,
            "most_positive_region": max(region_avg_sentiments.items(), key=lambda x: x[1])[0] if region_avg_sentiments else None,
            "most_negative_region": min(region_avg_sentiments.items(), key=lambda x: x[1])[0] if region_avg_sentiments else None
        }

    async def _analyze_category_patterns(self, news_items: List[News]) -> Dict[str, Any]:
        """分析类别模式"""
        # 按地区分析类别
        region_categories = {}
        for news in news_items:
            if news.category and news.location:
                country = news.location.get("country", "Unknown")
                if country not in region_categories:
                    region_categories[country] = {}
                region_categories[country][news.category] = region_categories[country].get(news.category, 0) + 1

        # 找出每个地区的主要类别
        region_primary_categories = {}
        for country, categories in region_categories.items():
            primary_category = max(categories.items(), key=lambda x: x[1])[0]
            region_primary_categories[country] = primary_category

        return {
            "regional_categories": region_primary_categories,
            "category_distribution_by_region": region_categories
        }

    async def _analyze_geographic_clusters(self, news_items: List[News]) -> Dict[str, Any]:
        """分析地理聚类"""
        points = []
        for news in news_items:
            loc = news.location or {}
            lat = loc.get("lat")
            lng = loc.get("lng")

            if lat and lng:
                points.append(GeoPoint(lat, lng))

        if not points:
            return {"clusters": []}

        # 使用DBSCAN聚类
        clusters = self._dbscan_clustering(points)

        return {
            "cluster_count": len(clusters),
            "clusters": [
                {
                    "center": [c.center_lat, c.center_lng],
                    "radius": c.radius,
                    "news_count": c.news_count,
                    "intensity": c.intensity
                }
                for c in clusters
            ]
        }

    async def _analyze_event_correlations(self, news_items: List[News]) -> Dict[str, Any]:
        """分析事件相关性"""
        # 简化的相关性分析：查找相似时间范围内的相似新闻
        correlations = []

        # 按时间排序
        sorted_news = sorted([n for n in news_items if n.publish_date],
                           key=lambda x: x.publish_date)

        # 查找24小时内的相关新闻
        for i, news1 in enumerate(sorted_news):
            for j, news2 in enumerate(sorted_news[i+1:], i+1):
                if not news1.publish_date or not news2.publish_date:
                    continue

                time_diff = abs((news2.publish_date - news1.publish_date).total_seconds())
                if time_diff > 24 * 3600:  # 超过24小时
                    break

                # 检查是否相关（相同类别、相似地点、相似情感）
                correlation_score = 0

                if news1.category and news1.category == news2.category:
                    correlation_score += 0.3

                if (news1.location and news2.location and
                    news1.location.get("country") == news2.location.get("country")):
                    correlation_score += 0.4

                if (news1.sentiment_score is not None and news2.sentiment_score is not None and
                    abs(news1.sentiment_score - news2.sentiment_score) < 20):
                    correlation_score += 0.3

                if correlation_score > 0.6:
                    correlations.append({
                        "news_id_1": news1.id,
                        "news_id_2": news2.id,
                        "correlation_score": correlation_score,
                        "time_diff_hours": time_diff / 3600
                    })

        return {
            "correlations_count": len(correlations),
            "top_correlations": sorted(correlations,
                                     key=lambda x: x["correlation_score"],
                                     reverse=True)[:10]
        }


# 全局实例
advanced_geo_heatmap_analyzer = AdvancedGeoHeatmapAnalyzer()