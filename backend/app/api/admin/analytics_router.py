"""
Analytics admin router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.db.session import get_db
from app.middleware.auth import verify_api_key
from app.services.analytics_service import (
    total_conversations,
    conversations_by_channel,
    avg_satisfaction,
    count_unrecognized,
    count_handoffs,
    get_all_channels_analytics,
    get_channel_analytics
)

router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics"])


@router.get("/summary")
async def get_analytics_summary(
    from_date: Optional[date] = Query(None, alias="from", description="تاريخ البداية (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, alias="to", description="تاريخ النهاية (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    ملخص التحليلات والإحصائيات
    
    Returns:
        - total_conversations: إجمالي المحادثات
        - conversations_by_channel: المحادثات حسب القناة
        - avg_satisfaction: متوسط الرضا
        - unrecognized_count: عدد الرسائل غير المفهومة
        - handoffs_count: عدد التحويلات
    """
    total = total_conversations(db, from_date, to_date)
    by_channel = conversations_by_channel(db, from_date, to_date)
    avg_sat = avg_satisfaction(db, from_date, to_date)
    unrecognized = count_unrecognized(db, from_date, to_date)
    handoffs = count_handoffs(db, from_date, to_date)
    
    return {
        "total_conversations": total,
        "conversations_by_channel": by_channel,
        "avg_satisfaction": avg_sat,
        "unrecognized_count": unrecognized,
        "handoffs_count": handoffs
    }


@router.get("/by-channel")
async def get_analytics_by_channel(
    from_date: Optional[date] = Query(None, alias="from", description="تاريخ البداية (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, alias="to", description="تاريخ النهاية (YYYY-MM-DD)"),
    channel: Optional[str] = Query(None, description="اسم القناة (whatsapp, instagram, tiktok, google_maps) - اختياري"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    إحصائيات مفصلة حسب القناة
    
    إذا تم تحديد channel، يتم إرجاع إحصائيات تلك القناة فقط.
    إذا لم يتم تحديد channel، يتم إرجاع إحصائيات جميع القنوات.
    
    Returns:
        إحصائيات مفصلة لكل قناة:
        - total_conversations: إجمالي المحادثات
        - avg_satisfaction: متوسط الرضا
        - unrecognized_count: عدد الرسائل غير المفهومة
        - handoffs_count: عدد التحويلات
        - satisfaction_count: عدد التقييمات
    """
    if channel:
        # إحصائيات قناة واحدة
        analytics = get_channel_analytics(db, channel, from_date, to_date)
        return {
            "channel": channel,
            "analytics": analytics
        }
    else:
        # إحصائيات جميع القنوات
        analytics = get_all_channels_analytics(db, from_date, to_date)
        return {
            "channels": analytics
        }

