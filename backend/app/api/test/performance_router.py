"""
Performance Tests API Endpoint
"""
import logging
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent
from app.core.models import ConversationInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test/performance", tags=["Test - Performance"])

# مجلد لحفظ تقارير الأداء
PERFORMANCE_REPORTS_DIR = Path("backend/performance_reports")
PERFORMANCE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class PerformanceResult(BaseModel):
    """نتيجة اختبار أداء واحد"""
    question: str
    duration: float
    success: bool
    intent: Optional[str] = None
    error: Optional[str] = None
    db_context_used: bool = False
    exceeds_p95: bool = False
    exceeds_p99: bool = False


class PerformanceSummary(BaseModel):
    """ملخص نتائج الأداء"""
    total_tests: int
    success_count: int
    error_count: int
    success_rate: float
    response_time: Dict[str, float]
    intents: Dict[str, int]
    results: List[PerformanceResult]
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Test questions
TEST_QUESTIONS = [
    "ما هي الخدمات المتاحة؟",
    "أريد حجز موعد",
    "كم سعر تنظيف الأسنان؟",
    "ما هي أوقات العمل؟",
    "من هم الأطباء المتاحون؟",
]


def get_test_agent(
    db: Session = Depends(get_db)
) -> ChatAgent:
    """Dependency للحصول على ChatAgent للاختبار"""
    llm_client = LLMClient()
    return ChatAgent(
        llm_client=llm_client,
        db_session=db
    )


@router.post("/run", response_model=PerformanceSummary)
async def run_performance_tests(
    num_tests: int = 5,
    agent: ChatAgent = Depends(get_test_agent),
    db: Session = Depends(get_db)
):
    """
    تشغيل اختبارات الأداء وحفظ النتائج في ملفات JSON/Markdown
    
    Args:
        num_tests: عدد الاختبارات المراد تشغيلها (افتراضي: 5)
        agent: ChatAgent instance
        db: database session
    
    Returns:
        PerformanceSummary: ملخص نتائج الاختبارات
    """
    if num_tests < 1 or num_tests > 20:
        raise HTTPException(status_code=400, detail="عدد الاختبارات يجب أن يكون بين 1 و 20")
    
    questions = TEST_QUESTIONS[:num_tests]
    results: List[PerformanceResult] = []
    durations: List[float] = []
    intents_count: Dict[str, int] = {}
    success_count = 0
    error_count = 0
    
    logger.info(f"بدء تشغيل {num_tests} اختبار أداء...")
    
    for question in questions:
        try:
            conv_input = ConversationInput(
                channel="whatsapp",
                user_id="performance_test_user",
                message=question,
                locale="ar-SA"
            )
            
            start_time = time.time()
            output = await agent.handle_message(conv_input)
            duration = time.time() - start_time
            
            durations.append(duration)
            success_count += 1
            
            intent = output.intent or "unknown"
            intents_count[intent] = intents_count.get(intent, 0) + 1
            
            results.append(PerformanceResult(
                question=question,
                duration=duration,
                success=True,
                intent=intent,
                db_context_used=output.db_context_used
            ))
            
            db.commit()
            
        except Exception as e:
            error_count += 1
            error_msg = str(e)[:200]
            logger.error(f"خطأ في اختبار السؤال '{question}': {error_msg}")
            
            results.append(PerformanceResult(
                question=question,
                duration=0.0,
                success=False,
                error=error_msg
            ))
            
            db.rollback()
    
    # حساب الإحصائيات
    if durations:
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        
        p50_idx = n // 2
        p95_idx = int(n * 0.95) if n > 1 else 0
        p99_idx = int(n * 0.99) if n > 1 else 0
        
        response_time = {
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / n,
            "p50": sorted_durations[p50_idx] if n > 0 else 0,
            "p95": sorted_durations[p95_idx] if n > 1 else sorted_durations[0],
            "p99": sorted_durations[p99_idx] if n > 1 else sorted_durations[0]
        }
        
        # تحديد الطلبات التي تتجاوز P95/P99
        p95_threshold = response_time["p95"]
        p99_threshold = response_time["p99"]
        alerts = []
        
        for result in results:
            if result.success and result.duration > 0:
                exceeds_p95 = result.duration > p95_threshold
                exceeds_p99 = result.duration > p99_threshold
                
                result.exceeds_p95 = exceeds_p95
                result.exceeds_p99 = exceeds_p99
                
                if exceeds_p99:
                    alerts.append({
                        "type": "p99_exceeded",
                        "severity": "high",
                        "question": result.question,
                        "duration": result.duration,
                        "threshold": p99_threshold,
                        "intent": result.intent
                    })
                elif exceeds_p95:
                    alerts.append({
                        "type": "p95_exceeded",
                        "severity": "medium",
                        "question": result.question,
                        "duration": result.duration,
                        "threshold": p95_threshold,
                        "intent": result.intent
                    })
    else:
        response_time = {
            "min": 0.0,
            "max": 0.0,
            "avg": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0
        }
        alerts = []
    
    total = success_count + error_count
    success_rate = (success_count / total * 100) if total > 0 else 0.0
    
    summary = PerformanceSummary(
        total_tests=total,
        success_count=success_count,
        error_count=error_count,
        success_rate=round(success_rate, 2),
        response_time=response_time,
        intents=intents_count,
        results=results,
        alerts=alerts,
        timestamp=datetime.now().isoformat()
    )
    
    # حفظ النتائج في ملفات JSON و Markdown
    try:
        _save_performance_report(summary)
    except Exception as e:
        logger.error(f"خطأ في حفظ تقرير الأداء: {str(e)}")
    
    # إرسال تنبيهات للطلبات التي تتجاوز P95/P99
    if alerts:
        _log_alerts(alerts)
    
    return summary


