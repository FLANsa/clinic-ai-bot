"""
خدمة التحليلات والإحصائيات
"""
from typing import Dict, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models import Conversation, UnansweredQuestion, PendingHandoff


def total_conversations(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> int:
    """
    إجمالي عدد المحادثات في نطاق زمني
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        عدد المحادثات
    """
    query = db_session.query(Conversation)
    
    if date_from:
        query = query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    return query.count()


def conversations_by_channel(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, int]:
    """
    عدد المحادثات حسب القناة
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        قاموس {channel: count}
    """
    query = db_session.query(
        Conversation.channel,
        func.count(Conversation.id).label('count')
    )
    
    if date_from:
        query = query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    results = query.group_by(Conversation.channel).all()
    
    return {channel: count for channel, count in results}


def avg_satisfaction(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Optional[float]:
    """
    متوسط درجة الرضا (لم يعد موجوداً - إرجاع None)
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        None (satisfaction_score تم إزالته من النموذج)
    """
    # satisfaction_score تم إزالته من النموذج المبسط
    return None


def count_unrecognized(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> int:
    """
    عدد الرسائل غير المفهومة
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        عدد الرسائل غير المفهومة
    """
    query = db_session.query(Conversation).filter(Conversation.unrecognized == True)
    
    if date_from:
        query = query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    return query.count()


def count_handoffs(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> int:
    """
    عدد التحويلات لموظفين
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        عدد التحويلات
    """
    query = db_session.query(Conversation).filter(Conversation.needs_handoff == True)
    
    if date_from:
        query = query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    return query.count()


def get_channel_analytics(db_session: Session, channel: str, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict:
    """
    إحصائيات مفصلة لقناة معينة
    
    Args:
        db_session: جلسة قاعدة البيانات
        channel: اسم القناة (whatsapp, instagram, tiktok, google_maps)
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        قاموس يحتوي على:
        - total_conversations: إجمالي المحادثات
        - avg_satisfaction: متوسط الرضا
        - unrecognized_count: عدد الرسائل غير المفهومة
        - handoffs_count: عدد التحويلات
        - satisfaction_count: عدد التقييمات
    """
    query = db_session.query(Conversation).filter(Conversation.channel == channel)
    
    if date_from:
        query = query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    # إجمالي المحادثات
    total = query.count()
    
    # متوسط الرضا (لم يعد موجوداً)
    avg_sat = None
    
    # عدد الرسائل غير المفهومة
    unrecognized = query.filter(Conversation.unrecognized == True).count()
    
    # عدد التحويلات
    handoffs = query.filter(Conversation.needs_handoff == True).count()
    
    # عدد التقييمات (لم يعد موجوداً)
    satisfaction_count = 0
    
    return {
        "total_conversations": total,
        "avg_satisfaction": avg_sat,
        "unrecognized_count": unrecognized,
        "handoffs_count": handoffs,
        "satisfaction_count": satisfaction_count
    }


def get_all_channels_analytics(db_session: Session, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, Dict]:
    """
    إحصائيات مفصلة لكل القنوات
    
    Args:
        db_session: جلسة قاعدة البيانات
        date_from: تاريخ البداية
        date_to: تاريخ النهاية
    
    Returns:
        قاموس {channel: analytics_dict}
    """
    # الحصول على جميع القنوات الفريدة
    channels_query = db_session.query(Conversation.channel).distinct()
    if date_from:
        channels_query = channels_query.filter(Conversation.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        channels_query = channels_query.filter(Conversation.created_at <= datetime.combine(date_to, datetime.max.time()))
    
    channels = [row[0] for row in channels_query.all()]
    
    result = {}
    for channel in channels:
        result[channel] = get_channel_analytics(db_session, channel, date_from, date_to)
    
    return result

