-- ============================================================
-- SQL Query واحد لعرض جميع البيانات من قاعدة البيانات
-- عيادات عادل كير
-- ============================================================

-- هذا Query يعرض ملخص شامل لجميع الجداول
SELECT 
    'appointments' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE status = 'pending') as "قيد الانتظار",
    COUNT(*) FILTER (WHERE status = 'confirmed') as "مؤكد",
    COUNT(*) FILTER (WHERE status = 'completed') as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM appointments
UNION ALL
SELECT 
    'patients' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM patients
UNION ALL
SELECT 
    'doctors' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM doctors
UNION ALL
SELECT 
    'invoices' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE payment_status = 'pending') as "قيد الانتظار",
    COUNT(*) FILTER (WHERE payment_status = 'paid') as "مدفوع",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM invoices
UNION ALL
SELECT 
    'conversations' as "الجدول",
    COUNT(*) as "عدد السجلات",
    0 as "قيد الانتظار",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM conversations
UNION ALL
SELECT 
    'services' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM services
UNION ALL
SELECT 
    'branches' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM branches
UNION ALL
SELECT 
    'offers' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM offers
UNION ALL
SELECT 
    'faqs' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM faqs
UNION ALL
SELECT 
    'treatments' as "الجدول",
    COUNT(*) as "عدد السجلات",
    0 as "قيد الانتظار",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM treatments
UNION ALL
SELECT 
    'employees' as "الجدول",
    COUNT(*) as "عدد السجلات",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل",
    MAX(created_at) as "آخر تحديث"
FROM employees
ORDER BY "عدد السجلات" DESC;

