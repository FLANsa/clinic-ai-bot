-- ============================================
-- استعلامات SQL للفروع والخدمات
-- ============================================

-- ==================== الفروع (Branches) ====================

-- 1. جلب جميع الفروع النشطة
SELECT 
    id,
    name,
    city,
    address,
    phone,
    location_url,
    working_hours,
    is_active,
    created_at,
    updated_at
FROM branches
WHERE is_active = true
ORDER BY created_at DESC;

-- 2. جلب جميع الفروع (بما فيها غير النشطة)
SELECT * FROM branches
ORDER BY name;

-- 3. جلب فرع محدد بالاسم
SELECT * FROM branches
WHERE name = 'فرع الشمال - حي الحزم';

-- 4. جلب الفروع في مدينة معينة
SELECT * FROM branches
WHERE city = 'الرياض'
ORDER BY name;

-- 5. جلب الفروع مع عدد الأطباء في كل فرع
SELECT 
    b.id,
    b.name,
    b.city,
    b.address,
    b.phone,
    COUNT(d.id) as doctors_count
FROM branches b
LEFT JOIN doctors d ON b.id = d.branch_id AND d.is_active = true
WHERE b.is_active = true
GROUP BY b.id, b.name, b.city, b.address, b.phone
ORDER BY doctors_count DESC;

-- 6. جلب الفروع مع عدد المواعيد القادمة
SELECT 
    b.id,
    b.name,
    b.city,
    COUNT(a.id) as upcoming_appointments
FROM branches b
LEFT JOIN appointments a ON b.id = a.branch_id
    AND a.datetime >= CURRENT_DATE
    AND a.status IN ('pending', 'confirmed')
WHERE b.is_active = true
GROUP BY b.id, b.name, b.city
ORDER BY upcoming_appointments DESC;

-- 7. جلب الفروع مع ساعات العمل
SELECT 
    id,
    name,
    city,
    address,
    phone,
    working_hours->>'sunday' as sunday_hours,
    working_hours->>'monday' as monday_hours,
    working_hours->>'tuesday' as tuesday_hours,
    working_hours->>'wednesday' as wednesday_hours,
    working_hours->>'thursday' as thursday_hours,
    working_hours->>'friday' as friday_hours,
    working_hours->>'saturday' as saturday_hours
FROM branches
WHERE is_active = true
ORDER BY name;

-- ==================== الخدمات (Services) ====================

-- 8. جلب جميع الخدمات النشطة
SELECT 
    id,
    name,
    description,
    base_price,
    is_active,
    created_at,
    updated_at
FROM services
WHERE is_active = true
ORDER BY name;

-- 9. جلب جميع الخدمات (بما فيها غير النشطة)
SELECT * FROM services
ORDER BY name;

-- 10. جلب الخدمات مرتبة حسب السعر
SELECT 
    id,
    name,
    description,
    base_price,
    is_active
FROM services
WHERE is_active = true
ORDER BY base_price ASC;

-- 11. جلب الخدمات مرتبة حسب السعر (من الأعلى للأقل)
SELECT 
    id,
    name,
    description,
    base_price,
    is_active
FROM services
WHERE is_active = true
ORDER BY base_price DESC;

-- 12. جلب الخدمات التي تحتوي على كلمة "أسنان" في الاسم
SELECT * FROM services
WHERE name LIKE '%أسنان%' OR name LIKE '%اسنان%'
ORDER BY base_price ASC;

-- 13. جلب الخدمات في نطاق سعري معين
SELECT * FROM services
WHERE is_active = true
    AND base_price BETWEEN 100 AND 300
ORDER BY base_price ASC;

-- 14. جلب الخدمات مع عدد المواعيد لكل خدمة
SELECT 
    s.id,
    s.name,
    s.description,
    s.base_price,
    COUNT(a.id) as appointments_count
FROM services s
LEFT JOIN appointments a ON s.id = a.service_id
WHERE s.is_active = true
GROUP BY s.id, s.name, s.description, s.base_price
ORDER BY appointments_count DESC;

-- 15. جلب الخدمات مع العروض المرتبطة
SELECT 
    s.id,
    s.name,
    s.description,
    s.base_price,
    o.title as offer_title,
    o.discount_type,
    o.discount_value,
    o.start_date,
    o.end_date
FROM services s
LEFT JOIN offers o ON s.id = o.related_service_id
    AND o.is_active = true
    AND (o.end_date IS NULL OR o.end_date >= CURRENT_DATE)
WHERE s.is_active = true
ORDER BY s.name;

-- 16. جلب الخدمات مع حساب السعر بعد الخصم (إن وجد)
SELECT 
    s.id,
    s.name,
    s.description,
    s.base_price as original_price,
    o.title as offer_title,
    o.discount_type,
    o.discount_value,
    CASE 
        WHEN o.discount_type = 'percentage' THEN 
            s.base_price - (s.base_price * o.discount_value / 100)
        WHEN o.discount_type = 'fixed' THEN 
            s.base_price - o.discount_value
        ELSE s.base_price
    END as final_price
