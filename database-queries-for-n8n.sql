-- ============================================
-- استعلامات SQL لقاعدة بيانات عيادات عادل كير
-- للاستخدام في n8n أو أي أداة أخرى
-- ============================================

-- 1. معرفة جميع الجداول في قاعدة البيانات
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. معرفة عدد السجلات في كل جدول
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY tablename;

-- 3. معرفة هيكل جدول معين (مثال: patients)
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name = 'patients'
ORDER BY ordinal_position;

-- 4. معرفة جميع الأعمدة في جميع الجداول
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- ============================================
-- استعلامات للجداول الرئيسية
-- ============================================

-- 5. جدول الفروع (Branches)
SELECT * FROM branches 
WHERE is_active = true
ORDER BY created_at DESC
LIMIT 10;

-- 6. جدول الأطباء (Doctors)
SELECT 
    d.id,
    d.name,
    d.specialty,
    d.license_number,
    d.phone_number,
    d.email,
    b.name as branch_name,
    d.is_active,
    d.created_at
FROM doctors d
LEFT JOIN branches b ON d.branch_id = b.id
WHERE d.is_active = true
ORDER BY d.created_at DESC
LIMIT 10;

-- 7. جدول الخدمات (Services)
SELECT * FROM services 
WHERE is_active = true
ORDER BY name
LIMIT 10;

-- 8. جدول المرضى (Patients)
SELECT * FROM patients 
ORDER BY created_at DESC
LIMIT 10;

-- 9. جدول المواعيد (Appointments)
SELECT 
    a.id,
    a.datetime,
    a.status,
    a.appointment_type,
    p.full_name as patient_name,
    p.phone_number as patient_phone,
    d.name as doctor_name,
    b.name as branch_name,
    a.created_at
FROM appointments a
LEFT JOIN patients p ON a.patient_id = p.id
LEFT JOIN doctors d ON a.doctor_id = d.id
LEFT JOIN branches b ON a.branch_id = b.id
ORDER BY a.datetime DESC
LIMIT 10;

-- 10. جدول المحادثات (Conversations)
SELECT 
    id,
    user_id,
    channel,
    user_message,
    bot_reply,
    intent,
    created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 10;

-- 11. جدول الفواتير (Invoices)
SELECT 
    i.id,
    i.invoice_number,
    i.invoice_date,
    i.total_amount,
    i.payment_status,
    i.payment_method,
    p.full_name as patient_name,
    a.datetime as appointment_datetime,
    i.created_at
FROM invoices i
LEFT JOIN patients p ON i.patient_id = p.id
LEFT JOIN appointments a ON i.appointment_id = a.id
ORDER BY i.invoice_date DESC
LIMIT 10;

-- 12. جدول العلاجات (Treatments)
SELECT 
    t.id,
    t.treatment_date,
    t.description,
    t.diagnosis,
    p.full_name as patient_name,
    d.name as doctor_name,
    t.created_at
FROM treatments t
LEFT JOIN patients p ON t.patient_id = p.id
LEFT JOIN doctors d ON t.doctor_id = d.id
ORDER BY t.treatment_date DESC
LIMIT 10;

-- 13. جدول الموظفين (Employees)
SELECT 
    e.id,
    e.full_name,
    e.position,
    e.phone_number,
    e.email,
    b.name as branch_name,
    e.hire_date,
    e.created_at
FROM employees e
LEFT JOIN branches b ON e.branch_id = b.id
ORDER BY e.created_at DESC
LIMIT 10;

-- 14. جدول العروض (Offers)
SELECT * FROM offers 
WHERE is_active = true 
    AND (end_date IS NULL OR end_date >= CURRENT_DATE)
ORDER BY start_date DESC
LIMIT 10;

-- 15. جدول الأسئلة الشائعة (FAQs)
SELECT * FROM faqs 
WHERE is_active = true
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- إحصائيات سريعة
-- ============================================

-- 16. عدد السجلات في كل جدول
SELECT 
    'branches' as table_name, COUNT(*) as count FROM branches
UNION ALL
SELECT 'doctors', COUNT(*) FROM doctors
UNION ALL
SELECT 'services', COUNT(*) FROM services
UNION ALL
SELECT 'patients', COUNT(*) FROM patients
UNION ALL
SELECT 'appointments', COUNT(*) FROM appointments
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'treatments', COUNT(*) FROM treatments
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'offers', COUNT(*) FROM offers
UNION ALL
SELECT 'faqs', COUNT(*) FROM faqs
ORDER BY table_name;

-- 17. المواعيد القادمة (الـ 7 أيام القادمة)
SELECT 
    a.id,
    a.datetime,
    a.status,
    p.full_name as patient_name,
    p.phone_number as patient_phone,
    d.name as doctor_name,
    d.specialty,
    b.name as branch_name
FROM appointments a
LEFT JOIN patients p ON a.patient_id = p.id
LEFT JOIN doctors d ON a.doctor_id = d.id
LEFT JOIN branches b ON a.branch_id = b.id
WHERE a.datetime >= CURRENT_DATE
    AND a.datetime <= CURRENT_DATE + INTERVAL '7 days'
    AND a.status != 'cancelled'
ORDER BY a.datetime ASC;

-- 18. الفواتير غير المدفوعة
SELECT 
    i.id,
    i.invoice_number,
    i.invoice_date,
    i.total_amount,
    i.payment_status,
    p.full_name as patient_name,
    p.phone_number as patient_phone
FROM invoices i
LEFT JOIN patients p ON i.patient_id = p.id
WHERE i.payment_status != 'paid'
ORDER BY i.invoice_date DESC;

-- 19. الأطباء الأكثر حجزاً (آخر 30 يوم)
SELECT 
    d.name,
    d.specialty,
    COUNT(a.id) as appointment_count
FROM doctors d
LEFT JOIN appointments a ON d.id = a.doctor_id
    AND a.datetime >= CURRENT_DATE - INTERVAL '30 days'
WHERE d.is_active = true
GROUP BY d.id, d.name, d.specialty
ORDER BY appointment_count DESC
LIMIT 10;

-- 20. المحادثات حسب القناة (آخر 7 أيام)
SELECT 
    channel,
    COUNT(*) as conversation_count,
    COUNT(DISTINCT user_id) as unique_users
FROM conversations
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY channel
ORDER BY conversation_count DESC;

