"""
WordPress Sample Page 삭제 스크립트
REST API를 사용하여 Sample Page를 자동으로 삭제합니다.
"""
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def delete_sample_page():
    """Sample Page 찾아서 삭제"""
    auth = (settings.wp_user, settings.wp_app_password)

    print("\n" + "=" * 50)
    print("🗑️  WordPress Sample Page 삭제")
    print("=" * 50 + "\n")

    # 모든 페이지 조회
    response = requests.get(
        f"{settings.wp_url}/wp-json/wp/v2/pages",
        auth=auth,
        params={"per_page": 100, "status": "any"}
    )

    if response.status_code != 200:
        print(f"❌ 페이지 조회 실패: {response.status_code}")
        print(f"   응답: {response.text}")
        return False

    pages = response.json()
    print(f"📄 총 {len(pages)}개 페이지 발견\n")

    # 모든 페이지 목록 출력
    print("현재 페이지 목록:")
    for page in pages:
        title = page['title']['rendered'] if page['title']['rendered'] else '(제목 없음)'
        print(f"  - {title} (slug: {page['slug']}, ID: {page['id']})")

    print("\n" + "-" * 50 + "\n")

    # Sample Page 찾아서 삭제
    deleted_count = 0
    for page in pages:
        slug = page['slug'].lower()
        title = page['title']['rendered'].lower()

        # Sample Page 패턴 매칭
        if 'sample' in slug or 'sample' in title:
            print(f"🎯 삭제 대상 발견: {page['title']['rendered']} (ID: {page['id']})")

            # 삭제 (완전 삭제)
            del_response = requests.delete(
                f"{settings.wp_url}/wp-json/wp/v2/pages/{page['id']}",
                auth=auth,
                params={"force": True}
            )

            if del_response.status_code == 200:
                print(f"   ✅ 삭제 완료!")
                deleted_count += 1
            else:
                print(f"   ❌ 삭제 실패: {del_response.status_code}")
                print(f"      {del_response.text[:200]}")

    print("\n" + "=" * 50)
    if deleted_count > 0:
        print(f"✅ 총 {deleted_count}개 Sample Page 삭제 완료!")
    else:
        print("ℹ️  Sample Page를 찾을 수 없습니다.")
        print("   이미 삭제되었거나 다른 이름일 수 있습니다.")
    print("=" * 50 + "\n")

    return deleted_count > 0


if __name__ == "__main__":
    delete_sample_page()
