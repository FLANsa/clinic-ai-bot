#!/usr/bin/env python3
"""
سيرفر لعرض قاعدة البيانات مباشرة
يعرض البيانات مباشرة من قاعدة البيانات عند فتح الصفحة
"""
import sys
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# إضافة مجلد backend إلى Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.db.models import (
    Appointment, Doctor, Service, Branch, Offer, FAQ,
    Patient, Treatment, Invoice, Employee, Conversation
)
from app.config import get_settings
from datetime import datetime

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def safe_query_count(model, filter_condition=None):
    """استعلام آمن مع معالجة الأخطاء"""
    db = SessionLocal()
    try:
        query = db.query(func.count(model.id))
        if filter_condition:
            query = query.filter(filter_condition)
        return query.scalar() or 0
    except:
        return 0
    finally:
        db.close()

def safe_query_all(model, order_by=None, limit=100):
    """استعلام آمن لجلب البيانات"""
    db = SessionLocal()
    try:
        query = db.query(model)
        if order_by:
            query = query.order_by(order_by)
        return query.limit(limit).all()
    except:
        return []
    finally:
        db.close()

def get_stats():
    """جلب الإحصائيات"""
    return {
        "appointments": {
            "total": safe_query_count(Appointment),
            "pending": safe_query_count(Appointment, Appointment.status == "pending"),
            "confirmed": safe_query_count(Appointment, Appointment.status == "confirmed"),
            "completed": safe_query_count(Appointment, Appointment.status == "completed"),
        },
        "patients": {
            "total": safe_query_count(Patient),
            "active": safe_query_count(Patient, Patient.is_active == True),
        },
        "doctors": {
            "total": safe_query_count(Doctor),
            "active": safe_query_count(Doctor, Doctor.is_active == True),
        },
        "invoices": {
            "total": safe_query_count(Invoice),
            "paid": safe_query_count(Invoice, Invoice.payment_status == "paid"),
            "pending": safe_query_count(Invoice, Invoice.payment_status == "pending"),
        },
        "conversations": {
            "total": safe_query_count(Conversation),
        }
    }

def serialize_model(obj):
    """تحويل النموذج إلى dictionary"""
    if obj is None:
        return None
    
    result = {}
    for key in dir(obj):
        if not key.startswith('_') and key not in ['metadata', 'registry']:
            try:
                value = getattr(obj, key)
                if not callable(value):
                    if isinstance(value, datetime):
                        result[key] = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        continue
                    else:
                        result[key] = value
            except:
                pass
    
    # إضافة الحقول المهمة
    if hasattr(obj, 'id'):
        result['id'] = str(obj.id)
    if hasattr(obj, 'created_at') and obj.created_at:
        result['created_at'] = obj.created_at.isoformat()
    if hasattr(obj, 'updated_at') and obj.updated_at:
        result['updated_at'] = obj.updated_at.isoformat()
    
    return result

