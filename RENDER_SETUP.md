# إعداد Render للنشر

## المتغيرات البيئية المطلوبة

### 1. ADMIN_API_KEY (مطلوب)

**كيفية إضافة ADMIN_API_KEY في Render:**

1. اذهب إلى Service Settings في Render Dashboard
2. اضغط على **Environment** 
3. أضف متغير جديد:
   - **Key**: `ADMIN_API_KEY`
   - **Value**: قم بتوليد قيمة عشوائية قوية باستخدام:
     ```bash
     python3 -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - أو استخدم هذه القيمة (يُنصح بتغييرها):
     ```
     6841Stjr1M6MTIsdW1gamsW7mEef8-5h4o61En_rqL0
     ```

### 2. GROQ_API_KEY (مطلوب)

- احصل على مفتاح من: https://console.groq.com/
- أضفه في Render Dashboard كمتغير بيئة

### 3. WHATSAPP_ACCESS_TOKEN (مطلوب)

- احصل على Token من Facebook Developers
- أضفه في Render Dashboard

### 4. WHATSAPP_PHONE_NUMBER_ID (مطلوب)

- من Facebook Developers > WhatsApp > API Setup

### 5. WHATSAPP_BUSINESS_ACCOUNT_ID (مطلوب)

- من Facebook Developers > WhatsApp > API Setup

---

## بعد إضافة جميع المتغيرات:

1. اضغط **Save Changes**
2. Render سيعيد نشر الخدمة تلقائياً
3. تحقق من `/health` للتأكد من أن كل شيء يعمل

