"""
WordPress 페이지 중복 제목 제거 스크립트
페이지 본문에서 첫 번째 H2 제목 블록을 제거합니다.
(WordPress가 페이지 제목을 자동 표시하므로 본문 내 제목은 불필요)
"""
import requests
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def remove_duplicate_title(page_id: int, page_name: str) -> bool:
    """페이지 본문에서 첫 번째 H2 제목 블록 제거"""
    auth = (settings.wp_user, settings.wp_app_password)

    # 1. 페이지 조회 (raw 콘텐츠 포함)
    response = requests.get(
        f"{settings.wp_url}/wp-json/wp/v2/pages/{page_id}",
        auth=auth,
        params={"context": "edit"}  # raw 콘텐츠 가져오기
    )

    if response.status_code != 200:
        print(f"❌ {page_name} 조회 실패: {response.status_code}")
        return False

    page = response.json()

    # raw 콘텐츠 가져오기
    content = page.get('content', {})
    if isinstance(content, dict):
        content = content.get('raw', content.get('rendered', ''))

    print(f"\n📄 {page_name} (ID: {page_id})")
    print(f"   현재 제목: {page['title']['rendered']}")

    # 2. 첫 번째 H2 블록 또는 heading 블록 제거
    original_content = content

    # 패턴 1: WordPress 블록 에디터 형식 (<!-- wp:heading --> ... <!-- /wp:heading -->)
    pattern_block = r'<!-- wp:heading[^>]*-->\s*<h2[^>]*>.*?</h2>\s*<!-- /wp:heading -->\s*'

    # 패턴 2: 단순 H2 태그 (맨 앞에 있는 경우)
    pattern_h2 = r'^[\s\n]*<h2[^>]*>.*?</h2>\s*'

    # 블록 형식 먼저 시도
    new_content = re.sub(pattern_block, '', content, count=1)

    # 변경 없으면 단순 H2 시도
    if new_content == content:
        new_content = re.sub(pattern_h2, '', content, count=1, flags=re.MULTILINE)

    # 앞뒤 공백 정리
    new_content = new_content.strip()

    if new_content == original_content.strip():
        print(f"   ℹ️  제거할 중복 제목 없음 (이미 정리됨)")
        return True

    # 3. 페이지 업데이트
    update_response = requests.post(
        f"{settings.wp_url}/wp-json/wp/v2/pages/{page_id}",
        auth=auth,
        json={"content": new_content}
    )

    if update_response.status_code == 200:
        print(f"   ✅ 중복 제목 제거 완료!")
        return True
    else:
        print(f"   ❌ 업데이트 실패: {update_response.status_code}")
        print(f"      {update_response.text[:200]}")
        return False


def main():
    print("\n" + "=" * 50)
    print("🔧 WordPress 페이지 중복 제목 제거")
    print("=" * 50)

    # 수정할 페이지 목록 (ID, 이름)
    pages = [
        (128, "개인정보처리방침"),
        (127, "문의하기"),
        (126, "소개"),
    ]

    success_count = 0
    for page_id, page_name in pages:
        if remove_duplicate_title(page_id, page_name):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"✅ 완료: {success_count}/{len(pages)} 페이지 처리됨")
    print("=" * 50)
    print("\n🌐 확인할 페이지:")
    print("   - https://quickinfo.kr/about/")
    print("   - https://quickinfo.kr/contact/")
    print("   - https://quickinfo.kr/privacy-policy-2/")
    print()


if __name__ == "__main__":
    main()
