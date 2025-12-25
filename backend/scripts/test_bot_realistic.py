"""
اختبار شامل للبوت - سيناريوهات واقعية للعملاء
محاكاة محادثات حقيقية لعملاء داخلين على العيادة
"""
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.llm_client import LLMClient
from app.core.agent import ChatAgent
from app.core.models import ConversationInput


class Colors:
    """ألوان للطباعة"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# السيناريوهات المختلفة
SCENARIOS = [
    {
        "name": "🩺 سيناريو 1: عميل جديد يسأل عن الأطباء",
        "channel": "whatsapp",
        "user_id": "user_doctor_inquiry",
        "messages": [
            "السلام عليكم",
            "عندكم أطباء أسنان؟",
            "وين الدكتور أحمد؟",
            "وش تخصصه؟"
        ],
        "expected_keywords": ["دكتور", "أسنان", "أحمد", "تخصص"]
    },
    {
        "name": "💰 سيناريو 2: عميل يسأل عن الأسعار",
        "channel": "whatsapp",
        "user_id": "user_price_inquiry",
        "messages": [
            "مرحبا",
            "كم يكلف تبييض الأسنان؟",
            "وش سعر تنظيف الأسنان؟",
            "في عروض خاصة؟"
        ],
        "expected_keywords": ["تكلف", "سعر", "تبييض", "تنظيف", "عروض"]
    },
    {
        "name": "📍 سيناريو 3: عميل يسأل عن الفروع",
        "channel": "instagram",
        "user_id": "user_branch_inquiry",
        "messages": [
            "وين فروعكم؟",
            "عندكم فرع في الرياض؟",
            "وش ساعات العمل؟",
            "وش رقم التواصل؟"
        ],
        "expected_keywords": ["فرع", "الرياض", "ساعات", "رقم"]
    },
    {
        "name": "📅 سيناريو 4: عميل يريد الحجز",
        "channel": "whatsapp",
        "user_id": "user_booking",
        "messages": [
            "أهلاً",
            "أبي أحجز موعد",
            "للتنظيف",
            "في فرع الرياض",
            "ممكن غداً؟"
        ],
        "expected_keywords": ["حجز", "موعد", "تنظيف", "الرياض"]
    },
    {
        "name": "💬 سيناريو 5: محادثة متعددة الجوانب",
        "channel": "whatsapp",
        "user_id": "user_multiple_inquiries",
        "messages": [
            "السلام عليكم",
            "وش الخدمات اللي عندكم؟",
            "كم يكلف التقويم؟",
            "وين أقرب فرع لي؟",
            "وش أفضل وقت للحجز؟"
        ],
        "expected_keywords": ["خدمات", "تقويم", "فرع", "حجز"]
    },
    {
        "name": "❓ سيناريو 6: أسئلة عامة",
        "channel": "google_maps",
        "user_id": "user_general_questions",
        "messages": [
            "مرحبا",
            "وش هو تبييض الأسنان؟",
            "كم تستغرق العملية؟",
            "هل يحتاج تخدير؟"
        ],
        "expected_keywords": ["تبييض", "عملية", "تخدير"]
    },
    {
        "name": "🔍 سيناريو 7: عميل يسأل عن تفاصيل خدمة محددة",
        "channel": "whatsapp",
        "user_id": "user_service_details",
        "messages": [
            "أبي أعرف عن تقويم الأسنان",
            "كم مدة العلاج؟",
            "وش أنواع التقويم المتاحة؟",
            "كم يكلف؟"
        ],
        "expected_keywords": ["تقويم", "مدة", "أنواع", "تكلف"]
    },
    {
        "name": "🎁 سيناريو 8: عميل يسأل عن العروض",
        "channel": "instagram",
        "user_id": "user_offers",
        "messages": [
            "مرحبا",
            "عندكم عروض؟",
            "وش العروض المتاحة؟",
            "وش الخصم على تبييض الأسنان؟"
        ],
        "expected_keywords": ["عروض", "خصم", "تبييض"]
    },
    {
        "name": "🔄 سيناريو 9: محادثة طويلة مع تتبع السياق",
        "channel": "whatsapp",
        "user_id": "user_context_test",
        "messages": [
            "السلام عليكم",
            "عندكم أطباء؟",
            "وش أسمائهم؟",
            "أبي أحجز مع الدكتور أحمد",
            "لخدمة تنظيف الأسنان",
            "بكم؟",
            "وين أقرب فرع؟"
        ],
        "expected_keywords": ["أطباء", "أحمد", "حجز", "تنظيف", "فرع"]
    },
    {
        "name": "🤔 سيناريو 10: أسئلة غير واضحة",
        "channel": "tiktok",
        "user_id": "user_unclear_questions",
        "messages": [
            "مرحبا",
            "وش تسوون؟",
            "أبي شي",
            "وينكم؟"
        ],
        "expected_keywords": []
    }
]


async def test_single_message(
    agent: ChatAgent,
    message: str,
    user_id: str,
    channel: str,
    message_number: int
) -> Dict[str, Any]:
    """اختبار رسالة واحدة"""
    try:
        conv_input = ConversationInput(
            channel=channel,
            user_id=user_id,
            message=message,
            locale="ar-SA"
        )
        
        output = await agent.handle_message(conv_input)
        
        return {
            "success": True,
            "message": message,
            "reply": output.reply_text,
            "intent": output.intent,
            "db_context_used": output.db_context_used,
            "needs_handoff": output.needs_handoff,
            "unrecognized": output.unrecognized
        }
    except Exception as e:
        return {
            "success": False,
            "message": message,
            "error": str(e),
            "reply": None
        }


async def run_scenario(scenario: Dict[str, Any], agent: ChatAgent) -> Dict[str, Any]:
    """تشغيل سيناريو كامل"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{scenario['name']}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    results = []
    total_messages = len(scenario['messages'])
    
    for idx, message in enumerate(scenario['messages'], 1):
        print(f"{Colors.OKCYAN}[{idx}/{total_messages}]{Colors.ENDC} {Colors.BOLD}المستخدم:{Colors.ENDC} {message}")
        
        result = await test_single_message(
            agent,
            message,
            scenario['user_id'],
            scenario['channel'],
            idx
        )
        
        if result['success']:
            print(f"{Colors.OKGREEN}[البوت]{Colors.ENDC} {result['reply'][:200]}...")
            print(f"{Colors.OKBLUE}  └─ Intent: {result['intent']} | DB Context: {result['db_context_used']} | Handoff: {result['needs_handoff']}{Colors.ENDC}")
            
            # التحقق من وجود الكلمات المتوقعة في الرد
            if scenario.get('expected_keywords'):
                found_keywords = [kw for kw in scenario['expected_keywords'] if kw.lower() in message.lower() or kw.lower() in result['reply'].lower()]
                if found_keywords:
                    print(f"{Colors.OKGREEN}  └─ ✅ وجد كلمات مفتاحية: {', '.join(found_keywords)}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}[خطأ]{Colors.ENDC} {result['error']}")
        
        results.append(result)
        print()
        
        # انتظار قصير بين الرسائل لمحاكاة المحادثة الحقيقية
        await asyncio.sleep(0.5)
    
    # تحليل النتائج
    success_count = sum(1 for r in results if r['success'])
    db_context_used_count = sum(1 for r in results if r.get('db_context_used', False))
    intents = [r['intent'] for r in results if r.get('intent')]
    
    return {
        "scenario_name": scenario['name'],
        "total_messages": total_messages,
        "success_count": success_count,
        "db_context_used_count": db_context_used_count,
        "unique_intents": list(set(intents)),
        "results": results
    }


