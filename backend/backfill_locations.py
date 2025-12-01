#!/usr/bin/env python3
"""
补充已分析新闻的地理位置数据

功能：
    - 查找已分析但没有地理位置的新闻
    - 调用 AI 提取地理位置信息
    - 更新数据库

使用方法：
    cd backend
    python backfill_locations.py [--limit 100] [--batch-size 10]
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.future import select
from sqlalchemy import and_
from app.db.session import AsyncSessionLocal
from app.models.news import News
from app.core.analyzer import news_analyzer
from app.core.logger import logger


async def backfill_locations(limit: int = 100, batch_size: int = 10):
    """
    为已分析但没有地理位置的新闻补充位置数据
    
    Args:
        limit: 处理的最大新闻数量
        batch_size: 每批处理数量
    """
    logger.info(f"开始补充地理位置数据，限制: {limit}, 批次大小: {batch_size}")
    
    processed = 0
    success = 0
    
    async with AsyncSessionLocal() as db:
        # 查找已分析但没有位置的新闻
        result = await db.execute(
            select(News).where(
                and_(
                    News.sentiment_score.isnot(None),  # 已分析
                    News.location.is_(None)  # 没有位置
                )
            ).limit(limit)
        )
        news_list = result.scalars().all()
        
        logger.info(f"找到 {len(news_list)} 条需要补充位置的新闻")
        
        if not news_list:
            logger.info("没有需要处理的新闻")
            return {"processed": 0, "success": 0}
        
        # 分批处理
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]
            logger.info(f"处理批次 {i // batch_size + 1}, 包含 {len(batch)} 条新闻")
            
            for news in batch:
                try:
                    logger.info(f"提取位置: ID {news.id} - {news.title[:50]}...")
                    
                    # 提取地理位置
                    location = await news_analyzer.extract_location(
                        news.title,
                        news.content or news.summary or ""
                    )
                    
                    if location and location.get("country"):
                        news.location = location
                        await db.commit()
                        success += 1
                        logger.info(f"  成功: {location.get('country')}, {location.get('city', '')}")
                    else:
                        logger.info(f"  无法提取位置")
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"处理新闻 ID {news.id} 失败: {e}")
                    await db.rollback()
                    processed += 1
                    continue
            
            # 每批次后暂停一下，避免API限流
            await asyncio.sleep(1)
    
    logger.info(f"补充完成! 处理: {processed}, 成功: {success}")
    return {"processed": processed, "success": success}


async def show_stats():
    """显示当前统计信息"""
    async with AsyncSessionLocal() as db:
        # 总新闻数
        total_result = await db.execute(select(News))
        total = len(total_result.scalars().all())
        
        # 已分析
        analyzed_result = await db.execute(
            select(News).where(News.sentiment_score.isnot(None))
        )
        analyzed = len(analyzed_result.scalars().all())
        
        # 有位置
        with_location_result = await db.execute(
            select(News).where(News.location.isnot(None))
        )
        with_location = len(with_location_result.scalars().all())
        
        # 需要补充位置
        need_location_result = await db.execute(
            select(News).where(
                and_(
                    News.sentiment_score.isnot(None),
                    News.location.is_(None)
                )
            )
        )
        need_location = len(need_location_result.scalars().all())
        
        print("\n" + "=" * 50)
        print("SmartInsight Global - 数据统计")
        print("=" * 50)
        print(f"总新闻数:           {total}")
        print(f"已分析:             {analyzed} ({analyzed/total*100:.1f}%)" if total > 0 else "已分析:             0")
        print(f"有地理位置:         {with_location} ({with_location/total*100:.1f}%)" if total > 0 else "有地理位置:         0")
        print(f"需要补充位置:       {need_location}")
        print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="补充已分析新闻的地理位置数据")
    parser.add_argument("--limit", "-l", type=int, default=100, help="处理的最大新闻数量 (默认: 100)")
    parser.add_argument("--batch-size", "-b", type=int, default=10, help="每批处理数量 (默认: 10)")
    parser.add_argument("--stats", "-s", action="store_true", help="只显示统计信息")
    
    args = parser.parse_args()
    
    if args.stats:
        asyncio.run(show_stats())
    else:
        asyncio.run(show_stats())
        print("开始补充地理位置数据...\n")
        result = asyncio.run(backfill_locations(args.limit, args.batch_size))
        print(f"\n结果: 处理 {result['processed']} 条, 成功 {result['success']} 条")
        asyncio.run(show_stats())


if __name__ == "__main__":
    main()

