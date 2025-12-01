import asyncio
import subprocess
import os
from pathlib import Path
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.crawler import crawler
from app.core.logger import logger
from app.core.analyzer import news_analyzer
from app.core.scheduler_config import scheduler_config
from app.db.session import AsyncSessionLocal
from app.crud.crud_news import create_news_if_not_exists
from app.schemas.news import NewsCreate
from sqlalchemy.future import select
from app.models.news import News

# 备份脚本路径
BACKUP_SCRIPT = Path(__file__).parent.parent.parent.parent / "scripts" / "backup" / "backup_local.sh"

async def fetch_and_save_feeds_async():
    """
    Fetch news from multiple RSS feeds and save to database.
    """
    # List of feeds to crawl
    feeds = [
        # Major Global News
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theguardian.com/world/rss",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://apnews.com/hub/world-news.rss",
        "http://rss.cnn.com/rss/edition_world.rss",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://feeds.washingtonpost.com/rss/world",
        
        # European & Asian Perspectives
        "https://www.dw.com/en/top-stories/s-9097/rss.xml",
        "https://www.france24.com/en/rss",
        "https://www3.nhk.or.jp/nhkworld/en/news/list.xml",
        "https://www.scmp.com/rss/2/feed",
        "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        
        # Tech & Finance
        "https://techcrunch.com/feed/",
        "https://www.economist.com/the-world-this-week/rss.xml"
    ]
    
    logger.info(f"Starting news fetch task for {len(feeds)} feeds")
    total_fetched = 0
    total_saved = 0
    
    async with AsyncSessionLocal() as db:
        for url in feeds:
            try:
                logger.info(f"Processing feed: {url}")
                entries = await crawler.fetch_feed(url)
                
                for entry in entries:
                    try:
                        news_in = NewsCreate(
                            title=entry['title'],
                            content=entry['content'] or entry['summary'],
                            source=entry['source'],
                            url=entry['url'],
                            publish_date=entry['publish_date'],
                            summary=entry['summary']
                        )
                        
                        result = await create_news_if_not_exists(db, news_in)
                        if result:
                            total_saved += 1
                    except Exception as e:
                        logger.error(f"Error saving news from {url}: {e}", exc_info=True)
                        continue
                
                total_fetched += len(entries)
                logger.info(f"Processed {len(entries)} entries from {url}")
                
            except Exception as e:
                logger.error(f"Error processing feed {url}: {e}", exc_info=True)
                continue
    
    logger.info(f"News fetch task completed. Fetched: {total_fetched}, Saved: {total_saved}")
    return {"fetched": total_fetched, "saved": total_saved}

async def analyze_unanalyzed_news_async():
    """
    分析未处理的新闻文章
    使用 AI 进行情感分析、关键词提取和分类
    """
    logger.info("开始 AI 分析任务...")
    analyzed_count = 0
    
    # 从配置中获取批次大小
    config = scheduler_config.get_config()
    batch_size = config.get("analyze_batch_size", 50)
    
    async with AsyncSessionLocal() as db:
        # 查找未分析的新闻
        result = await db.execute(
            select(News).where(News.sentiment_score == None).limit(batch_size)
        )
        news_list = result.scalars().all()
        
        logger.info(f"Found {len(news_list)} unanalyzed news articles")
        
        for news_item in news_list:
            try:
                logger.info(f"Analyzing news ID {news_item.id}: {news_item.title[:50]}...")
                
                # Perform AI analysis (with location extraction enabled)
                analysis = await news_analyzer.analyze_news_full(
                    news_item.title,
                    news_item.content or news_item.summary,
                    extract_location=True  # 启用地理位置提取
                )
                
                # Update news with analysis results
                if analysis.get("sentiment_score") is not None:
                    news_item.sentiment_score = analysis["sentiment_score"]
                if analysis.get("keywords"):
                    news_item.keywords = analysis["keywords"]
                if analysis.get("category"):
                    news_item.category = analysis["category"]
                if analysis.get("location"):
                    news_item.location = analysis["location"]
                
                await db.commit()
                analyzed_count += 1
                logger.info(f"Successfully analyzed news ID {news_item.id}")
                
            except Exception as e:
                logger.error(f"Error analyzing news ID {news_item.id}: {e}", exc_info=True)
                await db.rollback()
                continue
    
    logger.info(f"AI analysis task completed. Analyzed: {analyzed_count}")
    return {"analyzed": analyzed_count}

