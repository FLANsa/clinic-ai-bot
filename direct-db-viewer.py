#!/usr/bin/env python3
"""
عرض قاعدة البيانات مباشرة بدون API
يقرأ من قاعدة البيانات مباشرة ويعرض البيانات محلياً
"""
import sys
import os
from pathlib import Path

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
import json

settings = get_settings()

# إنشاء محرك قاعدة البيانات
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def safe_query_count(model, filter_condition=None):
    """استعلام آمن مع معالجة الأخطاء"""
    try:
        query = db.query(func.count(model.id))
        if filter_condition:
            query = query.filter(filter_condition)
        return query.scalar() or 0
    except:
        return 0

def safe_query_sum(model, column, filter_condition=None):
    """استعلام آمن لجمع القيم"""
    try:
        query = db.query(func.sum(column))
        if filter_condition:
            query = query.filter(filter_condition)
        return float(query.scalar() or 0)
    except:
        return 0.0

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
            "total_amount": safe_query_sum(Invoice, Invoice.total_amount),
        },
        "conversations": {
            "total": safe_query_count(Conversation),
        }
    }

def generate_html():
    """إنشاء صفحة HTML مع البيانات"""
    
    # جلب البيانات
    print("📊 جاري جلب البيانات من قاعدة البيانات...")
    
    stats = get_stats()
    
    # جلب البيانات مع معالجة الأخطاء
    try:
        appointments = db.query(Appointment).order_by(Appointment.datetime.desc()).limit(100).all()
    except:
        appointments = []
    
    try:
        patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(100).all()
    except:
        patients = []
    
    try:
        doctors = db.query(Doctor).limit(100).all()
    except:
        doctors = []
    
    try:
        invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).limit(100).all()
    except:
        invoices = []
    
    try:
        conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).limit(100).all()
    except:
        conversations = []
    
    try:
        services = db.query(Service).limit(100).all()
    except:
        services = []
    
    try:
        branches = db.query(Branch).limit(100).all()
    except:
        branches = []
    
    print(f"✅ تم جلب {len(appointments)} موعد، {len(patients)} مريض، {len(doctors)} طبيب")
    
    # إنشاء HTML
    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>عرض قاعدة البيانات - عيادات عادل كير</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .stat-card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .stat-card p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .tab {{
            background: white;
            padding: 15px 25px;
            border-radius: 10px 10px 0 0;
            cursor: pointer;
            border: none;
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .tab:hover {{
            background: #f0f0f0;
        }}
        .tab.active {{
            background: #667eea;
            color: white;
        }}
        .tab-content {{
            display: none;
            background: white;
            padding: 30px;
            border-radius: 0 15px 15px 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .tab-content.active {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: right;
            font-weight: bold;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-success {{ background: #28a745; color: white; }}
        .badge-warning {{ background: #ffc107; color: #333; }}
        .badge-danger {{ background: #dc3545; color: white; }}
        .badge-info {{ background: #17a2b8; color: white; }}
        .refresh-btn {{
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            margin-left: 10px;
            font-size: 14px;
        }}
        .refresh-btn:hover {{
            background: #218838;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 عرض قاعدة البيانات - عيادات عادل كير</h1>
            <p>عرض مباشر من قاعدة البيانات (بدون API)</p>
            <p style="margin-top: 10px; color: #666;">آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>{stats['appointments']['total']}</h3>
                <p>إجمالي المواعيد</p>
            </div>
            <div class="stat-card">
                <h3>{stats['appointments']['pending']}</h3>
                <p>مواعيد قيد الانتظار</p>
            </div>
            <div class="stat-card">
                <h3>{stats['patients']['total']}</h3>
                <p>إجمالي المرضى</p>
            </div>
            <div class="stat-card">
                <h3>{stats['doctors']['total']}</h3>
                <p>إجمالي الأطباء</p>
            </div>
            <div class="stat-card">
                <h3>{stats['invoices']['total']}</h3>
                <p>إجمالي الفواتير</p>
            </div>
            <div class="stat-card">
                <h3>{stats['conversations']['total']}</h3>
                <p>إجمالي المحادثات</p>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('appointments')">📅 المواعيد</button>
            <button class="tab" onclick="showTab('patients')">👥 المرضى</button>
            <button class="tab" onclick="showTab('doctors')">👨‍⚕️ الأطباء</button>
            <button class="tab" onclick="showTab('invoices')">🧾 الفواتير</button>
            <button class="tab" onclick="showTab('conversations')">💬 المحادثات</button>
            <button class="tab" onclick="showTab('services')">🩺 الخدمات</button>
            <button class="tab" onclick="showTab('branches')">🏢 الفروع</button>
        </div>

        <!-- Appointments -->
        <div id="appointments" class="tab-content active">
            <h2>📅 المواعيد ({len(appointments)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>التاريخ</th>
                        <th>اسم المريض</th>
                        <th>الهاتف</th>
                        <th>الحالة</th>
                        <th>القناة</th>
                        <th>النوع</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for apt in appointments:
        status_badge = {
            'pending': '<span class="badge badge-warning">قيد الانتظار</span>',
            'confirmed': '<span class="badge badge-success">مؤكد</span>',
            'completed': '<span class="badge badge-info">مكتمل</span>',
            'cancelled': '<span class="badge badge-danger">ملغي</span>'
        }.get(apt.status, f'<span class="badge">{apt.status}</span>')
        
        html += f"""
                    <tr>
                        <td>{apt.datetime.strftime('%Y-%m-%d %H:%M') if apt.datetime else '-'}</td>
                        <td>{apt.patient_name or '-'}</td>
                        <td>{apt.phone or '-'}</td>
                        <td>{status_badge}</td>
                        <td>{apt.channel or '-'}</td>
                        <td>{apt.appointment_type or '-'}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Patients -->
        <div id="patients" class="tab-content">
            <h2>👥 المرضى (""" + str(len(patients)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>الهاتف</th>
                        <th>البريد الإلكتروني</th>
                        <th>الجنس</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for patient in patients:
        active_badge = '<span class="badge badge-success">نشط</span>' if patient.is_active else '<span class="badge badge-danger">غير نشط</span>'
        html += f"""
                    <tr>
                        <td>{patient.full_name or '-'}</td>
                        <td>{patient.phone_number or '-'}</td>
                        <td>{patient.email or '-'}</td>
                        <td>{patient.gender or '-'}</td>
                        <td>{active_badge}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Doctors -->
        <div id="doctors" class="tab-content">
            <h2>👨‍⚕️ الأطباء (""" + str(len(doctors)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>التخصص</th>
                        <th>الهاتف</th>
                        <th>البريد الإلكتروني</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for doctor in doctors:
        active_badge = '<span class="badge badge-success">نشط</span>' if doctor.is_active else '<span class="badge badge-danger">غير نشط</span>'
        html += f"""
                    <tr>
                        <td>{doctor.name or '-'}</td>
                        <td>{doctor.specialty or '-'}</td>
                        <td>{doctor.phone_number or '-'}</td>
                        <td>{doctor.email or '-'}</td>
                        <td>{active_badge}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Invoices -->
        <div id="invoices" class="tab-content">
            <h2>🧾 الفواتير (""" + str(len(invoices)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>رقم الفاتورة</th>
                        <th>التاريخ</th>
                        <th>المبلغ الإجمالي</th>
                        <th>حالة الدفع</th>
                        <th>طريقة الدفع</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for invoice in invoices:
        status_badge = {
            'paid': '<span class="badge badge-success">مدفوع</span>',
            'pending': '<span class="badge badge-warning">قيد الانتظار</span>',
            'partially_paid': '<span class="badge badge-info">مدفوع جزئياً</span>',
            'cancelled': '<span class="badge badge-danger">ملغي</span>'
        }.get(invoice.payment_status, f'<span class="badge">{invoice.payment_status}</span>')
        
        html += f"""
                    <tr>
                        <td>{invoice.invoice_number or '-'}</td>
                        <td>{invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '-'}</td>
                        <td>{invoice.total_amount:.2f if invoice.total_amount else '0.00'} ريال</td>
                        <td>{status_badge}</td>
                        <td>{invoice.payment_method or '-'}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Conversations -->
        <div id="conversations" class="tab-content">
            <h2>💬 المحادثات (""" + str(len(conversations)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>التاريخ</th>
                        <th>المستخدم</th>
                        <th>القناة</th>
                        <th>الرسالة</th>
                        <th>الرد</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for conv in conversations:
        user_msg = (conv.user_message or '')[:50] + ('...' if len(conv.user_message or '') > 50 else '')
        bot_reply = (conv.bot_reply or '')[:50] + ('...' if len(conv.bot_reply or '') > 50 else '')
        html += f"""
                    <tr>
                        <td>{conv.created_at.strftime('%Y-%m-%d %H:%M') if conv.created_at else '-'}</td>
                        <td>{conv.user_id or '-'}</td>
                        <td>{conv.channel or '-'}</td>
                        <td>{user_msg}</td>
                        <td>{bot_reply}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Services -->
        <div id="services" class="tab-content">
            <h2>🩺 الخدمات (""" + str(len(services)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>السعر</th>
                        <th>الوصف</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for service in services:
        active_badge = '<span class="badge badge-success">نشط</span>' if service.is_active else '<span class="badge badge-danger">غير نشط</span>'
        desc = (service.description or '')[:50] + ('...' if len(service.description or '') > 50 else '')
        html += f"""
                    <tr>
                        <td>{service.name or '-'}</td>
                        <td>{service.base_price or '0'} ريال</td>
                        <td>{desc}</td>
                        <td>{active_badge}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>

        <!-- Branches -->
        <div id="branches" class="tab-content">
            <h2>🏢 الفروع (""" + str(len(branches)) + """)</h2>
            <table>
                <thead>
                    <tr>
                        <th>الاسم</th>
                        <th>المدينة</th>
                        <th>العنوان</th>
                        <th>الهاتف</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for branch in branches:
        active_badge = '<span class="badge badge-success">نشط</span>' if branch.is_active else '<span class="badge badge-danger">غير نشط</span>'
        html += f"""
                    <tr>
                        <td>{branch.name or '-'}</td>
                        <td>{branch.city or '-'}</td>
                        <td>{branch.address or '-'}</td>
                        <td>{branch.phone or '-'}</td>
                        <td>{active_badge}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""
    
    return html

if __name__ == '__main__':
    try:
        print("=" * 60)
        print("🚀 بدء عرض قاعدة البيانات مباشرة...")
        print("=" * 60)
        
        html = generate_html()
        
        # حفظ HTML في ملف
        output_file = Path(__file__).parent / "database-direct-view.html"
        output_file.write_text(html, encoding='utf-8')
        
        print(f"✅ تم إنشاء الملف: {output_file}")
        print("=" * 60)
        print("📂 افتح الملف في المتصفح:")
        print(f"   {output_file}")
        print("=" * 60)
        
        # فتح الملف تلقائياً
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        db.close()
        sys.exit(1)

