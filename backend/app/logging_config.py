"""
إعداد اللوقينغ للنظام
يدعم file logging و structured logging للـ production
"""
import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """JSON Formatter للـ structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """تنسيق السجل كـ JSON"""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # إضافة exception info إذا كان موجوداً
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # إضافة extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_file_logging: bool = False,
    use_json: bool = False
) -> None:
    """
    إعداد logging للنظام
    
    Args:
        log_level: مستوى اللوقينغ (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: مسار ملف اللوقينغ (افتراضي: logs/app.log)
        enable_file_logging: تفعيل file logging (افتراضي: False للتطوير)
        use_json: استخدام JSON format للـ structured logging (افتراضي: False)
    """
    # تحديد مستوى اللوقينغ
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # تنسيق اللوقينغ
    if use_json:
        formatter = JSONFormatter()
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, date_format)
    
    # إعداد root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # إزالة handlers الموجودة
    root_logger.handlers.clear()
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (إذا كان مفعلاً)
    if enable_file_logging:
        if log_file is None:
            # إنشاء مجلد logs إذا لم يكن موجوداً
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            log_file = str(log_dir / "app.log")
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        # استخدام JSON format للـ file logging في Production
        file_formatter = JSONFormatter() if use_json else formatter
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # إعداد loggers محددة
    # تقليل verbosity لبعض المكتبات
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"تم إعداد logging بنجاح (المستوى: {log_level}, JSON: {use_json})")