class DBViewerHandler(BaseHTTPRequestHandler):
    """معالج HTTP لعرض قاعدة البيانات"""
    
    def do_GET(self):
        """معالجة طلبات GET"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.serve_html()
        elif path == '/api/stats':
            self.serve_json(get_stats())
        elif path == '/api/appointments':
            appointments = safe_query_all(Appointment, Appointment.datetime.desc(), 100)
            self.serve_json([serialize_model(a) for a in appointments])
        elif path == '/api/patients':
            patients = safe_query_all(Patient, Patient.created_at.desc(), 100)
            self.serve_json([serialize_model(p) for p in patients])
        elif path == '/api/doctors':
            doctors = safe_query_all(Doctor, None, 100)
            self.serve_json([serialize_model(d) for d in doctors])
        elif path == '/api/invoices':
            invoices = safe_query_all(Invoice, Invoice.invoice_date.desc(), 100)
            self.serve_json([serialize_model(i) for i in invoices])
        elif path == '/api/conversations':
            conversations = safe_query_all(Conversation, Conversation.created_at.desc(), 100)
            self.serve_json([serialize_model(c) for c in conversations])
        elif path == '/api/services':
            services = safe_query_all(Service, None, 100)
            self.serve_json([serialize_model(s) for s in services])
        elif path == '/api/branches':
            branches = safe_query_all(Branch, None, 100)
            self.serve_json([serialize_model(b) for b in branches])
        else:
            self.send_error(404)
    
    def serve_html(self):
        """خدمة صفحة HTML"""
        html_file = Path(__file__).parent / "database-viewer-live.html"
        
        if html_file.exists():
            content = html_file.read_text(encoding='utf-8')
        else:
            # إنشاء صفحة HTML بسيطة
            content = self.get_default_html()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_json(self, data):
        """خدمة JSON"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))
    
    def get_default_html(self):
        """إنشاء صفحة HTML افتراضية"""
        return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>عرض قاعدة البيانات - مباشر</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: right; border-bottom: 1px solid #ddd; }
        th { background: #667eea; color: white; }
        .loading { text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 عرض قاعدة البيانات - مباشر</h1>
        <div id="content" class="loading">جاري تحميل البيانات...</div>
    </div>
    <script>
        async function loadData() {
            try {
                const stats = await fetch('/api/stats').then(r => r.json());
                const appointments = await fetch('/api/appointments').then(r => r.json());
                const patients = await fetch('/api/patients').then(r => r.json());
                const doctors = await fetch('/api/doctors').then(r => r.json());
                
                let html = '<div class="card"><h2>📊 الإحصائيات</h2>';
                html += `<p>المواعيد: ${stats.appointments.total} | المرضى: ${stats.patients.total} | الأطباء: ${stats.doctors.total}</p></div>`;
                
                html += '<div class="card"><h2>📅 المواعيد</h2><table><tr><th>التاريخ</th><th>اسم المريض</th><th>الهاتف</th><th>الحالة</th></tr>';
                appointments.forEach(a => {
                    html += `<tr><td>${a.datetime || '-'}</td><td>${a.patient_name || '-'}</td><td>${a.phone || '-'}</td><td>${a.status || '-'}</td></tr>`;
                });
                html += '</table></div>';
                
                html += '<div class="card"><h2>👥 المرضى</h2><table><tr><th>الاسم</th><th>الهاتف</th><th>البريد</th></tr>';
                patients.forEach(p => {
                    html += `<tr><td>${p.full_name || '-'}</td><td>${p.phone_number || '-'}</td><td>${p.email || '-'}</td></tr>`;
                });
                html += '</table></div>';
                
                html += '<div class="card"><h2>👨‍⚕️ الأطباء</h2><table><tr><th>الاسم</th><th>التخصص</th><th>الهاتف</th></tr>';
                doctors.forEach(d => {
                    html += `<tr><td>${d.name || '-'}</td><td>${d.specialty || '-'}</td><td>${d.phone_number || '-'}</td></tr>`;
                });
                html += '</table></div>';
                
                document.getElementById('content').innerHTML = html;
            } catch (error) {
                document.getElementById('content').innerHTML = '<div class="card">❌ خطأ: ' + error.message + '</div>';
            }
        }
        loadData();
        setInterval(loadData, 30000); // تحديث كل 30 ثانية
    </script>
</body>
</html>"""
    
    def log_message(self, format, *args):
        """تسجيل الرسائل"""
        print(f"[{self.address_string()}] {format % args}")

def run_server(port=8080):
    """تشغيل السيرفر"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DBViewerHandler)
    
    print("=" * 60)
    print("🚀 سيرفر عرض قاعدة البيانات المباشر يعمل الآن!")
    print("=" * 60)
    print(f"📊 افتح المتصفح على: http://localhost:{port}")
    print("=" * 60)
    print("البيانات تُعرض مباشرة من قاعدة البيانات")
    print("الصفحة تتحدث تلقائياً كل 30 ثانية")
    print("=" * 60)
    print("اضغط Ctrl+C لإيقاف السيرفر")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف السيرفر")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("⚠️  منفذ غير صحيح، استخدام المنفذ الافتراضي 8080")
    
    run_server(port)

