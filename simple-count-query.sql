-- ============================================================
-- SELECT COUNT(*) لكل الجداول - بسيط جداً
-- ============================================================

SELECT 'appointments' as "الجدول", COUNT(*) as "العدد" FROM appointments
UNION ALL SELECT 'patients', COUNT(*) FROM patients
UNION ALL SELECT 'doctors', COUNT(*) FROM doctors
UNION ALL SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL SELECT 'services', COUNT(*) FROM services
UNION ALL SELECT 'branches', COUNT(*) FROM branches
UNION ALL SELECT 'offers', COUNT(*) FROM offers
UNION ALL SELECT 'faqs', COUNT(*) FROM faqs
UNION ALL SELECT 'treatments', COUNT(*) FROM treatments
UNION ALL SELECT 'employees', COUNT(*) FROM employees
ORDER BY "العدد" DESC;

