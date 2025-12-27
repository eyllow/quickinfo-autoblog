"""
WordPress 메뉴 상태 확인 스크립트
REST API를 사용하여 메뉴 및 네비게이션 정보를 조회합니다.
"""
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def check_menus():
    """WordPress 메뉴 정보 조회"""
    auth = (settings.wp_user, settings.wp_app_password)

    print("\n" + "=" * 50)
    print("📋 WordPress 메뉴 정보 조회")
    print("=" * 50 + "\n")

    # 다양한 엔드포인트 시도
    endpoints = [
        ("/wp-json/wp/v2/pages", "페이지"),
        ("/wp-json/wp/v2/navigation", "네비게이션 블록"),
        ("/wp-json/wp/v2/menus", "메뉴"),
        ("/wp-json/wp/v2/menu-items", "메뉴 항목"),
    ]

    for endpoint, name in endpoints:
        response = requests.get(
            f"{settings.wp_url}{endpoint}",
            auth=auth,
            params={"per_page": 20}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: {len(data)}개 항목")

            for item in data[:10]:  # 최대 10개만 출력
                if isinstance(item, dict):
                    # 제목 추출
                    title = item.get('title', {})
                    if isinstance(title, dict):
                        title = title.get('rendered', 'N/A')
                    elif not title:
                        title = item.get('slug', 'N/A')

                    # ID와 slug
                    item_id = item.get('id', 'N/A')
                    slug = item.get('slug', 'N/A')

                    print(f"   - {title} (ID: {item_id}, slug: {slug})")
            print()
        else:
            print(f"❌ {name}: {response.status_code} (엔드포인트 없음 또는 권한 부족)\n")

    print("=" * 50)
    print("\n💡 블록 테마(Twenty Twenty-Five)의 메뉴 수정 방법:")
    print("   1. WordPress 관리자 접속: https://quickinfo.kr/wp-admin/")
    print("   2. 외모 → 편집기 (Site Editor)")
    print("   3. 좌측에서 'Template Parts' 선택")
    print("   4. 'Header' 또는 'Footer' 선택하여 편집")
    print("   5. Navigation 블록 클릭 후 메뉴 항목 수정")
    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    check_menus()