def _save_performance_report(summary: PerformanceSummary):
    """حفظ تقرير الأداء في ملفات JSON و Markdown"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # حفظ JSON
    json_file = PERFORMANCE_REPORTS_DIR / f"performance_report_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"تم حفظ تقرير الأداء JSON: {json_file}")
    
    # حفظ Markdown
    md_file = PERFORMANCE_REPORTS_DIR / f"performance_report_{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(_generate_markdown_report(summary))
    logger.info(f"تم حفظ تقرير الأداء Markdown: {md_file}")


def _generate_markdown_report(summary: PerformanceSummary) -> str:
    """توليد تقرير Markdown من النتائج"""
    md = f"""# تقرير أداء البوت الذكي

**التاريخ والوقت:** {summary.timestamp}
**عدد الاختبارات:** {summary.total_tests}
**معدل النجاح:** {summary.success_rate}%

## 📊 إحصائيات الأداء

### أوقات الاستجابة (بالثواني)

- **الأدنى:** {summary.response_time['min']:.2f}s
- **الأقصى:** {summary.response_time['max']:.2f}s
- **المتوسط:** {summary.response_time['avg']:.2f}s
- **الوسيط (P50):** {summary.response_time['p50']:.2f}s
- **P95:** {summary.response_time['p95']:.2f}s
- **P99:** {summary.response_time['p99']:.2f}s

## 🎯 توزيع النوايا

"""
    for intent, count in summary.intents.items():
        md += f"- **{intent}:** {count}\n"
    
    md += "\n## ⚠️ التنبيهات\n\n"
    if summary.alerts:
        for alert in summary.alerts:
            md += f"### {alert['type'].upper()} - {alert['severity'].upper()}\n"
            md += f"- **السؤال:** {alert['question']}\n"
            md += f"- **وقت الاستجابة:** {alert['duration']:.2f}s\n"
            md += f"- **العتبة:** {alert['threshold']:.2f}s\n"
            md += f"- **النية:** {alert.get('intent', 'N/A')}\n\n"
    else:
        md += "لا توجد تنبيهات - جميع الطلبات ضمن الحدود المقبولة ✅\n\n"
    
    md += "## 📋 تفاصيل الاختبارات\n\n"
    md += "| السؤال | النية | وقت الاستجابة | نجح | DB Context | P95 | P99 |\n"
    md += "|---------|-------|----------------|------|------------|-----|-----|\n"
    
    for result in summary.results:
        db_status = "✅" if result.db_context_used else "❌"
        success_status = "✅" if result.success else "❌"
        p95_status = "⚠️" if result.exceeds_p95 else "✅"
        p99_status = "🚨" if result.exceeds_p99 else "✅"
        
        md += f"| {result.question} | {result.intent or 'N/A'} | {result.duration:.2f}s | {success_status} | {db_status} | {p95_status} | {p99_status} |\n"
    
    return md


def _log_alerts(alerts: List[Dict]):
    """تسجيل التنبيهات في الـ logs"""
    for alert in alerts:
        if alert["severity"] == "high":
            logger.warning(
                f"🚨 P99 EXCEEDED: '{alert['question']}' took {alert['duration']:.2f}s "
                f"(threshold: {alert['threshold']:.2f}s, intent: {alert.get('intent', 'N/A')})"
            )
        else:
            logger.info(
                f"⚠️ P95 EXCEEDED: '{alert['question']}' took {alert['duration']:.2f}s "
                f"(threshold: {alert['threshold']:.2f}s, intent: {alert.get('intent', 'N/A')})"
            )
