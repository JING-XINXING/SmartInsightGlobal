"""
数据库索引优化
创建高性能索引以提升查询性能
"""
from sqlalchemy import text
import asyncio
from datetime import datetime

from app.core.logger import logger
from app.db.session import get_db


class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self):
        self.optimization_logs = []

    async def create_news_indexes(self, db):
        """创建新闻表的高性能索引"""
        indexes = [
            # 1. 复合索引用于分页查询优化
            {
                "name": "idx_news_publish_date_desc",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_publish_date_desc
                ON news (publish_date DESC);
                """,
                "purpose": "分页查询优化"
            },

            # 2. 情感和分类复合索引
            {
                "name": "idx_news_sentiment_category",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_sentiment_category
                ON news (sentiment_score, category)
                WHERE sentiment_score IS NOT NULL;
                """,
                "purpose": "情感和分类筛选"
            },

            # 3. 来源和发布日期复合索引
            {
                "name": "idx_news_source_publish_date",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_source_publish_date
                ON news (source, publish_date DESC);
                """,
                "purpose": "来源筛选和时间排序"
            },

            # 4. 分类和发布日期复合索引
            {
                "name": "idx_news_category_publish_date",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_category_publish_date
                ON news (category, publish_date DESC);
                """,
                "purpose": "分类筛选和时间排序"
            },

            # 5. 全文搜索向量索引（如果不存在）
            {
                "name": "idx_news_search_vector",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_search_vector
                ON news USING GIN (search_vector);
                """,
                "purpose": "全文搜索性能"
            },

            # 6. URL唯一索引（去重优化）
            {
                "name": "idx_news_url_unique",
                "sql": """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_news_url_unique
                ON news (url);
                """,
                "purpose": "URL唯一性检查"
            }
        ]

        created_indexes = []
        for index in indexes:
            try:
                await db.execute(text(index["sql"]))
                await db.commit()
                created_indexes.append(index["name"])
                logger.info(f"索引创建成功: {index['name']} - {index['purpose']}")
                self.optimization_logs.append({
                    "action": "create_index",
                    "index": index["name"],
                    "purpose": index["purpose"],
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"索引创建失败 {index['name']}: {e}")
                self.optimization_logs.append({
                    "action": "create_index",
                    "index": index["name"],
                    "purpose": index["purpose"],
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        return created_indexes

    async def analyze_query_performance(self, db):
        """分析查询性能"""
        analysis_queries = [
            # 1. 检查慢查询
            {
                "name": "slow_queries",
                "sql": """
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements
                WHERE mean_time > 100
                ORDER BY mean_time DESC
                LIMIT 10;
                """,
                "description": "慢查询分析"
            },

            # 2. 检查索引使用情况
            {
                "name": "index_usage",
                "sql": """
                SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC;
                """,
                "description": "索引使用分析"
            },

            # 3. 检查表大小
            {
                "name": "table_sizes",
                "sql": """
                SELECT
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname::text, tablename::text)) AS size,
                    pg_total_relation_size(schemaname::text, tablename::text) AS size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC;
                """,
                "description": "表大小分析"
            },

            # 4. 检查缓存命中率
            {
                "name": "cache_hit_ratio",
                "sql": """
                SELECT
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_hit) * 100.0 / (sum(heap_blks_read) + sum(heap_blks_hit)) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database();
                """,
                "description": "缓存命中率分析"
            }
        ]

        performance_data = {}
        for query_info in analysis_queries:
            try:
                result = await db.execute(text(query_info["sql"]))
                data = result.fetchall()
                performance_data[query_info["name"]] = {
                    "data": data,
                    "description": query_info["description"],
                    "query": query_info["sql"]
                }
                logger.info(f"性能分析完成: {query_info['name']}")
            except Exception as e:
                logger.error(f"性能分析失败 {query_info['name']}: {e}")
                performance_data[query_info["name"]] = {
                    "error": str(e),
                    "description": query_info["description"]
                }

        return performance_data

    async def update_table_statistics(self, db):
        """更新表统计信息"""
        stats_queries = [
            {
                "name": "news_stats",
                "sql": "ANALYZE VERBOSE news;",
                "description": "更新新闻表统计信息"
            },
            {
                "name": "all_tables",
                "sql": "ANALYZE;",
                "description": "更新所有表统计信息"
            }
        ]

        for stat_query in stats_queries:
            try:
                await db.execute(text(stat_query["sql"]))
                await db.commit()
                logger.info(f"统计信息更新: {stat_query['name']}")
                self.optimization_logs.append({
                    "action": "update_stats",
                    "table": stat_query["name"],
                    "description": stat_query["description"],
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"统计信息更新失败 {stat_query['name']}: {e}")
                self.optimization_logs.append({
                    "action": "update_stats",
                    "table": stat_query["name"],
                    "description": stat_query["description"],
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

    async def optimize_configuration(self, db):
        """数据库配置优化"""
        optimizations = [
            # 1. 增加共享缓冲区
            {
                "name": "shared_buffers",
                "sql": "ALTER SYSTEM SET shared_buffers = '256MB';",
                "description": "增加共享缓冲区"
            },

            # 2. 增加工作内存
            {
                "name": "work_mem",
                "sql": "ALTER SYSTEM SET work_mem = '8MB';",
                "description": "增加排序内存"
            },

            # 3. 优化查询规划器
            {
                "name": "random_page_cost",
                "sql": "ALTER SYSTEM SET random_page_cost = 1.1;",
                "description": "优化随机页面成本"
            }
        ]

        for opt in optimizations:
            try:
                await db.execute(text(opt["sql"]))
                await db.commit()
                logger.info(f"配置优化: {opt['name']} - {opt['description']}")
                self.optimization_logs.append({
                    "action": "config_optimization",
                    "setting": opt["name"],
                    "description": opt["description"],
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"配置优化失败 {opt['name']}: {e}")
                self.optimization_logs.append({
                    "action": "config_optimization",
                    "setting": opt["name"],
                    "description": opt["description"],
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

    def get_optimization_report(self):
        """获取优化报告"""
        return {
            "summary": {
                "total_actions": len(self.optimization_logs),
                "successful_actions": len([log for log in self.optimization_logs if log.get("status") == "success"]),
                "failed_actions": len([log for log in self.optimization_logs if log.get("status") == "failed"])
            },
            "logs": self.optimization_logs,
            "timestamp": datetime.utcnow().isoformat()
        }


async def run_optimization():
    """运行数据库优化"""
    logger.info("开始数据库优化...")

    async with get_db() as db:
        optimizer = DatabaseOptimizer()

        # 1. 创建索引
        logger.info("创建性能索引...")
        created_indexes = await optimizer.create_news_indexes(db)

        # 2. 分析性能
        logger.info("分析查询性能...")
        performance_data = await optimizer.analyze_query_performance(db)

        # 3. 更新统计信息
        logger.info("更新表统计信息...")
        await optimizer.update_table_statistics(db)

        # 4. 配置优化（谨慎使用）
        logger.info("优化数据库配置...")
        await optimizer.optimize_configuration(db)

        # 生成报告
        report = optimizer.get_optimization_report()

        logger.info("数据库优化完成")

        return {
            "status": "success",
            "indexes_created": created_indexes,
            "performance_analysis": performance_data,
            "optimization_report": report
        }


if __name__ == "__main__":
    asyncio.run(run_optimization())