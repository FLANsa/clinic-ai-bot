#!/usr/bin/env python3
"""
اختبار شامل للبوت - يختبر Intent Detection و Context Memory و Quality Evaluation
"""
import requests
import json
import time
from typing import List, Dict, Any

API_BASE = "http://localhost:8000"
TEST_USER_ID = "test_user_comprehensive"

# سيناريوهات الاختبار
TEST_SCENARIOS = [
    {
        "name": "سؤال مباشر عن خدمة",
        "messages": [
            "وش الخدمات المتوفرة عندكم؟"
        ],
        "expected_intent": "service_info",
        "description": "اختبار Intent Detection للأسئلة المباشرة"
    },
    {
        "name": "سؤال غير مباشر عن السعر (بدون سياق)",
        "messages": [
            "كم يكلف؟"
        ],
        "expected_intent": "price",
        "description": "اختبار Intent Detection للأسئلة غير المباشرة بدون سياق"
    },
    {
        "name": "سؤال غير مباشر عن السعر (مع سياق)",
        "messages": [
            "تبييض الأسنان",
            "كم يكلف؟"
        ],
        "expected_intent": "price",
        "description": "اختبار Context Memory - يجب أن يتذكر الخدمة المذكورة"
    },
    {
        "name": "سؤال عن فرع",
        "messages": [
            "وين أقرب فرع؟"
        ],
        "expected_intent": "branch_info",
        "description": "اختبار Intent Detection لأسئلة الفروع"
    },
    {
        "name": "سؤال عن طبيب",
        "messages": [
            "وش الأطباء المتوفرين؟"
        ],
        "expected_intent": "doctor_info",
        "description": "اختبار Intent Detection لأسئلة الأطباء"
    },
    {
        "name": "طلب حجز",
        "messages": [
            "أبي أحجز موعد"
        ],
        "expected_intent": "booking",
        "description": "اختبار Intent Detection لطلبات الحجز"
    },
    {
        "name": "سؤال متعدد الجوانب",
        "messages": [
            "تبييض الأسنان",
            "كم يكلف؟",
            "وين أقرب فرع؟",
            "وش أفضل وقت للحجز؟"
        ],
        "expected_intent": "booking",
        "description": "اختبار Context Memory مع أسئلة متعددة"
    }
]


