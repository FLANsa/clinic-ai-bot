# قائمة الجداول في قاعدة بيانات عيادات عادل كير

## الجداول الرئيسية

### 1. **branches** - الفروع
- `id` (UUID) - معرف الفرع
- `name` (String) - اسم الفرع
- `city` (String) - المدينة
- `address` (Text) - العنوان
- `location_url` (Text) - رابط الموقع على الخريطة
- `phone` (String) - رقم الهاتف
- `working_hours` (JSON) - ساعات العمل
- `is_active` (Boolean) - هل الفرع نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 2. **doctors** - الأطباء
- `id` (UUID) - معرف الطبيب
- `name` (String) - اسم الطبيب
- `specialty` (String) - تخصص الطبيب
- `license_number` (String) - رقم الترخيص
- `branch_id` (UUID) - معرف الفرع (Foreign Key → branches.id)
- `phone_number` (String) - رقم الهاتف
- `email` (String) - البريد الإلكتروني
- `bio` (Text) - نبذة عن الطبيب
- `working_hours` (JSON) - ساعات العمل
- `qualifications` (Text) - المؤهلات العلمية
- `experience_years` (String) - سنوات الخبرة
- `is_active` (Boolean) - هل الطبيب نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 3. **services** - الخدمات
- `id` (UUID) - معرف الخدمة
- `name` (String) - اسم الخدمة
- `description` (Text) - وصف الخدمة
- `base_price` (Float) - السعر الأساسي للخدمة
- `is_active` (Boolean) - هل الخدمة نشطة؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 4. **patients** - المرضى
- `id` (UUID) - معرف المريض
- `full_name` (String) - الاسم الكامل
- `date_of_birth` (Date) - تاريخ الميلاد
- `gender` (String) - الجنس (male, female)
- `address` (Text) - العنوان
- `phone_number` (String) - رقم الهاتف
- `email` (String) - البريد الإلكتروني
- `medical_history` (Text) - التاريخ الطبي
- `emergency_contact_name` (String) - اسم جهة الاتصال في الطوارئ
- `emergency_contact_phone` (String) - رقم جهة الاتصال في الطوارئ
- `notes` (Text) - ملاحظات إضافية
- `is_active` (Boolean) - هل المريض نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 5. **appointments** - المواعيد
- `id` (UUID) - معرف الموعد
- `patient_id` (UUID) - معرف المريض (Foreign Key → patients.id)
- `patient_name` (String) - اسم المريض (إذا لم يكن مسجلاً)
- `phone` (String) - رقم الهاتف
- `branch_id` (UUID) - معرف الفرع (Foreign Key → branches.id)
- `doctor_id` (UUID) - معرف الطبيب (Foreign Key → doctors.id)
- `service_id` (UUID) - معرف الخدمة (Foreign Key → services.id)
- `datetime` (DateTime) - تاريخ ووقت الموعد
- `channel` (String) - قناة الحجز (whatsapp, instagram, etc.)
- `status` (String) - حالة الموعد (pending, confirmed, completed, cancelled)
- `appointment_type` (String) - نوع الموعد (consultation, follow_up, emergency)
- `notes` (Text) - ملاحظات
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 6. **conversations** - المحادثات
- `id` (UUID) - معرف المحادثة
- `user_id` (String) - معرف المستخدم
- `channel` (String) - قناة الاتصال (whatsapp, instagram, google_maps, etc.)
- `user_message` (Text) - رسالة المستخدم
- `bot_reply` (Text) - رد البوت
- `intent` (String) - النية المكتشفة
- `db_context_used` (Boolean) - هل تم استخدام معلومات من قاعدة البيانات؟
- `unrecognized` (Boolean) - هل الرسالة لم تُفهم؟
- `needs_handoff` (Boolean) - هل تحتاج المحادثة لتحويل لموظف بشري؟
- `created_at` (DateTime) - تاريخ ووقت الإنشاء
- `updated_at` (DateTime) - تاريخ ووقت آخر تحديث

