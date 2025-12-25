#!/usr/bin/env python3
"""
سكريبت تشغيل اختبارات الأداء
"""
import os
import sys
import subprocess

def main():
    """تشغيل اختبارات الأداء"""
    
    # التحقق من وجود GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  تحذير: GROQ_API_KEY غير معرّف")
        print("   سيتم تخطي الاختبارات التي تحتاج API key")
        print()
    
    # تغيير المسار إلى مجلد backend
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_dir)
    
    print("="*70)
    print("🚀 تشغيل اختبارات الأداء")
    print("="*70)
    print()
    
    # تشغيل pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/performance/",
        "-v",  # verbose
        "-s",  # show print statements
        "--tb=short"  # shorter traceback
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⚠️  تم إيقاف الاختبارات بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الاختبارات: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

