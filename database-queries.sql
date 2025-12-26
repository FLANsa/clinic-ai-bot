-- ============================================================
-- SQL Queries لعرض جميع البيانات من قاعدة البيانات
-- عيادات عادل كير
-- ============================================================

-- ==================== الإحصائيات السريعة ====================
SELECT 
    'المواعيد' as "النوع",
    COUNT(*) as "الإجمالي",
    COUNT(*) FILTER (WHERE status = 'pending') as "قيد الانتظار",
    COUNT(*) FILTER (WHERE status = 'confirmed') as "مؤكد",
    COUNT(*) FILTER (WHERE status = 'completed') as "مكتمل"
FROM appointments
UNION ALL
SELECT 
    'المرضى' as "النوع",
    COUNT(*) as "الإجمالي",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل"
FROM patients
UNION ALL
SELECT 
    'الأطباء' as "النوع",
    COUNT(*) as "الإجمالي",
    COUNT(*) FILTER (WHERE is_active = true) as "نشط",
    0 as "مؤكد",
    0 as "مكتمل"
FROM doctors
UNION ALL
SELECT 
    'الفواتير' as "النوع",
    COUNT(*) as "الإجمالي",
    COUNT(*) FILTER (WHERE payment_status = 'pending') as "قيد الانتظار",
    COUNT(*) FILTER (WHERE payment_status = 'paid') as "مدفوع",
    0 as "مكتمل"
FROM invoices;

-- ==================== المواعيد ====================
SELECT 
    id,
    patient_name as "اسم المريض",
    phone as "الهاتف",
    datetime as "التاريخ والوقت",
    status as "الحالة",
    channel as "القناة",
    appointment_type as "نوع الموعد",
    notes as "ملاحظات",
    created_at as "تاريخ الإنشاء"
FROM appointments
ORDER BY datetime DESC
LIMIT 100;

-- ==================== المرضى ====================
SELECT 
    id,
    full_name as "الاسم الكامل",
    phone_number as "رقم الهاتف",
    email as "البريد الإلكتروني",
    date_of_birth as "تاريخ الميلاد",
    gender as "الجنس",
    address as "العنوان",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM patients
ORDER BY created_at DESC
LIMIT 100;

-- ==================== الأطباء ====================
SELECT 
    id,
    name as "الاسم",
    specialty as "التخصص",
    license_number as "رقم الترخيص",
    phone_number as "رقم الهاتف",
    email as "البريد الإلكتروني",
    qualifications as "المؤهلات",
    experience_years as "سنوات الخبرة",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM doctors
ORDER BY name
LIMIT 100;

-- ==================== الفواتير ====================
SELECT 
    id,
    invoice_number as "رقم الفاتورة",
    invoice_date as "تاريخ الفاتورة",
    sub_total as "المبلغ قبل الخصم",
    discount_amount as "مبلغ الخصم",
    tax_amount as "مبلغ الضريبة",
    total_amount as "المبلغ الإجمالي",
    payment_status as "حالة الدفع",
    payment_method as "طريقة الدفع",
    notes as "ملاحظات",
    created_at as "تاريخ الإنشاء"
FROM invoices
ORDER BY invoice_date DESC
LIMIT 100;

-- ==================== المحادثات ====================
SELECT 
    id,
    user_id as "معرف المستخدم",
    channel as "القناة",
    LEFT(user_message, 100) as "الرسالة (100 حرف)",
    LEFT(bot_reply, 100) as "الرد (100 حرف)",
    intent as "النية",
    db_context_used as "استخدم سياق قاعدة البيانات",
    unrecognized as "غير معروف",
    needs_handoff as "يحتاج تحويل",
    created_at as "تاريخ الإنشاء"
FROM conversations
ORDER BY created_at DESC
LIMIT 100;

-- ==================== الخدمات ====================
SELECT 
    id,
    name as "الاسم",
    base_price as "السعر الأساسي",
    LEFT(description, 100) as "الوصف (100 حرف)",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM services
ORDER BY name
LIMIT 100;