### 7. **treatments** - العلاجات
- `id` (UUID) - معرف العلاج
- `patient_id` (UUID) - معرف المريض (Foreign Key → patients.id)
- `doctor_id` (UUID) - معرف الطبيب (Foreign Key → doctors.id)
- `appointment_id` (UUID) - معرف الموعد (Foreign Key → appointments.id)
- `treatment_date` (Date) - تاريخ العلاج
- `description` (Text) - وصف العلاج
- `diagnosis` (Text) - التشخيص
- `prescription` (Text) - الوصفة الطبية
- `follow_up_required` (Boolean) - هل يحتاج متابعة؟
- `follow_up_date` (Date) - تاريخ المتابعة
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 8. **invoices** - الفواتير
- `id` (UUID) - معرف الفاتورة
- `invoice_number` (String) - رقم الفاتورة
- `patient_id` (UUID) - معرف المريض (Foreign Key → patients.id)
- `appointment_id` (UUID) - معرف الموعد (Foreign Key → appointments.id)
- `invoice_date` (Date) - تاريخ الفاتورة
- `sub_total` (Float) - المجموع الفرعي
- `discount_amount` (Float) - مبلغ الخصم
- `tax_amount` (Float) - مبلغ الضريبة
- `total_amount` (Float) - المبلغ الإجمالي
- `payment_status` (String) - حالة الدفع (pending, paid, partial, cancelled)
- `payment_method` (String) - طريقة الدفع (cash, card, online)
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 9. **employees** - الموظفين
- `id` (UUID) - معرف الموظف
- `full_name` (String) - الاسم الكامل
- `position` (String) - الوظيفة (receptionist, nurse, admin, etc.)
- `branch_id` (UUID) - معرف الفرع (Foreign Key → branches.id)
- `phone_number` (String) - رقم الهاتف
- `email` (String) - البريد الإلكتروني
- `hire_date` (Date) - تاريخ التوظيف
- `salary` (Float) - الراتب
- `notes` (Text) - ملاحظات
- `is_active` (Boolean) - هل الموظف نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 10. **offers** - العروض
- `id` (UUID) - معرف العرض
- `title` (String) - عنوان العرض
- `description` (Text) - وصف العرض
- `discount_type` (String) - نوع الخصم (percentage, fixed)
- `discount_value` (Float) - قيمة الخصم
- `related_service_id` (UUID) - معرف الخدمة المرتبطة (Foreign Key → services.id)
- `start_date` (Date) - تاريخ بداية العرض
- `end_date` (Date) - تاريخ نهاية العرض
- `is_active` (Boolean) - هل العرض نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 11. **faqs** - الأسئلة الشائعة
- `id` (UUID) - معرف السؤال
- `question` (Text) - السؤال
- `answer` (Text) - الإجابة
- `tags` (String) - العلامات (tags)
- `is_active` (Boolean) - هل السؤال نشط؟
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

## الجداول الإضافية

### 12. **document_sources** - مصادر المستندات
- `id` (UUID) - معرف المصدر
- `title` (String) - العنوان
- `source_type` (String) - نوع المصدر
- `tags` (String) - العلامات
- `language` (String) - اللغة
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

### 13. **document_chunks** - أجزاء المستندات
- `id` (UUID) - معرف الجزء
- `document_id` (UUID) - معرف المستند (Foreign Key → document_sources.id)
- `content` (Text) - المحتوى
- `chunk_index` (Integer) - فهرس الجزء
- `metadata` (JSON) - البيانات الوصفية
- `created_at` (DateTime) - تاريخ الإنشاء

### 14. **unanswered_questions** - الأسئلة غير المجابة
- `id` (UUID) - معرف السؤال
- `question` (Text) - السؤال
- `user_id` (String) - معرف المستخدم
- `channel` (String) - القناة
- `created_at` (DateTime) - تاريخ الإنشاء

### 15. **pending_handoffs** - التحويلات المعلقة
- `id` (UUID) - معرف التحويل
- `conversation_id` (UUID) - معرف المحادثة
- `user_id` (String) - معرف المستخدم
- `channel` (String) - القناة
- `reason` (Text) - سبب التحويل
- `status` (String) - الحالة
- `created_at` (DateTime) - تاريخ الإنشاء
- `updated_at` (DateTime) - تاريخ آخر تحديث

## ملخص الجداول

| رقم | اسم الجدول | الوصف |
|-----|-----------|-------|
| 1 | `branches` | الفروع |
| 2 | `doctors` | الأطباء |
| 3 | `services` | الخدمات |
| 4 | `patients` | المرضى |
| 5 | `appointments` | المواعيد |
| 6 | `conversations` | المحادثات |
| 7 | `treatments` | العلاجات |
| 8 | `invoices` | الفواتير |
| 9 | `employees` | الموظفين |
| 10 | `offers` | العروض |
| 11 | `faqs` | الأسئلة الشائعة |
| 12 | `document_sources` | مصادر المستندات |
| 13 | `document_chunks` | أجزاء المستندات |
| 14 | `unanswered_questions` | الأسئلة غير المجابة |
| 15 | `pending_handoffs` | التحويلات المعلقة |

## استعلام SQL لمعرفة الجداول

```sql
-- معرفة جميع الجداول
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- معرفة عدد السجلات في كل جدول
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY tablename;
```

