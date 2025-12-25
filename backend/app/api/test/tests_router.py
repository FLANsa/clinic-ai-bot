"""
Tests API Endpoint - تشغيل جميع الاختبارات
"""
import logging
import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import os
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test/tests", tags=["Test - All Tests"])


class TestResult(BaseModel):
    """نتيجة اختبار واحد"""
    name: str
    success: bool
    duration: float
    output: str = ""
    error: str = ""


class AllTestsSummary(BaseModel):
    """ملخص جميع الاختبارات"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    total_duration: float
    timestamp: str
    results: Dict[str, TestResult]
    summary: Dict[str, Any]


def run_tests_command(test_path: str, test_name: str) -> tuple:
    """
    تشغيل اختبارات معينة
    
    Returns:
        (success, duration, stdout, stderr)
    """
    backend_dir = Path(__file__).parent.parent.parent.parent
    original_dir = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        
        cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", "--json-report", "--json-report-file=/tmp/pytest_report.json"]
        
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 دقائق timeout
        )
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        return result.returncode == 0, duration, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, 300.0, "", f"Timeout بعد 5 دقائق"
    except Exception as e:
        return False, 0.0, "", str(e)
    finally:
        os.chdir(original_dir)


@router.post("/run-all", response_model=AllTestsSummary)
async def run_all_tests():
    """
    تشغيل جميع الاختبارات (Unit, Integration, Functional, Performance)
    
    ملاحظة: هذا endpoint معطّل في Production لأنه يستهلك الكثير من الموارد
    
    Returns:
        AllTestsSummary: ملخص نتائج جميع الاختبارات
    """
    # تعطيل الاختبارات الشاملة في Production (Render) لأنها تستهلك الكثير من الموارد
    is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"
    if is_production:
        raise HTTPException(
            status_code=503,
            detail="الاختبارات الشاملة معطّلة في بيئة Production لأنها تستهلك الكثير من الموارد. يُرجى تشغيلها محلياً أو في بيئة التطوير."
        )
    
    logger.info("بدء تشغيل جميع الاختبارات...")
    
    tests_to_run = {
        "unit": "tests/unit/",
        "integration": "tests/integration/test_api.py",
        "functional": "tests/integration/test_comprehensive_functional.py",
        "performance": "tests/performance/test_comprehensive_performance.py"
    }
    
    results = {}
    total_duration = 0.0
    
    for test_name, test_path in tests_to_run.items():
        logger.info(f"تشغيل {test_name} tests...")
        success, duration, stdout, stderr = run_tests_command(test_path, test_name)
        
        total_duration += duration
        
        results[test_name] = TestResult(
            name=test_name,
            success=success,
            duration=duration,
            output=stdout[:5000] if stdout else "",  # Limit output size
            error=stderr[:2000] if stderr else ""  # Limit error size
        )
        
        logger.info(f"{test_name} tests {'نجح' if success else 'فشل'} في {duration:.2f}s")
    
    passed_tests = sum(1 for r in results.values() if r.success)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
    
    summary = AllTestsSummary(
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=total_tests - passed_tests,
        success_rate=round(success_rate, 2),
        total_duration=round(total_duration, 2),
        timestamp=datetime.now().isoformat(),
        results=results,
        summary={
            "unit": results["unit"].success,
            "integration": results["integration"].success,
            "functional": results["functional"].success,
            "performance": results["performance"].success
        }
    )
    
    return summary


@router.post("/run-unit", response_model=TestResult)
async def run_unit_tests():
    """تشغيل Unit Tests فقط"""
    success, duration, stdout, stderr = run_tests_command("tests/unit/", "unit")
    return TestResult(
        name="unit",
        success=success,
        duration=duration,
        output=stdout[:5000] if stdout else "",
        error=stderr[:2000] if stderr else ""
    )


@router.post("/run-functional", response_model=TestResult)
async def run_functional_tests():
    """تشغيل Functional Tests فقط"""
    # تعطيل في Production
    is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"
    if is_production:
        raise HTTPException(
            status_code=503,
            detail="اختبارات الوظائف معطّلة في بيئة Production لأنها تستهلك الكثير من الموارد. يُرجى تشغيلها محلياً أو في بيئة التطوير."
        )
    
    success, duration, stdout, stderr = run_tests_command(
        "tests/integration/test_comprehensive_functional.py",
        "functional"
    )
    return TestResult(
        name="functional",
        success=success,
        duration=duration,
        output=stdout[:5000] if stdout else "",
        error=stderr[:2000] if stderr else ""
    )


@router.post("/run-performance", response_model=TestResult)
async def run_performance_tests():
    """تشغيل Performance Tests فقط"""
    # تعطيل في Production
    is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"
    if is_production:
        raise HTTPException(
            status_code=503,
            detail="اختبارات الأداء معطّلة في بيئة Production لأنها تستهلك الكثير من الموارد. يُرجى تشغيلها محلياً أو في بيئة التطوير."
        )
    
    success, duration, stdout, stderr = run_tests_command(
        "tests/performance/test_comprehensive_performance.py",
        "performance"
    )
    return TestResult(
        name="performance",
        success=success,
        duration=duration,
        output=stdout[:5000] if stdout else "",
        error=stderr[:2000] if stderr else ""
    )

