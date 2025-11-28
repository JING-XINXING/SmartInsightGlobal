import asyncio
from app.core.celery_app import celery_app
from app.core.crawler import crawler
from app.core.logger import logger
from app.core.analyzer import news_analyzer
from app.db.session import AsyncSessionLocal
from app.crud.crud_news import create_news_if_not_exists
from app.schemas.news import NewsCreate
from sqlalchemy.future import select
from app.models.news import News

async def fetch_and_save_feeds_async():
    """
    Fetch news from multiple RSS feeds and save to database.
    """
    # List of feeds to crawl
    feeds = [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theguardian.com/world/rss"
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
    Analyze news articles that haven't been analyzed yet.
    """
    logger.info("Starting AI analysis task for unanalyzed news")
    analyzed_count = 0
    
    async with AsyncSessionLocal() as db:
        # Find news without analysis
        result = await db.execute(
            select(News).where(News.sentiment_score == None).limit(10)
        )
        news_list = result.scalars().all()
        
        logger.info(f"Found {len(news_list)} unanalyzed news articles")
        
        for news_item in news_list:
            try:
                logger.info(f"Analyzing news ID {news_item.id}: {news_item.title[:50]}...")
                
                # Perform AI analysis
                analysis = await news_analyzer.analyze_news_full(
                    news_item.title,
                    news_item.content or news_item.summary
                )
                
                # Update news with analysis results
                if analysis.get("sentiment_score") is not None:
                    news_item.sentiment_score = analysis["sentiment_score"]
                if analysis.get("keywords"):
                    news_item.keywords = analysis["keywords"]
                if analysis.get("category"):
                    news_item.category = analysis["category"]
                
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

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks for Celery Beat.
    """
    logger.info("Setting up periodic tasks")
    # Fetch news every 60 minutes
    sender.add_periodic_task(3600.0, fetch_news_task.s(), name='fetch-news-every-hour')
    # Analyze news every 30 minutes
    sender.add_periodic_task(1800.0, analyze_news_task.s(), name='analyze-news-every-30min')
    logger.info("Periodic tasks configured: fetch-news-every-hour, analyze-news-every-30min")
