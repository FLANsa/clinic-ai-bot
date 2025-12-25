#!/usr/bin/env python3
"""
Script شامل لتشغيل جميع الاختبارات (وظيفية + أداء)
"""
import subprocess
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# الألوان للـ output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """طباعة header ملون"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """طباعة رسالة نجاح"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    """طباعة رسالة خطأ"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text):
    """طباعة رسالة تحذير"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def run_command(cmd, description):
    """تشغيل command وإرجاع النتيجة"""
    print(f"\n{Colors.BOLD}📋 {description}{Colors.RESET}")
    print(f"Command: {Colors.YELLOW}{' '.join(cmd)}{Colors.RESET}\n")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print_success(f"{description} - نجح ({duration:.2f}s)")
            return True, result.stdout, result.stderr
        else:
            print_error(f"{description} - فشل ({duration:.2f}s)")
            return False, result.stdout, result.stderr
    except Exception as e:
        duration = time.time() - start_time
        print_error(f"{description} - خطأ: {str(e)} ({duration:.2f}s)")
        return False, "", str(e)


def main():
    """الدالة الرئيسية"""
    # التأكد من أننا في مجلد backend
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    
    if os.getcwd() != str(backend_dir):
        os.chdir(backend_dir)
        print_warning(f"تم تغيير المجلد إلى: {backend_dir}")
    
    print_header("🚀 تشغيل جميع الاختبارات الشاملة")
    print(f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"المجلد: {os.getcwd()}")
    
    results = {
        "unit": {"success": False, "duration": 0},
        "integration": {"success": False, "duration": 0},
        "performance": {"success": False, "duration": 0},
        "functional": {"success": False, "duration": 0}
    }
    
    # 1. Unit Tests
    print_header("1️⃣  اختبارات الوحدة (Unit Tests)")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
        "Unit Tests"
    )
    results["unit"]["success"] = success
    if stdout:
        print(stdout)
    if stderr and not success:
        print(stderr)
    
    # 2. Integration Tests
    print_header("2️⃣  اختبارات التكامل (Integration Tests)")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
        "Integration Tests"
    )
    results["integration"]["success"] = success
    if stdout:
        print(stdout)
    if stderr and not success:
        print(stderr)
    
    # 3. Functional Tests (Comprehensive)
    print_header("3️⃣  اختبارات وظيفية شاملة (Comprehensive Functional Tests)")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/integration/test_comprehensive_functional.py", "-v", "--tb=short"],
        "Comprehensive Functional Tests"
    )
    results["functional"]["success"] = success
    if stdout:
        print(stdout)
    if stderr and not success:
        print(stderr)
    
    # 4. Performance Tests
    print_header("4️⃣  اختبارات الأداء (Performance Tests)")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/performance/", "-v", "-s", "--tb=short"],
        "Performance Tests"
    )
    results["performance"]["success"] = success
    if stdout:
        print(stdout)
    if stderr and not success:
        print(stderr)
    
    # ملخص النتائج
    print_header("📊 ملخص النتائج")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    for test_type, result in results.items():
        status = "✅ نجح" if result["success"] else "❌ فشل"
        print(f"{test_type.upper():20s}: {status}")
    
    print(f"\n{Colors.BOLD}النتيجة الإجمالية: {passed_tests}/{total_tests} اختبارات نجحت{Colors.RESET}")
    
    if passed_tests == total_tests:
        print_success("جميع الاختبارات نجحت! 🎉")
        return 0
    else:
        print_error(f"{total_tests - passed_tests} اختبارات فشلت")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

