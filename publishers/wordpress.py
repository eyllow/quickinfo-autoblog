"""워드프레스 REST API 발행기"""
import base64
import logging
import re
import time
from typing import Optional
from dataclasses import dataclass

import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings
from config.categories import (
    get_category_for_keyword,
    get_category_id,
    get_category_name,
    CATEGORY_IDS,
)
from generators.content_generator import clean_html_styles

logger = logging.getLogger(__name__)

# 카테고리별 추가 태그 매핑 (4개 카테고리 체계)
CATEGORY_TAGS = {
    "finance": ["재테크", "투자", "절세"],
    "policy": ["지원금", "정부정책", "혜택"],
    "life": ["생활정보", "실용정보"],
    "trend": ["트렌드", "이슈"],
    # 레거시 호환 (한글 카테고리명)
    "재테크": ["재테크", "투자", "절세"],
    "정책/지원금": ["지원금", "정부정책", "혜택"],
    "생활정보": ["생활정보", "실용정보"],
    "트렌드": ["트렌드", "이슈"],
}


def is_auto_publish_tag(tag: str) -> bool:
    """
    자동발행 내부용 태그인지 확인

    다음 패턴을 필터링:
    - 날짜 형식: 20251230, 2025-12-30, 2025/12/30
    - 자동발행 관련: 자동발행, auto, autopublish, scheduled
    - 순수 숫자: 1234
    """
    tag_lower = tag.lower().strip()

    # 자동발행 관련 키워드
    auto_keywords = ['자동발행', 'auto', 'autopublish', 'scheduled', 'autopost']
    if tag_lower in auto_keywords:
        return True

    # 순수 숫자 (날짜 등)
    if tag.isdigit():
        return True

    # YYYYMMDD 형식 (예: 20251230)
    if re.match(r'^\d{8}$', tag):
        return True

    # YYYY-MM-DD 또는 YYYY/MM/DD 형식
    if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', tag):
        return True

    # YYYYMM 형식 (예: 202512)
    if re.match(r'^\d{6}$', tag):
        return True

    return False


def generate_tags(keyword: str, category: str = None) -> list[str]:
    """
    SEO 최적화 태그 생성

    Args:
        keyword: 키워드
        category: 카테고리 이름

    Returns:
        태그 리스트 (최대 5개)
    """
    tags = []

    # 1. 키워드 기반 태그
    tags.append(keyword)

    # 키워드를 공백으로 분리하여 추가
    keyword_parts = keyword.split()
    for part in keyword_parts:
        if len(part) >= 2 and part != keyword:
            tags.append(part)

    # 2. 카테고리 기반 태그
    if category and category in CATEGORY_TAGS:
        tags.extend(CATEGORY_TAGS[category])

    # 3. 필터링 (자동발행 내부 태그 제거)
    filtered_tags = []
    for tag in tags:
        # 자동발행 내부 태그 제거 (날짜, auto 등)
        if is_auto_publish_tag(tag):
            logger.debug(f"Filtered auto-publish tag: {tag}")
            continue
        # 중복 제거
        if tag not in filtered_tags:
            filtered_tags.append(tag)

    # 최대 5개
    return filtered_tags[:5]


@dataclass
class PublishResult:
    """발행 결과 데이터 클래스"""
    success: bool
    post_id: Optional[int] = None
    url: Optional[str] = None
    error: Optional[str] = None