FROM services s
LEFT JOIN offers o ON s.id = o.related_service_id
    AND o.is_active = true
    AND (o.end_date IS NULL OR o.end_date >= CURRENT_DATE)
WHERE s.is_active = true
ORDER BY s.name;

-- ==================== الفروع والخدمات معاً ====================

-- 17. جلب الفروع مع الخدمات المتاحة (من خلال الأطباء)
SELECT DISTINCT
    b.id as branch_id,
    b.name as branch_name,
    b.city,
    s.id as service_id,
    s.name as service_name,
    s.base_price,
    COUNT(DISTINCT d.id) as doctors_count
FROM branches b
CROSS JOIN services s
LEFT JOIN doctors d ON b.id = d.branch_id 
    AND d.is_active = true
    AND d.specialty LIKE '%' || s.name || '%'
WHERE b.is_active = true
    AND s.is_active = true
GROUP BY b.id, b.name, b.city, s.id, s.name, s.base_price
HAVING COUNT(DISTINCT d.id) > 0
ORDER BY b.name, s.name;

-- 18. جلب الفروع مع الخدمات المتاحة (من خلال المواعيد)
SELECT DISTINCT
    b.id as branch_id,
    b.name as branch_name,
    b.city,
    s.id as service_id,
    s.name as service_name,
    s.base_price,
    COUNT(a.id) as appointments_count
FROM branches b
INNER JOIN appointments a ON b.id = a.branch_id
INNER JOIN services s ON a.service_id = s.id
WHERE b.is_active = true
    AND s.is_active = true
GROUP BY b.id, b.name, b.city, s.id, s.name, s.base_price
ORDER BY b.name, appointments_count DESC;

-- 19. ملخص شامل: الفروع والخدمات والأطباء
SELECT 
    b.name as branch_name,
    b.city,
    b.phone as branch_phone,
    s.name as service_name,
    s.base_price,
    COUNT(DISTINCT d.id) as doctors_count,
    COUNT(DISTINCT a.id) as total_appointments
FROM branches b
LEFT JOIN doctors d ON b.id = d.branch_id AND d.is_active = true
LEFT JOIN appointments a ON b.id = a.branch_id
LEFT JOIN services s ON a.service_id = s.id
WHERE b.is_active = true
GROUP BY b.id, b.name, b.city, b.phone, s.id, s.name, s.base_price
ORDER BY b.name, s.name;

-- 20. إحصائيات سريعة للفروع والخدمات
SELECT 
    'الفروع النشطة' as category,
    COUNT(*) as count
FROM branches
WHERE is_active = true
UNION ALL
SELECT 
    'الخدمات النشطة',
    COUNT(*)
FROM services
WHERE is_active = true
UNION ALL
SELECT 
    'متوسط سعر الخدمات',
    ROUND(AVG(base_price), 2)
FROM services
WHERE is_active = true
UNION ALL
SELECT 
    'أعلى سعر خدمة',
    MAX(base_price)
FROM services
WHERE is_active = true
UNION ALL
SELECT 
    'أقل سعر خدمة',
    MIN(base_price)
FROM services
WHERE is_active = true;

-- ==================== استعلامات محددة ====================

-- 21. جلب فرع الشمال مع جميع خدماته
SELECT 
    b.name as branch_name,
    b.address,
    b.working_hours,
    s.name as service_name,
    s.description,
    s.base_price
FROM branches b
CROSS JOIN services s
WHERE b.name = 'فرع الشمال - حي الحزم'
    AND b.is_active = true
    AND s.is_active = true
ORDER BY s.name;

-- 22. جلب جميع خدمات الأسنان مع الأسعار
SELECT 
    name,
    description,
    base_price,
    CASE 
        WHEN base_price < 150 THEN 'اقتصادي'
        WHEN base_price < 300 THEN 'متوسط'
        ELSE 'عالي'
    END as price_category
FROM services
WHERE (name LIKE '%أسنان%' OR name LIKE '%اسنان%' OR description LIKE '%أسنان%')
    AND is_active = true
ORDER BY base_price ASC;

-- 23. جلب الفروع مع عدد الخدمات المتاحة في كل فرع
SELECT 
    b.name as branch_name,
    b.city,
    COUNT(DISTINCT a.service_id) as available_services_count,
    STRING_AGG(DISTINCT s.name, ', ') as services_list
FROM branches b
LEFT JOIN appointments a ON b.id = a.branch_id
LEFT JOIN services s ON a.service_id = s.id AND s.is_active = true
WHERE b.is_active = true
GROUP BY b.id, b.name, b.city
ORDER BY available_services_count DESC;

