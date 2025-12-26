-- ============================================================
-- حذف جميع البيانات من قاعدة البيانات (آمن - مع TRUNCATE)
-- ⚠️ تحذير: هذا سيحذف جميع البيانات!
-- ============================================================

-- استخدام TRUNCATE (أسرع وأكثر أماناً)
-- TRUNCATE يحذف جميع البيانات ويعيد reset للـ sequences

-- تعطيل Foreign Key Constraints مؤقتاً
SET session_replication_role = 'replica';

-- حذف البيانات بترتيب صحيح
TRUNCATE TABLE treatments CASCADE;
TRUNCATE TABLE invoices CASCADE;
TRUNCATE TABLE appointments CASCADE;
TRUNCATE TABLE conversations CASCADE;
TRUNCATE TABLE patients CASCADE;
TRUNCATE employees CASCADE;
TRUNCATE TABLE doctors CASCADE;
TRUNCATE TABLE services CASCADE;
TRUNCATE TABLE branches CASCADE;
TRUNCATE TABLE offers CASCADE;
TRUNCATE TABLE faqs CASCADE;

-- إعادة تفعيل Foreign Key Constraints
SET session_replication_role = 'origin';

-- التحقق من أن جميع الجداول فارغة
SELECT 
    'appointments' as "الجدول", COUNT(*) as "عدد السجلات المتبقية" FROM appointments
UNION ALL SELECT 'patients', COUNT(*) FROM patients
UNION ALL SELECT 'doctors', COUNT(*) FROM doctors
UNION ALL SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL SELECT 'services', COUNT(*) FROM services
UNION ALL SELECT 'branches', COUNT(*) FROM branches
UNION ALL SELECT 'offers', COUNT(*) FROM offers
UNION ALL SELECT 'faqs', COUNT(*) FROM faqs
UNION ALL SELECT 'treatments', COUNT(*) FROM treatments
UNION ALL SELECT 'employees', COUNT(*) FROM employees;