class WordPressPublisher:
    """워드프레스 REST API 발행기"""

    def __init__(
        self,
        wp_url: str = None,
        wp_user: str = None,
        wp_app_password: str = None
    ):
        self.wp_url = (wp_url or settings.wp_url).rstrip('/')
        self.wp_user = wp_user or settings.wp_user
        self.wp_app_password = wp_app_password or settings.wp_app_password

        # API 엔드포인트
        self.api_base = f"{self.wp_url}/wp-json/wp/v2"

        # Basic Auth 토큰 생성
        credentials = f"{self.wp_user}:{self.wp_app_password}"
        self.auth_token = base64.b64encode(credentials.encode()).decode()

        self.headers = {
            "Authorization": f"Basic {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        files: dict = None,
        retry_count: int = 3
    ) -> Optional[dict]:
        """
        API 요청 실행 (재시도 로직 포함)

        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            data: 요청 데이터
            files: 파일 데이터
            retry_count: 재시도 횟수

        Returns:
            응답 JSON 또는 None
        """
        url = f"{self.api_base}/{endpoint}"
        headers = self.headers.copy()

        for attempt in range(retry_count):
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                elif method == "POST":
                    if files:
                        # 파일 업로드 시 Content-Type 제거
                        headers.pop("Content-Type", None)
                        response = requests.post(
                            url, headers=headers, files=files, data=data, timeout=60
                        )
                    else:
                        response = requests.post(
                            url, headers=headers, json=data, timeout=30
                        )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    logger.error(f"All retry attempts failed for {endpoint}")
                    raise

        return None

    def upload_image(
        self,
        image_url: str = None,
        image_path: str = None,
        title: str = "Featured Image"
    ) -> Optional[int]:
        """
        이미지 업로드

        Args:
            image_url: 이미지 URL (Unsplash 등)
            image_path: 로컬 이미지 경로
            title: 이미지 제목

        Returns:
            미디어 ID 또는 None
        """
        try:
            if image_url:
                # URL에서 이미지 다운로드
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_data = response.content
                filename = "featured-image.jpg"
            elif image_path:
                # 로컬 파일 읽기
                with open(image_path, "rb") as f:
                    image_data = f.read()
                filename = Path(image_path).name
            else:
                logger.warning("No image source provided")
                return None

            # 미디어 업로드
            files = {
                "file": (filename, image_data, "image/jpeg")
            }
            data = {
                "title": title,
                "alt_text": title,
            }

            result = self._make_request("POST", "media", data=data, files=files)
            if result:
                media_id = result.get("id")
                logger.info(f"Image uploaded successfully: {media_id}")
                return media_id

        except Exception as e:
            logger.error(f"Failed to upload image: {e}")

        return None

    def get_or_create_category(self, category_name: str) -> Optional[int]:
        """
        카테고리 조회 또는 생성

        Args:
            category_name: 카테고리 이름

        Returns:
            카테고리 ID 또는 None
        """
        try:
            # 기존 카테고리 검색
            response = self._make_request(
                "GET",
                f"categories?search={category_name}"
            )
            if response and len(response) > 0:
                return response[0]["id"]

            # 새 카테고리 생성
            result = self._make_request(
                "POST",
                "categories",
                data={"name": category_name}
            )
            if result:
                return result.get("id")

        except Exception as e:
            logger.warning(f"Failed to get/create category: {e}")

        return None

    def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """
        태그 조회 또는 생성

        Args:
            tag_name: 태그 이름

        Returns:
            태그 ID 또는 None
        """
        try:
            # 기존 태그 검색
            response = self._make_request(
                "GET",
                f"tags?search={tag_name}"
            )
            if response and len(response) > 0:
                return response[0]["id"]

            # 새 태그 생성
            result = self._make_request(
                "POST",
                "tags",
                data={"name": tag_name}
            )
            if result:
                return result.get("id")

        except Exception as e:
            logger.warning(f"Failed to get/create tag: {e}")

        return None

    def publish_post(
        self,
        title: str,
        content: str,
        status: str = "publish",
        categories: list[str] = None,
        tags: list[str] = None,
        featured_media_id: int = None,
        excerpt: str = None,
        category_id: int = None
    ) -> PublishResult:
        """
        워드프레스에 글 발행

        Args:
            title: 글 제목
            content: HTML 본문
            status: 발행 상태 ('publish', 'draft', 'pending')
            categories: 카테고리 목록 (레거시 호환)
            tags: 태그 목록
            featured_media_id: 대표 이미지 ID
            excerpt: 요약문
            category_id: 카테고리 ID (직접 지정 - 우선 사용)

        Returns:
            PublishResult 객체
        """
        try:
            # 발행 전 HTML 스타일 정리 (왼쪽 검은 라인 등 제거)
            content = clean_html_styles(content)

            # 카테고리 ID 결정 (category_id 우선, 없으면 categories에서 변환)
            category_ids = []
            if category_id:
                # 직접 지정된 category_id 사용
                category_ids = [category_id]
                logger.info(f"Using direct category ID: {category_id}")
            elif categories:
                # 레거시 호환: 문자열 카테고리를 ID로 변환
                for cat in categories:
                    cat_id = self.get_or_create_category(cat)
                    if cat_id:
                        category_ids.append(cat_id)

            # 태그 ID 변환
            tag_ids = []
            if tags:
                for tag in tags:
                    tag_id = self.get_or_create_tag(tag)
                    if tag_id:
                        tag_ids.append(tag_id)

            # 포스트 데이터 구성
            post_data = {
                "title": title,
                "content": content,
                "status": status,
            }

            if category_ids:
                post_data["categories"] = category_ids
            if tag_ids:
                post_data["tags"] = tag_ids
            # Featured Image 제거 - 본문 이미지와 중복 방지
            # if featured_media_id:
            #     post_data["featured_media"] = featured_media_id
            if excerpt:
                post_data["excerpt"] = excerpt

            logger.info(f"Publishing post: {title} (status: {status}, categories: {category_ids})")

            # 포스트 발행
            result = self._make_request("POST", "posts", data=post_data)

            if result:
                post_id = result.get("id")
                post_url = result.get("link")
                logger.info(f"Post published successfully: {post_url}")

                return PublishResult(
                    success=True,
                    post_id=post_id,
                    url=post_url
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to publish post: {error_msg}")
            return PublishResult(success=False, error=error_msg)

        return PublishResult(success=False, error="Unknown error")

    def fetch_pexels_image(self, keyword: str) -> Optional[str]:
        """
        Pexels에서 키워드 관련 이미지 URL 가져오기

        Args:
            keyword: 검색 키워드

        Returns:
            이미지 URL 또는 None
        """
        api_key = settings.pexels_api_key
        if not api_key:
            logger.warning("PEXELS_API_KEY not found")
            return None

        try:
            # 한글 키워드를 영어로 매핑
            keyword_mapping = {
                "연말정산": "tax document calculator",
                "실업급여": "job search interview",
                "청년도약계좌": "savings money piggy bank",
                "국민연금": "retirement pension planning",
                "건강보험": "health insurance medical",
                "주택청약": "apartment housing keys",
                "전월세": "rental apartment interior",
                "정부24": "government office document",
                "비트코인": "cryptocurrency digital",
                "주식": "stock market chart",
                "환율": "currency exchange money",
            }

            # 키워드 매핑 찾기
            search_query = "business office professional"
            for kr_key, en_query in keyword_mapping.items():
                if kr_key in keyword:
                    search_query = en_query
                    break

            headers = {"Authorization": api_key}
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": search_query, "per_page": 1, "orientation": "landscape"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("photos"):
                    image_url = data["photos"][0]["src"]["large"]
                    logger.info(f"Pexels 이미지 찾음: {keyword} -> {search_query}")
                    return image_url

            logger.warning(f"Pexels 검색 실패: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Pexels image fetch failed: {e}")
            return None

    def publish_with_image(
        self,
        title: str,
        content: str,
        keyword: str,
        status: str = "publish",
        categories: list[str] = None,
        tags: list[str] = None,
        excerpt: str = None,
        category: str = None,
        category_id: int = None
    ) -> PublishResult:
        """
        이미지와 함께 글 발행

        Args:
            title: 글 제목
            content: HTML 본문
            keyword: 키워드 (이미지 검색용)
            status: 발행 상태
            categories: 카테고리 목록 (레거시 호환)
            tags: 태그 목록
            excerpt: 메타 설명 (요약문)
            category: 카테고리 이름 (태그 생성용)
            category_id: 카테고리 ID (직접 지정 시)

        Returns:
            PublishResult 객체
        """
        # 카테고리 자동 배정 (키워드 기반)
        if category_id is None and categories is None:
            category_key, auto_category_id = get_category_for_keyword(keyword)
            category_id = auto_category_id
            category = category_key  # 태그 생성용
            logger.info(f"Auto-assigned category: {get_category_name(category_key)} (ID: {category_id}) for keyword: {keyword}")

        # 태그 생성 (generate_tags 함수 사용)
        if tags is None:
            tags = generate_tags(keyword, category)
        else:
            # 기존 태그에서 자동발행 내부 태그 필터링
            tags = [t for t in tags if not is_auto_publish_tag(t)]
            if keyword not in tags:
                tags.insert(0, keyword)
            tags = tags[:5]

        logger.info(f"Generated tags: {tags}")

        # 글 발행 (category_id 직접 사용)
        return self.publish_post(
            title=title,
            content=content,
            status=status,
            categories=categories,
            tags=tags,
            excerpt=excerpt,
            category_id=category_id
        )


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 카테고리 자동 배정 테스트 ===\n")

    test_keywords = [
        "2026 연말정산 환급",
        "근로장려금 신청 방법",
        "종합소득세 신고",
        "손흥민 토트넘",
        "엔비디아 주가 전망",
    ]

    for kw in test_keywords:
        cat_key, cat_id = get_category_for_keyword(kw)
        cat_name = get_category_name(cat_key)
        print(f"{kw} → {cat_name} ({cat_key}, ID: {cat_id})")

    print("\n=== WordPress 발행 테스트 ===\n")

    publisher = WordPressPublisher()

    # 테스트 포스트 발행 (draft 모드) - 자동 카테고리 배정 테스트
    result = publisher.publish_with_image(
        title="테스트 포스트 - 연말정산",
        content="<p>이것은 테스트 포스트입니다.</p>",
        keyword="연말정산 환급",
        status="draft"
        # categories 생략 시 자동 배정됨
    )

    if result.success:
        print(f"Post published: {result.url}")
    else:
        print(f"Failed: {result.error}")
