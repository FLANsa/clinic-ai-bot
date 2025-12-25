"""
Background Tasks Scheduler using APScheduler
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Conversation

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """الحصول على scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def cleanup_old_conversations(days: int = 90):
    """
    تنظيف المحادثات القديمة (أقدم من X يوم)
    
    Args:
        days: عدد الأيام (افتراضي: 90)
    """
    db: Session = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # حذف المحادثات القديمة
        deleted_count = db.query(Conversation).filter(
            Conversation.created_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old conversations (older than {days} days)")
    except Exception as e:
        logger.error(f"Error cleaning up old conversations: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def generate_daily_report():
    """إنشاء تقرير يومي (يمكن إرساله بالبريد الإلكتروني)"""
    logger.info("Generating daily report...")
    # TODO: تنفيذ إنشاء تقرير يومي
    pass


def start_scheduler():
    """بدء تشغيل scheduler"""
    scheduler_instance = get_scheduler()
    
    # تنظيف المحادثات القديمة كل أسبوع (الأحد = sun أو 6)
    scheduler_instance.add_job(
        cleanup_old_conversations,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='cleanup_old_conversations',
        replace_existing=True
    )
    
    # تقرير يومي (كل يوم الساعة 9 صباحاً)
    scheduler_instance.add_job(
        generate_daily_report,
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_report',
        replace_existing=True
    )
    
    scheduler_instance.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """إيقاف scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")

