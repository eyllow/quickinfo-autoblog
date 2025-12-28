#!/bin/bash
# systemd 서비스 설치 스크립트 (서버에서 한 번만 실행)

set -e

echo "=== systemd 서비스 설치 ==="

# 서비스 파일 복사
sudo cp quickinfo-dashboard-api.service /etc/systemd/system/
sudo cp quickinfo-dashboard-web.service /etc/systemd/system/

# systemd 리로드
sudo systemctl daemon-reload

# 서비스 활성화
sudo systemctl enable quickinfo-dashboard-api
sudo systemctl enable quickinfo-dashboard-web

# 서비스 시작
sudo systemctl start quickinfo-dashboard-api
sudo systemctl start quickinfo-dashboard-web

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "서비스 상태 확인:"
sudo systemctl status quickinfo-dashboard-api --no-pager
sudo systemctl status quickinfo-dashboard-web --no-pager
