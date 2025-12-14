#!/usr/bin/env python3
"""
补充已分析新闻的地理位置数据

功能：
    - 查找已分析但没有地理位置的新闻
    - 调用 AI 提取地理位置信息
    - 更新数据库
    - 支持为所有新闻（包括未分析的）补充位置

使用方法：
    cd backend
    python backfill_locations.py [--limit 100] [--batch-size 10]
    python backfill_locations.py --all  # 处理所有新闻（包括未分析的）
    python backfill_locations.py --stats  # 只显示统计信息
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
from app.db.session import AsyncSessionLocal
from app.models.news import News
from app.core.analyzer import news_analyzer
from app.core.logger import logger


async def backfill_locations(limit: int = 100, batch_size: int = 10, include_all: bool = False):
    """
    为没有地理位置的新闻补充位置数据
    
    Args:
        limit: 处理的最大新闻数量
        batch_size: 每批处理数量
        include_all: 是否包括未分析的新闻
    """
    logger.info(f"开始补充地理位置数据，限制: {limit}, 批次大小: {batch_size}, 包含所有: {include_all}")
    
    processed = 0
    success = 0
    failed = 0
    
    async with AsyncSessionLocal() as db:
        # 构建查询条件
        if include_all:
            # 所有没有位置的新闻
            query = select(News).where(
                or_(
                    News.location.is_(None),
                    func.json_extract(News.location, '$.country') == '',
                    func.json_extract(News.location, '$.lat') == 0
                )
            )
        else:
            # 只处理已分析但没有位置的新闻
            query = select(News).where(
                and_(
                    News.sentiment_score.isnot(None),  # 已分析
                    or_(
                        News.location.is_(None),
                        func.json_extract(News.location, '$.country') == ''
                    )
                )
            )
        
        result = await db.execute(query.limit(limit))
        news_list = result.scalars().all()
        
        total = len(news_list)
        logger.info(f"找到 {total} 条需要补充位置的新闻")
        print(f"\n🔍 找到 {total} 条需要补充位置的新闻\n")
        
        if not news_list:
            logger.info("没有需要处理的新闻")
            return {"processed": 0, "success": 0, "failed": 0}
        
        # 分批处理
        batch_count = (total + batch_size - 1) // batch_size
        
        for batch_idx in range(0, total, batch_size):
            batch = news_list[batch_idx:batch_idx + batch_size]
            current_batch = batch_idx // batch_size + 1
            
            print(f"📦 处理批次 {current_batch}/{batch_count} ({len(batch)} 条新闻)")
            logger.info(f"处理批次 {current_batch}/{batch_count}, 包含 {len(batch)} 条新闻")
            
            for news in batch:
                try:
                    title_short = news.title[:40] + "..." if len(news.title) > 40 else news.title
                    
                    # 提取地理位置
                    location = await news_analyzer.extract_location(
                        news.title,
                        news.content or news.summary or ""
                    )
                    
                    if location and location.get("country") and location.get("lat", 0) != 0:
                        news.location = location
                        await db.commit()
                        success += 1
                        country_info = f"{location.get('country_cn', location.get('country'))}"
                        if location.get('city'):
                            country_info += f", {location.get('city')}"
                        print(f"  ✅ ID {news.id}: {title_short}")
                        print(f"     → {country_info} ({location.get('lat'):.2f}, {location.get('lng'):.2f})")
                        logger.info(f"成功提取位置 ID {news.id}: {country_info}")
                    else:
                        failed += 1
                        print(f"  ⚠️ ID {news.id}: {title_short} - 无法提取位置")
                        logger.info(f"无法提取位置 ID {news.id}")
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"处理新闻 ID {news.id} 失败: {e}")
                    print(f"  ❌ ID {news.id}: 处理失败 - {str(e)[:50]}")
                    await db.rollback()
                    processed += 1
                    failed += 1
                    continue
            
            # 显示进度
            progress = (batch_idx + len(batch)) / total * 100
            print(f"   进度: {progress:.1f}% ({processed}/{total})")
            print()
            
            # 每批次后暂停一下，避免API限流
            if current_batch < batch_count:
                await asyncio.sleep(1)
    
    logger.info(f"补充完成! 处理: {processed}, 成功: {success}, 失败: {failed}")
    return {"processed": processed, "success": success, "failed": failed}


async def show_stats():
    """显示当前统计信息"""
    async with AsyncSessionLocal() as db:
        # 总新闻数
        total_result = await db.execute(select(func.count(News.id)))
        total = total_result.scalar() or 0
        
        # 已分析
        analyzed_result = await db.execute(
            select(func.count(News.id)).where(News.sentiment_score.isnot(None))
        )
        analyzed = analyzed_result.scalar() or 0
        
        # 有位置（且坐标有效）
        with_location_result = await db.execute(
            select(func.count(News.id)).where(
                and_(
                    News.location.isnot(None),
                    func.json_extract(News.location, '$.country') != '',
                    func.json_extract(News.location, '$.lat') != 0
                )
            )
        )
        with_location = with_location_result.scalar() or 0
        
        # 需要补充位置（已分析但没有有效位置）
        need_location_result = await db.execute(
            select(func.count(News.id)).where(
                and_(
                    News.sentiment_score.isnot(None),
                    or_(
                        News.location.is_(None),
                        func.json_extract(News.location, '$.country') == ''
                    )
                )
            )
        )
        need_location = need_location_result.scalar() or 0
        
        # 所有没有位置的新闻
        all_need_location_result = await db.execute(
            select(func.count(News.id)).where(
                or_(
                    News.location.is_(None),
                    func.json_extract(News.location, '$.country') == ''
                )
            )
        )
        all_need_location = all_need_location_result.scalar() or 0
        
        print("\n" + "=" * 55)
        print("    SmartInsight Global - 数据统计")
        print("=" * 55)
        print(f"  📰 总新闻数:              {total}")
        if total > 0:
            print(f"  🔬 已分析:                {analyzed} ({analyzed/total*100:.1f}%)")
            print(f"  📍 有地理位置:            {with_location} ({with_location/total*100:.1f}%)")
            print(f"  ⏳ 需要补充位置(已分析):  {need_location}")
            print(f"  ⏳ 需要补充位置(全部):    {all_need_location}")
        else:
            print("  🔬 已分析:                0")
            print("  📍 有地理位置:            0")
            print("  ⏳ 需要补充位置:          0")
        print("=" * 55)
        
        return {
            "total": total,
            "analyzed": analyzed,
            "with_location": with_location,
            "need_location": need_location,
            "all_need_location": all_need_location
        }


def main():
    parser = argparse.ArgumentParser(
        description="补充新闻的地理位置数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python backfill_locations.py --stats          # 只显示统计信息
  python backfill_locations.py                  # 处理100条已分析的新闻
  python backfill_locations.py -l 50 -b 5       # 处理50条，每批5条
  python backfill_locations.py --all -l 200     # 处理所有新闻（包括未分析的）
        """
    )
    parser.add_argument("--limit", "-l", type=int, default=100, 
                        help="处理的最大新闻数量 (默认: 100)")
    parser.add_argument("--batch-size", "-b", type=int, default=10, 
                        help="每批处理数量 (默认: 10)")
    parser.add_argument("--stats", "-s", action="store_true", 
                        help="只显示统计信息")
    parser.add_argument("--all", "-a", action="store_true", 
                        help="处理所有新闻（包括未分析的）")
    
    args = parser.parse_args()
    
    if args.stats:
        asyncio.run(show_stats())
    else:
        # 显示初始统计
        print("\n📊 初始状态:")
        asyncio.run(show_stats())
        
        print("\n🚀 开始补充地理位置数据...\n")
        result = asyncio.run(backfill_locations(args.limit, args.batch_size, args.all))
        
        print("\n" + "=" * 55)
        print("    处理结果")
        print("=" * 55)
        print(f"  📝 处理总数: {result['processed']}")
        print(f"  ✅ 成功:     {result['success']}")
        print(f"  ❌ 失败:     {result['failed']}")
        if result['processed'] > 0:
            success_rate = result['success'] / result['processed'] * 100
            print(f"  📈 成功率:   {success_rate:.1f}%")
        print("=" * 55)
        
        print("\n📊 最终状态:")
        asyncio.run(show_stats())


if __name__ == "__main__":
    main()

