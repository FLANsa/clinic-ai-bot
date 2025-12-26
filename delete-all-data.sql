-- ============================================================
-- حذف جميع البيانات من قاعدة البيانات
-- ⚠️ تحذير: هذا سيحذف جميع البيانات!
-- ============================================================

-- تعطيل Foreign Key Constraints مؤقتاً
SET session_replication_role = 'replica';

-- حذف البيانات بترتيب صحيح (حذف الجداول التي تعتمد على غيرها أولاً)

-- 1. حذف البيانات من الجداول التي تعتمد على جداول أخرى
DELETE FROM treatments;
DELETE FROM invoices;
DELETE FROM appointments;
DELETE FROM conversations;

-- 2. حذف البيانات من الجداول الأساسية
DELETE FROM patients;
DELETE FROM employees;
DELETE FROM doctors;
DELETE FROM services;
DELETE FROM branches;
DELETE FROM offers;
DELETE FROM faqs;

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

