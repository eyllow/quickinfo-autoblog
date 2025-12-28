#!/bin/bash
# QuickInfo Dashboard 배포 스크립트

set -e

echo "=== QuickInfo Dashboard 배포 시작 ==="

cd ~/quickinfo-autoblog
git pull

# Backend
echo ">>> Backend 설치..."
cd dashboard/backend
pip install -r requirements.txt

# Frontend
echo ">>> Frontend 빌드..."
cd ../frontend
npm install
npm run build

# Restart services
echo ">>> 서비스 재시작..."
sudo systemctl restart quickinfo-dashboard-api
sudo systemctl restart quickinfo-dashboard-web

echo ""
echo "=== 배포 완료 ==="
echo "API: http://43.202.224.41:8003"
echo "Web: http://43.202.224.41:3003"
echo ""
echo "상태 확인:"
echo "  sudo systemctl status quickinfo-dashboard-api"
echo "  sudo systemctl status quickinfo-dashboard-web"
