#!/bin/bash
# Script لتشغيل الباك إند على البورت 8000

cd backend
echo "🚀 Starting backend server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

