"""
워드프레스 REST API 발행 모듈
블로그 글을 워드프레스에 발행합니다.
"""
import logging
import requests
from typing import Optional, List, Dict
from base64 import b64encode

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.categories import get_category_id
from media.image_fetcher import fetch_images

logger = logging.getLogger(__name__)


class WordPressPublisher:
    """워드프레스 REST API 클라이언트"""

    def __init__(self):
        self.base_url = settings.wp_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.username = settings.wp_user
        self.password = settings.wp_app_password

        # 인증 헤더
        credentials = f"{self.username}:{self.password}"
        token = b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        """설정 확인"""
        return bool(self.base_url and self.username and self.password)

    def test_connection(self) -> bool:
        """
        워드프레스 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            response = requests.get(
                f"{self.api_url}/posts",
                headers=self.headers,
                params={"per_page": 1},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"워드프레스 연결 실패: {e}")
            return False

    def upload_image(self, image_url: str, filename: str = None) -> Optional[int]:
        """
        이미지 업로드

        Args:
            image_url: 이미지 URL
            filename: 파일명

        Returns:
            미디어 ID 또는 None
        """
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            if not filename:
                filename = image_url.split("/")[-1].split("?")[0]
                if not filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    filename = "image.jpg"

            # 워드프레스에 업로드
            media_headers = {
                "Authorization": self.headers["Authorization"],
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/jpeg",
            }

            upload_response = requests.post(
                f"{self.api_url}/media",
                headers=media_headers,
                data=response.content,
                timeout=60
            )
            upload_response.raise_for_status()

            media_id = upload_response.json().get("id")
            logger.info(f"이미지 업로드 성공: ID {media_id}")
            return media_id

        except Exception as e:
            logger.error(f"이미지 업로드 실패: {e}")
            return None

    def insert_images_to_content(
        self,
        content: str,
        keyword: str,
        count: int = 5
    ) -> tuple:
        """
        본문에 이미지 삽입

        Args:
            content: HTML 본문
            keyword: 키워드 (이미지 검색용)
            count: 이미지 개수 (기본 5개)

        Returns:
            (수정된 본문, 첫 번째 이미지 ID) 튜플
        """
        import re

        # Pexels에서 이미지 수집
        print(f"  🖼️ 이미지 수집 중... ({keyword})")
        images = fetch_images(keyword, count)

        if not images:
            logger.warning("이미지를 찾을 수 없습니다.")
            content = re.sub(r'\[IMAGE_\d+\]', '', content)
            return content, None

        print(f"  ✅ {len(images)}개 이미지 수집 완료")

        first_image_id = None
        inserted_count = 0

        # 1. [IMAGE_X] 태그가 있으면 해당 위치에 삽입
        for i, img in enumerate(images, 1):
            tag = f"[IMAGE_{i}]"

            if tag in content:
                # 이미지 업로드
                media_id = self.upload_image(img["url"])

                if media_id:
                    if first_image_id is None:
                        first_image_id = media_id

                    img_html = self._create_image_html(img, keyword)
                    content = content.replace(tag, img_html)
                    inserted_count += 1
                    logger.info(f"이미지 {i} 삽입 완료 (태그 위치)")
                else:
                    content = content.replace(tag, "")

        # 2. 이미지가 하나도 삽입되지 않았으면 자동 위치 삽입
        if inserted_count == 0 and images:
            print("  ⚠️ 이미지 태그가 없어 자동 위치 삽입...")
            content, first_image_id = self._auto_insert_images(content, images, keyword)
            inserted_count = min(3, len(images))

        # 남은 이미지 태그 제거
        content = re.sub(r'\[IMAGE_\d+\]', '', content)

        print(f"  ✅ 총 {inserted_count}개 이미지 본문에 삽입 완료")
        return content, first_image_id

    def _create_image_html(self, img: dict, keyword: str) -> str:
        """이미지 HTML 생성"""
        alt_text = img.get('alt', f'{keyword} 관련 이미지')
        photographer = img.get('photographer', 'Pexels')

        return f'''
<figure style="text-align: center; margin: 40px 0;">
    <img src="{img['url']}"
         alt="{alt_text}"
         style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"
         loading="lazy" />
    <figcaption style="margin-top: 12px; color: #888; font-size: 13px;">
        {alt_text} | Photo by {photographer}
    </figcaption>
</figure>
'''

    def _auto_insert_images(self, content: str, images: list, keyword: str) -> tuple:
        """
        [IMAGE_X] 태그가 없을 때 자동으로 이미지 삽입

        Args:
            content: HTML 본문
            images: 이미지 리스트
            keyword: 키워드

        Returns:
            (수정된 본문, 첫 번째 이미지 ID)
        """
        import re

        first_image_id = None

        # H2 또는 H3 태그 위치 찾기
        headings = list(re.finditer(r'</h[23]>', content, re.IGNORECASE))

        if len(headings) >= 2:
            # 헤딩이 충분하면 2번째, 4번째, 6번째 헤딩 뒤에 삽입
            insert_positions = []
            for i, match in enumerate(headings):
                if i in [1, 3, 5]:  # 2번째, 4번째, 6번째
                    insert_positions.append(match.end())

            # 뒤에서부터 삽입 (인덱스 변경 방지)
            for idx, pos in enumerate(reversed(insert_positions)):
                img_idx = len(insert_positions) - 1 - idx
                if img_idx < len(images):
                    img = images[img_idx]
                    media_id = self.upload_image(img["url"])

                    if media_id:
                        if first_image_id is None:
                            first_image_id = media_id
                        img_html = self._create_image_html(img, keyword)
                        content = content[:pos] + img_html + content[pos:]
                        logger.info(f"이미지 자동 삽입 완료 (헤딩 뒤)")
        else:
            # 헤딩이 부족하면 </p> 태그 기준으로 삽입
            paragraphs = list(re.finditer(r'</p>', content, re.IGNORECASE))
            total_p = len(paragraphs)

            if total_p >= 3:
                # 1/3, 2/3 위치에 삽입
                insert_positions = [
                    paragraphs[total_p // 3].end(),
                    paragraphs[total_p * 2 // 3].end(),
                ]

                for idx, pos in enumerate(reversed(insert_positions)):
                    if idx < len(images):
                        img = images[idx]
                        media_id = self.upload_image(img["url"])

                        if media_id:
                            if first_image_id is None:
                                first_image_id = media_id
                            img_html = self._create_image_html(img, keyword)
                            content = content[:pos] + img_html + content[pos:]
                            logger.info(f"이미지 자동 삽입 완료 (단락 뒤)")

        return content, first_image_id

    def publish_post(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        category: str = "트렌드",
        tags: List[str] = None,
        featured_image_id: int = None,
        status: str = "draft"
    ) -> Optional[Dict]:
        """
        글 발행

        Args:
            title: 제목
            content: 본문 HTML
            excerpt: 메타 설명
            category: 카테고리명
            tags: 태그 리스트
            featured_image_id: 특성 이미지 ID
            status: 발행 상태 (draft/publish)

        Returns:
            발행 결과 또는 None
        """
        if not self.is_configured():
            logger.error("워드프레스 설정이 없습니다.")
            return None

        try:
            # 카테고리 ID
            category_id = get_category_id(category)

            # 태그 생성 (없으면 키워드에서 추출)
            if not tags:
                tags = title.split()[:5]

            # 태그 ID 조회/생성
            tag_ids = []
            for tag_name in tags:
                tag_id = self._get_or_create_tag(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)

            # 포스트 데이터
            post_data = {
                "title": title,
                "content": content,
                "excerpt": excerpt,
                "status": status,
                "categories": [category_id],
                "tags": tag_ids,
            }

            if featured_image_id:
                post_data["featured_media"] = featured_image_id

            # 발행 요청
            logger.info(f"글 발행 중: {title} (상태: {status})")
            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            post_url = result.get("link", "")

            logger.info(f"글 발행 성공: {post_url}")

            return {
                "id": result.get("id"),
                "url": post_url,
                "title": title,
                "status": status,
            }

        except requests.RequestException as e:
            logger.error(f"글 발행 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답: {e.response.text}")
            return None

    def _get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """태그 조회 또는 생성"""
        try:
            # 태그 검색
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                params={"search": tag_name},
                timeout=10
            )

            if response.status_code == 200:
                tags = response.json()
                if tags:
                    return tags[0]["id"]

            # 새 태그 생성
            create_response = requests.post(
                f"{self.api_url}/tags",
                headers=self.headers,
                json={"name": tag_name},
                timeout=10
            )

            if create_response.status_code in [200, 201]:
                return create_response.json().get("id")

        except Exception as e:
            logger.debug(f"태그 처리 실패: {tag_name} - {e}")

        return None


def publish_to_wordpress(
    title: str,
    content: str,
    excerpt: str = "",
    category: str = "트렌드",
    keyword: str = "",
    status: str = "draft"
) -> Optional[Dict]:
    """
    워드프레스 발행 편의 함수

    Args:
        title: 제목
        content: 본문
        excerpt: 메타 설명
        category: 카테고리
        keyword: 키워드 (이미지 검색용)
        status: 발행 상태

    Returns:
        발행 결과 또는 None
    """
    publisher = WordPressPublisher()

    # 이미지 삽입
    if keyword:
        content, featured_image_id = publisher.insert_images_to_content(
            content, keyword, count=3
        )
    else:
        featured_image_id = None

    # 발행
    return publisher.publish_post(
        title=title,
        content=content,
        excerpt=excerpt,
        category=category,
        featured_image_id=featured_image_id,
        status=status
    )


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 워드프레스 연결 테스트 ===\n")

    publisher = WordPressPublisher()

    if not publisher.is_configured():
        print("❌ 워드프레스 설정이 없습니다.")
        print("   .env 파일에 WP_URL, WP_USER, WP_APP_PASSWORD를 설정하세요.")
    else:
        if publisher.test_connection():
            print("✅ 워드프레스 연결 성공!")
        else:
            print("❌ 워드프레스 연결 실패")
