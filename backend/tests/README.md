# دليل الاختبارات الشاملة

هذا الدليل يشرح كيفية تشغيل واختبار جميع وظائف وأداء النظام.

## 📋 أنواع الاختبارات

### 1. اختبارات الوحدة (Unit Tests)
- **الموقع:** `tests/unit/`
- **الوصف:** اختبار المكونات الفردية (intents, agent logic)
- **الملفات:**
  - `test_intents.py` - اختبارات كشف النوايا
  - `test_agent.py` - اختبارات منطق الوكيل

### 2. اختبارات التكامل (Integration Tests)
- **الموقع:** `tests/integration/`
- **الوصف:** اختبار تفاعل المكونات معاً
- **الملفات:**
  - `test_api.py` - اختبارات API endpoints الأساسية
  - `test_comprehensive_functional.py` - **اختبارات وظيفية شاملة لجميع الـ endpoints**

### 3. اختبارات الأداء (Performance Tests)
- **الموقع:** `tests/performance/`
- **الوصف:** اختبار أداء النظام (response time, load, concurrency, memory)
- **الملفات:**
  - `test_performance.py` - اختبارات أداء أساسية
  - `test_comprehensive_performance.py` - **اختبارات أداء شاملة**

## 🚀 تشغيل الاختبارات

### تشغيل جميع الاختبارات (موصى به)

```bash
cd backend
python scripts/run_all_tests.py
```

هذا السكريبت سيقوم بتشغيل:
1. ✅ Unit Tests
2. ✅ Integration Tests
3. ✅ Comprehensive Functional Tests
4. ✅ Performance Tests

### تشغيل نوع محدد من الاختبارات

#### Unit Tests فقط:
```bash
cd backend
pytest tests/unit/ -v
```

#### Integration Tests فقط:
```bash
cd backend
pytest tests/integration/ -v
```

#### Comprehensive Functional Tests:
```bash
cd backend
pytest tests/integration/test_comprehensive_functional.py -v
```

#### Performance Tests:
```bash
cd backend
pytest tests/performance/ -v -s
```

> **ملاحظة:** `-s` لعرض output الـ print statements (مثل أوقات الاستجابة)

## 📊 ما تغطيه الاختبارات

### اختبارات وظيفية شاملة (`test_comprehensive_functional.py`)

#### ✅ Health & Root Endpoints
- Root endpoint
- Health check endpoint

#### ✅ Admin Endpoints
- **Branches:** List, Create, Get by ID
- **Doctors:** List, Create
- **Services:** List, Create
- **FAQ:** List, Create
- **Offers:** List, Create
- **Appointments:** List, Create
- **Analytics:** Get summary

#### ✅ Test Endpoints
- Test chat endpoint

#### ✅ Webhooks
- WhatsApp webhook verification
- WhatsApp webhook POST

#### ✅ Export
- Export conversations to CSV

#### ✅ Reports
- Daily reports

### اختبارات أداء شاملة (`test_comprehensive_performance.py`)

#### ⏱️ Response Time Tests
- Single message response time (< 10s)
- Multiple messages response time (avg < 8s, max < 15s)

#### 🔄 Concurrency Tests
- Concurrent requests handling
- Parallel processing efficiency

#### 📈 Load Tests
- 10 requests load test (< 60s total)
- 20 requests load test (< 120s total, < 10% error rate)

#### 💾 Memory Usage Tests
- Single request memory usage (< 50MB increase)
- Multiple requests memory usage (< 100MB increase for 5 requests)

#### 🌐 API Endpoints Performance
- Root endpoint performance (< 100ms)
- Health check performance (< 100ms)

## 📝 متطلبات التشغيل

تأكد من تثبيت جميع الـ dependencies:

```bash
cd backend
pip install -r requirements.txt
```

**Dependencies إضافية للاختبارات:**
- `psutil` - لقياس استخدام الذاكرة
- `numpy` - للحسابات الإحصائية

## 🔧 إعدادات الاختبارات

### Test Database
- الاختبارات تستخدم SQLite in-memory database
- لا تؤثر على قاعدة البيانات الرئيسية
- يتم تنظيف البيانات بعد كل اختبار

### API Key
- للاختبارات التي تحتاج authentication، يتم استخدام `test_api_key_123`
- يمكن تغييرها في `conftest.py`

## 📊 تفسير النتائج

### Response Time Metrics
- **P50 (Median):** الوقت المتوسط - 50% من الطلبات أسرع منه
- **P95:** 95% من الطلبات أسرع منه
- **P99:** 99% من الطلبات أسرع منه

### Memory Usage
- يتم قياس استخدام الذاكرة قبل وبعد كل اختبار
- الزيادة في الذاكرة يجب أن تكون معقولة

### Error Rate
- معدل الأخطاء يجب أن يكون أقل من 10% في load tests

## ⚠️ ملاحظات مهمة

1. **LLM API:** بعض الاختبارات تحتاج `GROQ_API_KEY` في environment variables
2. **Database:** الاختبارات تستخدم SQLite - لا تحتاج PostgreSQL للاختبارات
3. **Timeouts:** بعض الاختبارات قد تستغرق وقتاً طويلاً (خاصة performance tests)
4. **Resources:** Performance tests قد تستهلك موارد كبيرة - تأكد من توفر RAM كافي

## 🐛 Troubleshooting

### خطأ: "Module not found"
```bash
# تأكد من تثبيت جميع dependencies
pip install -r requirements.txt
```

### خطأ: "API key not found"
```bash
# قم بتعيين API key في environment
export API_KEY="test_api_key_123"
```

### خطأ: "Database connection failed"
- الاختبارات تستخدم SQLite - لا تحتاج اتصال خارجي
- تأكد من أن SQLite مثبت في النظام

## 📈 تحسين الأداء

إذا فشلت performance tests:

1. **تحقق من LLM API:** قد يكون هناك rate limiting
2. **تحقق من Memory:** قد تحتاج إلى زيادة RAM
3. **تحقق من Network:** قد يكون هناك تأخير في الشبكة
4. **راجع Logs:** تحقق من logs للأخطاء

## 🔄 CI/CD Integration

يمكن استخدام هذه الاختبارات في CI/CD pipelines:

```yaml
# مثال GitHub Actions
- name: Run Tests
  run: |
    cd backend
    python scripts/run_all_tests.py
```

---

**تم إنشاء الاختبارات بواسطة:** AI Assistant  
**آخر تحديث:** 2024

