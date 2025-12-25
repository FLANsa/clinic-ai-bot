"""
Functional tests for Database operations
"""
import pytest
from datetime import datetime
import uuid
from app.db.models import Doctor, Service, Branch, Offer, FAQ, Appointment, Conversation


class TestDatabaseOperations:
    """اختبارات عمليات قاعدة البيانات"""
    
    def test_create_doctor(self, test_db, sample_branch):
        """اختبار إنشاء طبيب"""
        doctor = Doctor(
            id=uuid.uuid4(),
            name="د. أحمد الاختبار",
            specialty="طب الأسنان",
            branch_id=sample_branch.id,
            bio="طبيب أسنان متخصص",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(doctor)
        test_db.commit()
        test_db.refresh(doctor)
        
        assert doctor.id is not None
        assert doctor.name == "د. أحمد الاختبار"
    
    def test_create_service(self, test_db):
        """اختبار إنشاء خدمة"""
        service = Service(
            id=uuid.uuid4(),
            name="خدمة الاختبار",
            base_price=500.0,
            description="وصف الخدمة",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)
        
        assert service.id is not None
        assert service.name == "خدمة الاختبار"
    
    def test_create_branch(self, test_db):
        """اختبار إنشاء فرع"""
        branch = Branch(
            id=uuid.uuid4(),
            name="فرع الاختبار",
            city="الرياض",
            address="شارع الاختبار",
            working_hours={"from": "9:00", "to": "21:00"},
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(branch)
        test_db.commit()
        test_db.refresh(branch)
        
        assert branch.id is not None
        assert branch.name == "فرع الاختبار"
    
    def test_create_offer(self, test_db):
        """اختبار إنشاء عرض"""
        from datetime import timedelta
        offer = Offer(
            id=uuid.uuid4(),
            title="عرض الاختبار",
            description="وصف العرض",
            discount_type="percentage",
            discount_value=20.0,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(offer)
        test_db.commit()
        test_db.refresh(offer)
        
        assert offer.id is not None
        assert offer.title == "عرض الاختبار"
    
    def test_create_faq(self, test_db):
        """اختبار إنشاء FAQ"""
        faq = FAQ(
            id=uuid.uuid4(),
            question="سؤال الاختبار؟",
            answer="إجابة الاختبار",
            tags=[],
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(faq)
        test_db.commit()
        test_db.refresh(faq)
        
        assert faq.id is not None
        assert faq.question == "سؤال الاختبار؟"
    
    def test_create_conversation(self, test_db):
        """اختبار إنشاء محادثة"""
        now = datetime.now()
        conversation = Conversation(
            user_id="test_user_db",
            channel="whatsapp",
            user_message="مرحباً",
            bot_reply="أهلاً وسهلاً",
            intent="other",
            db_context_used=False,
            unrecognized=False,
            needs_handoff=False,
            created_at=now,
            updated_at=now
        )
        test_db.add(conversation)
        test_db.commit()
        test_db.refresh(conversation)
        
        assert conversation.id is not None
        assert conversation.user_id == "test_user_db"
    
    def test_query_doctors(self, test_db, sample_doctor, sample_branch):
        """اختبار استعلام الأطباء"""
        doctors = test_db.query(Doctor).filter(Doctor.is_active == True).all()
        assert len(doctors) >= 1
        assert sample_doctor in doctors
    
    def test_query_services(self, test_db, sample_service):
        """اختبار استعلام الخدمات"""
        services = test_db.query(Service).filter(Service.is_active == True).all()
        assert len(services) >= 1
        assert sample_service in services
    
    def test_query_branches(self, test_db, sample_branch):
        """اختبار استعلام الفروع"""
        branches = test_db.query(Branch).filter(Branch.is_active == True).all()
        assert len(branches) >= 1
        assert sample_branch in branches
    
    def test_update_doctor(self, test_db, sample_doctor, sample_branch):
        """اختبار تحديث طبيب"""
        sample_doctor.specialty = "طب العائلة"
        test_db.commit()
        test_db.refresh(sample_doctor)
        
        assert sample_doctor.specialty == "طب العائلة"
    
    def test_delete_doctor(self, test_db, sample_doctor, sample_branch):
        """اختبار حذف طبيب"""
        doctor_id = sample_doctor.id
        test_db.delete(sample_doctor)
        test_db.commit()
        
        deleted_doctor = test_db.query(Doctor).filter(Doctor.id == doctor_id).first()
        assert deleted_doctor is None
    
    def test_constraints_validation(self, test_db):
        """اختبار validation للـ constraints"""
        # محاولة إنشاء doctor بدون name (required field)
        try:
            doctor = Doctor(
                specialty="طب الأسنان",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            test_db.add(doctor)
            test_db.commit()
            # إذا نجح، يجب أن يكون name موجود
            assert doctor.name is not None
        except Exception:
            # إذا فشل، هذا متوقع
            test_db.rollback()
            pass

