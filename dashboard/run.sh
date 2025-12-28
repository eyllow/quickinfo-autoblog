#!/bin/bash

# QuickInfo Dashboard API 실행 스크립트

cd "$(dirname "$0")"

echo "==================================="
echo "QuickInfo Dashboard API Starting..."
echo "==================================="

# 가상환경 활성화 (있는 경우)
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# 의존성 설치 확인
pip install -q fastapi uvicorn pydantic python-multipart 2>/dev/null

# API 서버 실행
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload

