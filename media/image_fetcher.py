"""
Pexels 이미지 수집 모듈
키워드에 맞는 무료 이미지를 수집합니다.
"""
import logging
import random
import requests
from typing import List, Dict, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings

logger = logging.getLogger(__name__)

# 한국어 → 영어 키워드 매핑 (자주 사용되는 키워드)
KEYWORD_TRANSLATIONS = {
    "연말정산": "tax return",
    "세금": "tax documents",
    "주식": "stock market",
    "투자": "investment finance",
    "부동산": "real estate",
    "비트코인": "bitcoin cryptocurrency",
    "다이어트": "healthy diet food",
    "운동": "fitness exercise",
    "건강": "healthy lifestyle",
    "자동차": "car automobile",
    "여행": "travel vacation",
    "맛집": "restaurant food",
    "아이폰": "iphone smartphone",
    "갤럭시": "samsung smartphone",
    "노트북": "laptop computer",
    "인테리어": "home interior",
    "요리": "cooking food",
    "뷰티": "beauty skincare",
    "패션": "fashion style",
}


class ImageFetcher:
    """Pexels API를 사용한 이미지 수집기 (중복 방지 포함)"""

    # 클래스 레벨에서 사용된 이미지 ID 추적
    _used_image_ids = set()

    def __init__(self):
        self.api_key = settings.pexels_api_key
        self.base_url = "https://api.pexels.com/v1/search"
        self.headers = {"Authorization": self.api_key}

    @classmethod
    def reset_used_images(cls):
        """새 글 작성 시 사용된 이미지 초기화"""
        cls._used_image_ids.clear()
        logger.info("이미지 중복 방지 캐시 초기화")

    def is_configured(self) -> bool:
        """API 설정 여부 확인"""
        return bool(self.api_key)

    def translate_keyword(self, keyword: str) -> str:
        """
        한국어 키워드를 영어로 변환

        Args:
            keyword: 한국어 키워드

        Returns:
            영어 키워드
        """
        # 매핑된 키워드 확인
        for kr, en in KEYWORD_TRANSLATIONS.items():
            if kr in keyword:
                return en

        # 매핑 없으면 일반적인 주제어 반환
        return "modern lifestyle"

    def search_images(
        self,
        keyword: str,
        count: int = 5,
        page: int = 1
    ) -> List[Dict]:
        """
        키워드로 이미지 검색

        Args:
            keyword: 검색 키워드
            count: 이미지 개수
            page: 페이지 번호 (중복 방지용)

        Returns:
            이미지 정보 리스트
        """
        if not self.is_configured():
            logger.warning("Pexels API가 설정되지 않았습니다.")
            return []

        try:
            # 영어로 변환
            en_keyword = self.translate_keyword(keyword)
            logger.info(f"이미지 검색: '{keyword}' → '{en_keyword}'")

            params = {
                "query": en_keyword,
                "per_page": count * 2,  # 선택 여유분
                "page": page,
                "orientation": "landscape",
            }

            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            photos = data.get("photos", [])

            if not photos:
                logger.warning(f"이미지를 찾을 수 없습니다: {en_keyword}")
                return []

            # 랜덤하게 섞기
            random.shuffle(photos)

            # 중복 제거하면서 이미지 수집
            images = []
            for photo in photos:
                photo_id = photo["id"]

                # 이미 사용된 이미지 건너뛰기
                if photo_id in self._used_image_ids:
                    continue

                # 사용 기록에 추가
                self._used_image_ids.add(photo_id)

                images.append({
                    "id": photo_id,
                    "url": photo["src"]["large"],  # 큰 이미지
                    "thumbnail": photo["src"]["medium"],
                    "alt": photo.get("alt", keyword),
                    "photographer": photo["photographer"],
                    "photographer_url": photo["photographer_url"],
                })

                if len(images) >= count:
                    break

            logger.info(f"이미지 {len(images)}개 수집 완료 (중복 제외)")
            return images

        except requests.RequestException as e:
            logger.error(f"이미지 검색 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"이미지 검색 오류: {e}")
            return []

    def get_images_for_post(self, keyword: str, count: int = 3) -> List[Dict]:
        """
        블로그 포스트용 이미지 수집 (중복 방지, 다중 페이지)

        Args:
            keyword: 키워드
            count: 필요한 이미지 개수

        Returns:
            이미지 정보 리스트
        """
        images = []
        max_pages = 5

        for page in range(1, max_pages + 1):
            if len(images) >= count:
                break

            new_images = self.search_images(keyword, count - len(images), page)
            images.extend(new_images)

        return images[:count]

    def fetch_single(self, keyword: str) -> Optional[Dict]:
        """
        단일 이미지 수집 (중복 없이)

        Args:
            keyword: 키워드

        Returns:
            이미지 정보 또는 None
        """
        images = self.get_images_for_post(keyword, count=1)
        return images[0] if images else None

    def fetch_with_variations(self, keyword: str, count: int = 3) -> List[Dict]:
        """
        다양한 검색어로 이미지 수집 (다양성 확보)

        Args:
            keyword: 기본 키워드
            count: 필요한 이미지 개수

        Returns:
            이미지 정보 리스트
        """
        # 검색어 변형
        variations = [
            keyword,
            f"{keyword} 정보",
            f"{keyword} 한국",
            "modern business",
            "professional office",
        ]

        images = []
        variation_idx = 0

        while len(images) < count and variation_idx < len(variations):
            search_keyword = variations[variation_idx]
            new_images = self.search_images(search_keyword, 2, page=random.randint(1, 3))

            for img in new_images:
                if len(images) >= count:
                    break
                images.append(img)

            variation_idx += 1

        return images[:count]


def fetch_images(keyword: str, count: int = 3) -> List[Dict]:
    """
    이미지 수집 편의 함수

    Args:
        keyword: 키워드
        count: 이미지 개수

    Returns:
        이미지 정보 리스트
    """
    fetcher = ImageFetcher()
    return fetcher.get_images_for_post(keyword, count)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== Pexels 이미지 검색 테스트 ===\n")

    fetcher = ImageFetcher()

    if not fetcher.is_configured():
        print("❌ Pexels API가 설정되지 않았습니다.")
        print("   .env 파일에 PEXELS_API_KEY를 설정하세요.")
    else:
        keyword = "연말정산"
        images = fetcher.get_images_for_post(keyword, count=3)

        print(f"검색 키워드: {keyword}\n")
        for i, img in enumerate(images, 1):
            print(f"{i}. {img['alt']}")
            print(f"   URL: {img['url'][:60]}...")
            print(f"   사진작가: {img['photographer']}")
            print()
