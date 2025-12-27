#!/bin/bash
#
# QuickInfo 테마 배포 스크립트
# WordPress 서버에서 실행: bash deploy_theme.sh
#

set -e

THEME_DIR="/opt/bitnami/wordpress/wp-content/themes/quickinfo-theme"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "=========================================="
echo "  QuickInfo Theme 배포"
echo "=========================================="
echo ""

# 테마 디렉토리 생성
echo "[1/4] 테마 디렉토리 생성..."
sudo mkdir -p $THEME_DIR
sudo mkdir -p $THEME_DIR/parts

# 파일 복사
echo "[2/4] 테마 파일 복사..."
sudo cp "$PROJECT_DIR/theme/style.css" $THEME_DIR/
sudo cp "$PROJECT_DIR/theme/theme.json" $THEME_DIR/
sudo cp "$PROJECT_DIR/theme/functions.php" $THEME_DIR/
sudo cp "$PROJECT_DIR/theme/parts/footer.html" $THEME_DIR/parts/

# 권한 설정
echo "[3/4] 권한 설정..."
sudo chown -R bitnami:daemon $THEME_DIR
sudo chmod -R 755 $THEME_DIR

# 확인
echo "[4/4] 설치 확인..."
echo ""
echo "설치된 파일:"
ls -la $THEME_DIR/
echo ""
ls -la $THEME_DIR/parts/

echo ""
echo "=========================================="
echo "  배포 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "  1. WordPress 관리자 접속: https://quickinfo.kr/wp-admin/"
echo "  2. 외모 > 테마로 이동"
echo "  3. 'QuickInfo Theme' 활성화"
echo "  4. 필수 페이지 생성: python scripts/create_pages.py"
echo ""