-- ==================== الفروع ====================
SELECT 
    id,
    name as "الاسم",
    city as "المدينة",
    address as "العنوان",
    phone as "الهاتف",
    working_hours as "ساعات العمل",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM branches
ORDER BY name
LIMIT 100;

-- ==================== العروض ====================
SELECT 
    id,
    title as "العنوان",
    description as "الوصف",
    discount_type as "نوع الخصم",
    discount_value as "قيمة الخصم",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM offers
ORDER BY created_at DESC
LIMIT 100;

-- ==================== الأسئلة الشائعة ====================
SELECT 
    id,
    question as "السؤال",
    LEFT(answer, 100) as "الجواب (100 حرف)",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM faqs
ORDER BY created_at DESC
LIMIT 100;

-- ==================== العلاجات ====================
SELECT 
    id,
    treatment_date as "تاريخ العلاج",
    LEFT(description, 100) as "الوصف (100 حرف)",
    LEFT(diagnosis, 100) as "التشخيص (100 حرف)",
    follow_up_required as "يتطلب متابعة",
    follow_up_date as "تاريخ المتابعة",
    created_at as "تاريخ الإنشاء"
FROM treatments
ORDER BY treatment_date DESC
LIMIT 100;

-- ==================== الموظفين ====================
SELECT 
    id,
    full_name as "الاسم الكامل",
    position as "الوظيفة",
    phone_number as "رقم الهاتف",
    email as "البريد الإلكتروني",
    hire_date as "تاريخ التوظيف",
    is_active as "نشط",
    created_at as "تاريخ الإنشاء"
FROM employees
ORDER BY created_at DESC
LIMIT 100;

-- ==================== عرض كل شيء في جدول واحد (ملخص) ====================
SELECT 
    'appointments' as "الجدول",
    COUNT(*) as "عدد السجلات",
    MAX(created_at) as "آخر تحديث"
FROM appointments
UNION ALL
SELECT 'patients', COUNT(*), MAX(created_at) FROM patients
UNION ALL
SELECT 'doctors', COUNT(*), MAX(created_at) FROM doctors
UNION ALL
SELECT 'invoices', COUNT(*), MAX(created_at) FROM invoices
UNION ALL
SELECT 'conversations', COUNT(*), MAX(created_at) FROM conversations
UNION ALL
SELECT 'services', COUNT(*), MAX(created_at) FROM services
UNION ALL
SELECT 'branches', COUNT(*), MAX(created_at) FROM branches
UNION ALL
SELECT 'offers', COUNT(*), MAX(created_at) FROM offers
UNION ALL
SELECT 'faqs', COUNT(*), MAX(created_at) FROM faqs
UNION ALL
SELECT 'treatments', COUNT(*), MAX(created_at) FROM treatments
UNION ALL
SELECT 'employees', COUNT(*), MAX(created_at) FROM employees
ORDER BY "عدد السجلات" DESC;

-- ==================== المواعيد مع تفاصيل المريض والطبيب ====================
SELECT 
    a.id,
    a.patient_name as "اسم المريض",
    a.phone as "الهاتف",
    a.datetime as "التاريخ والوقت",
    a.status as "الحالة",
    d.name as "اسم الطبيب",
    d.specialty as "تخصص الطبيب",
    s.name as "الخدمة",
    b.name as "الفرع"
FROM appointments a
LEFT JOIN doctors d ON a.doctor_id = d.id
LEFT JOIN services s ON a.service_id = s.id
LEFT JOIN branches b ON a.branch_id = b.id
ORDER BY a.datetime DESC
LIMIT 50;

-- ==================== الفواتير مع تفاصيل المريض ====================
SELECT 
    i.id,
    i.invoice_number as "رقم الفاتورة",
    i.invoice_date as "تاريخ الفاتورة",
    i.total_amount as "المبلغ الإجمالي",
    i.payment_status as "حالة الدفع",
    p.full_name as "اسم المريض",
    p.phone_number as "هاتف المريض"
FROM invoices i
LEFT JOIN patients p ON i.patient_id = p.id
ORDER BY i.invoice_date DESC
LIMIT 50;