@celery_app.task(acks_late=True, bind=True, max_retries=3)
def fetch_news_task(self):
    """
    Celery task to fetch news from RSS feeds and save to DB.
    """
    try:
        logger.info("Celery task 'fetch_news_task' started")
        result = asyncio.run(fetch_and_save_feeds_async())
        logger.info(f"Celery task 'fetch_news_task' completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Celery task 'fetch_news_task' failed: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@celery_app.task(acks_late=True, bind=True, max_retries=3)
def analyze_news_task(self):
    """
    Celery task to analyze unanalyzed news with AI.
    """
    try:
        logger.info("Celery task 'analyze_news_task' started")
        result = asyncio.run(analyze_unanalyzed_news_async())
        logger.info(f"Celery task 'analyze_news_task' completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Celery task 'analyze_news_task' failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(acks_late=True, bind=True, max_retries=2)
def backup_database_task(self):
    """
    Celery task to backup the database.
    执行本地数据库备份，可选上传到云端。
    """
    try:
        logger.info("Celery task 'backup_database_task' started")
        
        # 检查备份脚本是否存在
        if not BACKUP_SCRIPT.exists():
            logger.error(f"备份脚本不存在: {BACKUP_SCRIPT}")
            return {"success": False, "error": "backup script not found"}
        
        # 执行备份脚本（不需要参数，脚本使用默认配置）
        result = subprocess.run(
            [str(BACKUP_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=600,  # 10 分钟超时
            env={**os.environ, "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD or ""}
        )
        
        if result.returncode == 0:
            logger.info(f"数据库备份成功:\n{result.stdout}")
            
            # 尝试上传到云端 (可选)
            try:
                upload_script = BACKUP_SCRIPT.parent / "backup_upload.py"
                if upload_script.exists():
                    config_file = BACKUP_SCRIPT.parent / "config.yaml"
                    if config_file.exists():
                        upload_result = subprocess.run(
                            ["python3", str(upload_script), "upload", "-c", str(config_file)],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if upload_result.returncode == 0:
                            logger.info(f"云端同步成功:\n{upload_result.stdout}")
                        else:
                            logger.warning(f"云端同步失败: {upload_result.stderr}")
            except Exception as e:
                logger.warning(f"云端同步异常 (忽略): {e}")
            
            return {"success": True, "output": result.stdout}
        else:
            logger.error(f"数据库备份失败: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        logger.error("备份任务超时")
        raise self.retry(exc=Exception("backup timeout"), countdown=300)
    except Exception as e:
        logger.error(f"Celery task 'backup_database_task' failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300)

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    设置 Celery Beat 定时任务
    从 Redis 配置中读取任务频率
    """
    logger.info("正在设置定时任务...")
    
    # 从配置中获取频率设置
    config = scheduler_config.get_config()
    fetch_interval = scheduler_config.get_fetch_interval_seconds()
    analyze_interval = scheduler_config.get_analyze_interval_seconds()
    
    logger.info(f"当前配置: 采集间隔={config['fetch_interval_hours']}小时, "
                f"分析间隔={config['analyze_interval_minutes']}分钟")
    
    # 设置新闻采集定时任务
    if config.get("fetch_enabled", True):
        sender.add_periodic_task(
            fetch_interval,
            fetch_news_task.s(),
            name=f'fetch-news-every-{config["fetch_interval_hours"]}h'
        )
        logger.info(f"已启用新闻采集任务: 每 {config['fetch_interval_hours']} 小时执行")
    else:
        logger.info("新闻采集任务已禁用")
    
    # 设置新闻分析定时任务
    if config.get("analyze_enabled", True):
        sender.add_periodic_task(
            analyze_interval,
            analyze_news_task.s(),
            name=f'analyze-news-every-{config["analyze_interval_minutes"]}min'
        )
        logger.info(f"已启用新闻分析任务: 每 {config['analyze_interval_minutes']} 分钟执行")
    else:
        logger.info("新闻分析任务已禁用")
    
    # 设置数据库备份定时任务 (每天凌晨 2:00 执行)
    if config.get("backup_enabled", True):
        from celery.schedules import crontab
        sender.add_periodic_task(
            crontab(hour=2, minute=0),  # 每天凌晨 2:00
            backup_database_task.s(),
            name='backup-database-daily-2am'
        )
        logger.info("已启用数据库备份任务: 每天凌晨 2:00 执行")
    else:
        logger.info("数据库备份任务已禁用")
    
    logger.info("定时任务配置完成")