async def main():
    """الدالة الرئيسية"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🧪 اختبار شامل للبوت - سيناريوهات واقعية{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    print(f"{Colors.OKCYAN}📝 عدد السيناريوهات: {len(SCENARIOS)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}⏰ وقت البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")
    
    # إعداد Agent
    db = SessionLocal()
    try:
        llm_client = LLMClient()
        agent = ChatAgent(llm_client=llm_client, db_session=db)
        print(f"{Colors.OKGREEN}✅ تم تهيئة ChatAgent بنجاح{Colors.ENDC}\n")
        
        # تشغيل جميع السيناريوهات
        all_results = []
        for scenario in SCENARIOS:
            try:
                result = await run_scenario(scenario, agent)
                all_results.append(result)
            except Exception as e:
                print(f"{Colors.FAIL}❌ خطأ في السيناريو {scenario['name']}: {str(e)}{Colors.ENDC}\n")
                all_results.append({
                    "scenario_name": scenario['name'],
                    "error": str(e)
                })
        
        # ملخص النتائج
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 ملخص النتائج{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        total_scenarios = len(all_results)
        successful_scenarios = sum(1 for r in all_results if not r.get('error'))
        total_messages = sum(r.get('total_messages', 0) for r in all_results)
        total_success = sum(r.get('success_count', 0) for r in all_results)
        total_db_context = sum(r.get('db_context_used_count', 0) for r in all_results)
        
        print(f"{Colors.OKCYAN}📋 السيناريوهات:{Colors.ENDC}")
        print(f"  - الإجمالي: {total_scenarios}")
        print(f"  - نجحت: {successful_scenarios}")
        print(f"  - فشلت: {total_scenarios - successful_scenarios}")
        
        print(f"\n{Colors.OKCYAN}💬 الرسائل:{Colors.ENDC}")
        print(f"  - الإجمالي: {total_messages}")
        print(f"  - نجحت: {total_success}")
        print(f"  - فشلت: {total_messages - total_success}")
        
        print(f"\n{Colors.OKCYAN}🗄️  استخدام قاعدة البيانات:{Colors.ENDC}")
        print(f"  - عدد الرسائل التي استخدمت DB: {total_db_context}")
        print(f"  - النسبة: {(total_db_context / total_messages * 100) if total_messages > 0 else 0:.1f}%")
        
        # تفاصيل كل سيناريو
        print(f"\n{Colors.HEADER}{Colors.BOLD}📝 تفاصيل السيناريوهات:{Colors.ENDC}\n")
        for result in all_results:
            if result.get('error'):
                print(f"{Colors.FAIL}❌ {result['scenario_name']}: {result['error']}{Colors.ENDC}")
            else:
                status_icon = "✅" if result['success_count'] == result['total_messages'] else "⚠️"
                print(f"{status_icon} {result['scenario_name']}")
                print(f"   - الرسائل: {result['success_count']}/{result['total_messages']} نجحت")
                print(f"   - استخدام DB: {result['db_context_used_count']}/{result['total_messages']}")
                print(f"   - Intents: {', '.join(result['unique_intents']) if result['unique_intents'] else 'لا يوجد'}")
            print()
        
        print(f"{Colors.OKGREEN}✅ تم الانتهاء من جميع الاختبارات!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}⏰ وقت الانتهاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ خطأ فادح: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

