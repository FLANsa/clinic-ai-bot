"""
Data Export Router - تصدير البيانات (CSV, JSON)
"""
import csv
import json
from io import StringIO
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.db.session import get_db
from app.middleware.auth import verify_api_key
from app.db.models import Conversation, Appointment, Branch, Doctor, Service

router = APIRouter(prefix="/admin/export", tags=["Admin - Export"])


@router.get("/conversations")
async def export_conversations(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """تصدير المحادثات"""
    from datetime import datetime
    
    query = db.query(Conversation)
    
    if from_date:
        query = query.filter(Conversation.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Conversation.created_at <= datetime.combine(to_date, datetime.max.time()))
    
    conversations = query.order_by(Conversation.created_at.desc()).all()
    
    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "User ID", "Channel", "Message", "Reply", "Intent",
            "DB Context Used", "Unrecognized", "Needs Handoff", "Created At"
        ])
        
        for conv in conversations:
            writer.writerow([
                str(conv.id),
                conv.user_id,
                conv.channel,
                conv.user_message,
                conv.bot_reply or "",
                conv.intent or "",
                conv.db_context_used,
                conv.unrecognized,
                conv.needs_handoff,
                conv.created_at.isoformat()
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=conversations.csv"}
        )
    else:  # JSON
        data = [
            {
                "id": str(conv.id),
                "user_id": conv.user_id,
                "channel": conv.channel,
                "message": conv.user_message,
                "reply": conv.bot_reply,
                "intent": conv.intent,
                "db_context_used": conv.db_context_used,
                "unrecognized": conv.unrecognized,
                "needs_handoff": conv.needs_handoff,
                "created_at": conv.created_at.isoformat()
            }
            for conv in conversations
        ]
        return Response(
            content=json.dumps(data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=conversations.json"}
        )


@router.get("/appointments")
async def export_appointments(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """تصدير المواعيد"""
    from datetime import datetime
    
    query = db.query(Appointment)
    
    if from_date:
        query = query.filter(Appointment.datetime >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Appointment.datetime <= datetime.combine(to_date, datetime.max.time()))
    
    appointments = query.order_by(Appointment.datetime.desc()).all()
    
    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Patient Name", "Phone", "Branch", "Doctor", "Service",
            "DateTime", "Channel", "Status", "Notes", "Created At"
        ])
        
        for apt in appointments:
            writer.writerow([
                str(apt.id),
                apt.patient_name,
                apt.phone,
                apt.branch.name if apt.branch else "",
                apt.doctor.name if apt.doctor else "",
                apt.service.name if apt.service else "",
                apt.datetime.isoformat(),
                apt.channel,
                apt.status,
                apt.notes or "",
                apt.created_at.isoformat()
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=appointments.csv"}
        )
    else:  # JSON
        data = [
            {
                "id": str(apt.id),
                "patient_name": apt.patient_name,
                "phone": apt.phone,
                "branch": apt.branch.name if apt.branch else None,
                "doctor": apt.doctor.name if apt.doctor else None,
                "service": apt.service.name if apt.service else None,
                "datetime": apt.datetime.isoformat(),
                "channel": apt.channel,
                "status": apt.status,
                "notes": apt.notes,
                "created_at": apt.created_at.isoformat()
            }
            for apt in appointments
        ]
        return Response(
            content=json.dumps(data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=appointments.json"}
        )

