# اختبارات الأداء

## المتطلبات

- `GROQ_API_KEY` يجب أن يكون معرّف في environment variables
- قاعدة بيانات SQLite للاختبارات (تتم إنشاؤها تلقائياً)

## تشغيل الاختبارات

```bash
# جميع اختبارات الأداء
pytest tests/performance/ -v -s

# اختبار محدد
pytest tests/performance/test_performance.py::test_api_endpoint_performance -v -s

# مع تفاصيل أكثر
pytest tests/performance/ -v -s --tb=short
```

## الاختبارات المتاحة

1. **test_single_message_performance**: اختبار أداء رسالة واحدة
2. **test_api_endpoint_performance**: اختبار أداء API endpoint (5 أسئلة)
3. **test_concurrent_requests_performance**: اختبار الطلبات المتزامنة (5 طلبات)
4. **test_response_time_percentiles**: تحليل توزيع أوقات الاستجابة (20 سؤال)
5. **test_load_performance**: اختبار تحت حمل (10 طلبات متتالية)

## النتائج المتوقعة

- متوسط وقت الاستجابة: < 5 ثواني
- P95: < 10 ثواني
- P99: < 15 ثواني
- معدل النجاح: > 90%

## ملاحظات

- الاختبارات تستخدم SQLite محلي (أسرع)
- إذا لم يكن `GROQ_API_KEY` متوفر، سيتم تخطي الاختبارات
- النتائج تظهر في console مع تفاصيل كاملة