def test_chat(message: str, user_id: str = TEST_USER_ID, channel: str = "whatsapp") -> Dict[str, Any]:
    """اختبار رسالة واحدة"""
    url = f"{API_BASE}/test/chat"
    payload = {
        "message": message,
        "user_id": user_id,
        "channel": channel
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """تشغيل سيناريو اختبار كامل"""
    print(f"\n{'='*60}")
    print(f"📋 السيناريو: {scenario['name']}")
    print(f"📝 الوصف: {scenario['description']}")
    print(f"{'='*60}")
    
    results = []
    conversation_context = []
    
    for i, message in enumerate(scenario['messages'], 1):
        print(f"\n💬 الرسالة {i}: {message}")
        
        # انتظار قليل بين الرسائل
        if i > 1:
            time.sleep(1)
        
        result = test_chat(message, TEST_USER_ID)
        
        if "error" in result:
            print(f"❌ خطأ: {result['error']}")
            results.append({
                "message": message,
                "error": result['error']
            })
            continue
        
        reply = result.get("reply", "")
        intent = result.get("intent", None)
        satisfaction_score = result.get("satisfaction_score", None)
        rag_used = result.get("rag_used", False)
        db_context_used = result.get("db_context_used", False)
        unrecognized = result.get("unrecognized", False)
        needs_handoff = result.get("needs_handoff", False)
        
        print(f"🤖 الرد: {reply[:100]}..." if len(reply) > 100 else f"🤖 الرد: {reply}")
        print(f"🎯 النية المكتشفة: {intent}")
        print(f"📊 تقييم الجودة: {satisfaction_score:.2f}" if satisfaction_score else "📊 تقييم الجودة: غير متوفر")
        print(f"🔍 RAG مستخدم: {'✅' if rag_used else '❌'}")
        print(f"💾 DB Context مستخدم: {'✅' if db_context_used else '❌'}")
        print(f"⚠️ غير معروف: {'✅' if unrecognized else '❌'}")
        print(f"🔄 يحتاج تحويل: {'✅' if needs_handoff else '❌'}")
        
        # التحقق من النية المتوقعة
        if scenario.get('expected_intent'):
            if intent == scenario['expected_intent']:
                print(f"✅ النية صحيحة: {intent}")
            else:
                print(f"⚠️ النية المتوقعة: {scenario['expected_intent']}, المكتشفة: {intent}")
        
        results.append({
            "message": message,
            "reply": reply,
            "intent": intent,
            "satisfaction_score": satisfaction_score,
            "rag_used": rag_used,
            "db_context_used": db_context_used,
            "unrecognized": unrecognized,
            "needs_handoff": needs_handoff
        })
        
        conversation_context.append({"role": "user", "content": message})
        conversation_context.append({"role": "assistant", "content": reply})
    
    return {
        "scenario": scenario['name'],
        "results": results,
        "success": len([r for r in results if "error" not in r]) == len(scenario['messages'])
    }


def test_health_check() -> bool:
    """اختبار health check"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health Check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check error: {str(e)}")
        return False


def main():
    """الدالة الرئيسية"""
    print("🚀 بدء الاختبار الشامل للبوت")
    print("="*60)
    
    # 1. اختبار Health Check
    print("\n1️⃣ اختبار Health Check...")
    health_ok = test_health_check()
    if not health_ok:
        print("❌ الباك إند غير متاح. تأكد من تشغيله على http://localhost:8000")
        return
    
    # 2. تشغيل جميع السيناريوهات
    print("\n2️⃣ تشغيل سيناريوهات الاختبار...")
    all_results = []
    
    for scenario in TEST_SCENARIOS:
        result = run_scenario(scenario)
        all_results.append(result)
        time.sleep(2)  # انتظار بين السيناريوهات
        
        # 3. ملخص النتائج
        print("\n" + "="*60)
        print("📊 ملخص النتائج")
        print("="*60)
        
        total_scenarios = len(all_results)
        successful_scenarios = len([r for r in all_results if r['success']])
        
        print(f"\n✅ السيناريوهات الناجحة: {successful_scenarios}/{total_scenarios}")
        
        for result in all_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['scenario']}")
            
            # عرض تفاصيل النوايا المكتشفة
            for i, r in enumerate(result['results'], 1):
                if "error" not in r:
                    intent_status = "✅" if r.get('intent') else "⚠️"
                    print(f"   {intent_status} رسالة {i}: intent={r.get('intent', 'None')}, quality={r.get('satisfaction_score', 'N/A')}")
        
        # 4. إحصائيات إضافية
        print("\n" + "="*60)
        print("📈 إحصائيات")
        print("="*60)
        
        all_intents = [r.get('intent') for result in all_results for r in result['results'] if "error" not in r and r.get('intent')]
        all_quality_scores = [r.get('satisfaction_score') for result in all_results for r in result['results'] if "error" not in r and r.get('satisfaction_score')]
        
        print(f"\n🎯 عدد النوايا المكتشفة: {len(all_intents)}")
        if all_intents:
            intent_counts = {}
            for intent in all_intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            print("   توزيع النوايا:")
            for intent, count in intent_counts.items():
                print(f"   - {intent}: {count}")
        
        print(f"\n📊 عدد التقييمات: {len(all_quality_scores)}")
        if all_quality_scores:
            avg_quality = sum(all_quality_scores) / len(all_quality_scores)
            print(f"   متوسط الجودة: {avg_quality:.2f}")
            print(f"   أعلى جودة: {max(all_quality_scores):.2f}")
            print(f"   أقل جودة: {min(all_quality_scores):.2f}")
        
        print("\n" + "="*60)
        print("✅ انتهى الاختبار الشامل")
        print("="*60)


if __name__ == "__main__":
    main()

