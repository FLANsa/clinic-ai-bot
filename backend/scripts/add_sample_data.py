"""
إضافة بيانات تجريبية لقاعدة البيانات
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Doctor, Service, Branch, Offer, FAQ
from datetime import datetime
import uuid


def add_sample_data(db: Session):
    """إضافة بيانات تجريبية"""
    print("📝 إضافة بيانات تجريبية...")
    
    # إضافة فروع
    print("  - إضافة فروع...")
    now = datetime.now()
    branches = [
        Branch(
            id=uuid.uuid4(),
            name="فرع الرياض",
            address="حي النخيل، شارع الملك فهد",
            city="الرياض",
            phone="0112345678",
            working_hours={"from": "9:00", "to": "21:00"},
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Branch(
            id=uuid.uuid4(),
            name="فرع جدة",
            address="حي الزهراء، شارع التحلية",
            city="جدة",
            phone="0123456789",
            working_hours={"from": "10:00", "to": "22:00"},
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Branch(
            id=uuid.uuid4(),
            name="فرع الدمام",
            address="حي الفيصلية، شارع الأمير سلطان",
            city="الدمام",
            phone="0134567890",
            working_hours={"from": "9:00", "to": "20:00"},
            is_active=True,
            created_at=now,
            updated_at=now
        )
    ]
    
    for branch in branches:
        existing = db.query(Branch).filter(Branch.name == branch.name).first()
        if not existing:
            db.add(branch)
            db.flush()  # flush بعد كل إضافة
    
    # إضافة أطباء
    print("  - إضافة أطباء...")
    doctors = [
        Doctor(
            id=uuid.uuid4(),
            name="د. محمد العلي",
            specialty="طب الأسنان",
            branch_id=branches[0].id if branches else None,
            bio="متخصص في تبييض الأسنان وتقويم الأسنان",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Doctor(
            id=uuid.uuid4(),
            name="د. سارة النجار",
            specialty="طب العائلة",
            branch_id=branches[0].id if branches else None,
            bio="متخصصة في الفحوصات الدورية والاستشارات العامة",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Doctor(
            id=uuid.uuid4(),
            name="د. خالد الأحمد",
            specialty="الجراحة العامة",
            branch_id=branches[1].id if len(branches) > 1 else None,
            bio="متخصص في الجراحات البسيطة والعمليات الجراحية",
            is_active=True,
            created_at=now,
            updated_at=now
        )
    ]
    
    for doctor in doctors:
        existing = db.query(Doctor).filter(Doctor.name == doctor.name).first()
        if not existing:
            db.add(doctor)
            db.flush()  # flush بعد كل إضافة
    
    # إضافة خدمات
    print("  - إضافة خدمات...")
    services = [
        Service(
            id=uuid.uuid4(),
            name="تبييض الأسنان",
            base_price=800.0,
            description="خدمة تبييض الأسنان - مدة الجلسة ساعة واحدة - يحتاج 2-3 جلسات",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Service(
            id=uuid.uuid4(),
            name="تنظيف الأسنان",
            base_price=200.0,
            description="تنظيف الأسنان - مدة الجلسة 30 دقيقة - يُنصح به كل 6 أشهر",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Service(
            id=uuid.uuid4(),
            name="حشو الأسنان",
            base_price=300.0,
            description="حشو الأسنان - مدة الجلسة 45 دقيقة - حسب حجم الحشو",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Service(
            id=uuid.uuid4(),
            name="تقويم الأسنان",
            base_price=5000.0,
            description="تقويم الأسنان - مدة العلاج سنة إلى سنتين - يحتاج متابعة شهرية",
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Service(
            id=uuid.uuid4(),
            name="الفحص الدوري",
            base_price=150.0,
            description="فحص دوري - مدة الجلسة 20 دقيقة - يُنصح به سنوياً",
            is_active=True,
            created_at=now,
            updated_at=now
        )
    ]
    
    for service in services:
        existing = db.query(Service).filter(Service.name == service.name).first()
        if not existing:
            db.add(service)
            db.flush()  # flush بعد كل إضافة
    
    # إضافة عروض
    print("  - إضافة عروض...")
    from datetime import timedelta
    offers = [
        Offer(
            id=uuid.uuid4(),
            title="عرض خاص على تبييض الأسنان",
            description="خصم 20% للجلسة الأولى",
            discount_type="percentage",
            discount_value=20.0,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
            created_at=now,
            updated_at=now
        ),
        Offer(
            id=uuid.uuid4(),
            title="عرض تنظيف الأسنان",
            description="خصم 10% عند الحجز لشخصين أو أكثر",
            discount_type="percentage",
            discount_value=10.0,
            start_date=now,
            end_date=now + timedelta(days=365),  # عرض لمدة سنة
            is_active=True,
            created_at=now,
            updated_at=now
        )
    ]
    
    for offer in offers:
        existing = db.query(Offer).filter(Offer.title == offer.title).first()
        if not existing:
            db.add(offer)
            db.flush()  # flush بعد كل إضافة
    
    # إضافة أسئلة شائعة
    print("  - إضافة أسئلة شائعة...")
    # تخطي FAQ مؤقتاً بسبب مشكلة في tags
    faqs = []
    
    for faq in faqs:
        existing = db.query(FAQ).filter(FAQ.question == faq.question).first()
        if not existing:
            db.add(faq)
            db.flush()  # flush بعد كل إضافة
    
    db.commit()
    print("✅ تم إضافة البيانات التجريبية بنجاح!")


def main():
    """الدالة الرئيسية"""
    print("="*60)
    print("🚀 إضافة بيانات تجريبية لقاعدة البيانات")
    print("="*60 + "\n")
    
    db = SessionLocal()
    try:
        add_sample_data(db)
        print("\n✅ تمت العملية بنجاح!")
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

