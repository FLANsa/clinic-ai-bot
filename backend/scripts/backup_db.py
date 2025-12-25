#!/usr/bin/env python3
"""
Database Backup Script
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def backup_database():
    """إنشاء backup لقاعدة البيانات"""
    from app.config import get_settings
    
    settings = get_settings()
    database_url = settings.DATABASE_URL
    
    # تحليل database URL
    # postgresql://user:password@host:port/database
    if not database_url.startswith("postgresql://"):
        print("ERROR: Invalid database URL")
        return False
    
    # استخراج المعلومات من URL
    url_parts = database_url.replace("postgresql://", "").split("@")
    if len(url_parts) != 2:
        print("ERROR: Could not parse database URL")
        return False
    
    auth_parts = url_parts[0].split(":")
    if len(auth_parts) != 2:
        print("ERROR: Could not parse database credentials")
        return False
    
    username = auth_parts[0]
    password = auth_parts[1]
    
    db_host_port = url_parts[1].split("/")
    if len(db_host_port) != 2:
        print("ERROR: Could not parse database host/port")
        return False
    
    host_port = db_host_port[0].split(":")
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5432"
    database = db_host_port[1]
    
    # إنشاء مجلد backups
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # اسم ملف backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"clinic_ai_bot_backup_{timestamp}.sql"
    
    # إنشاء backup باستخدام pg_dump
    # تعيين password كمتغير بيئة لتجنب prompt
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    
    try:
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", username,
            "-d", database,
            "-F", "c",  # Custom format
            "-f", str(backup_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Backup created successfully: {backup_file}")
            print(f"  Size: {backup_file.stat().st_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"ERROR: Backup failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("ERROR: pg_dump not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = backup_database()
    sys.exit(0 if success else 1)

