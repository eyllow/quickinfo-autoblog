"""Pexels API를 사용한 카테고리별 이미지 검색"""
import json
import logging
import requests
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_DIR = Path(settings.config_dir)


@dataclass
class PexelsImage:
    """Pexels 이미지 데이터"""
    id: int
    url: str
    photographer: str
    alt: str
    width: int
    height: int


class ImageFetcher:
    """Pexels API 카테고리별 이미지 검색기"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.pexels_api_key
        self.api_url = settings.pexels_api_url
        self.headers = {
            "Authorization": self.api_key
        }
        # 카테고리 설정 로드
        self.categories_config = self._load_categories()

    def _load_categories(self) -> dict:
        """카테고리 설정 로드"""
        try:
            filepath = CONFIG_DIR / "categories.json"
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load categories.json: {e}")
            return {"categories": {}, "image_styles": {}}

    def get_image_style_keywords(self, image_style: str) -> list[str]:
        """이미지 스타일에 해당하는 검색 키워드 반환"""
        image_styles = self.categories_config.get("image_styles", {})
        return image_styles.get(image_style, image_styles.get("ai_general", [
            "people lifestyle", "modern urban life", "success growth"
        ]))

    def search_images(
        self,
        keyword: str,
        count: int = 4,
        orientation: str = "landscape",
        image_style: str = None
    ) -> list[PexelsImage]:
        """
        Pexels에서 카테고리 스타일에 맞는 이미지 검색

        Args:
            keyword: 검색 키워드
            count: 반환할 이미지 수
            orientation: 이미지 방향 (landscape, portrait, square)
            image_style: 이미지 스타일 (ai_office, ai_tech 등)

        Returns:
            PexelsImage 리스트
        """
        if not self.api_key:
            logger.warning("Pexels API key not configured")
            return []

        try:
            # 이미지 스타일에 따른 검색어 결정
            if image_style:
                style_keywords = self.get_image_style_keywords(image_style)
            else:
                style_keywords = self._get_default_search_terms(keyword)
                style_keywords = [style_keywords]  # 단일 문자열을 리스트로

            images = []

            # 각 스타일 키워드로 검색하여 다양한 이미지 확보
            for style_term in style_keywords[:count]:
                search_query = style_term

                params = {
                    "query": search_query,
                    "per_page": 3,
                    "orientation": orientation,
                    "size": "medium"
                }

                logger.info(f"Searching Pexels: {search_query}")
                response = requests.get(
                    self.api_url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                photos = data.get("photos", [])

                if photos:
                    photo = photos[0]  # 첫 번째 결과 사용
                    img_url = photo.get("src", {}).get("medium", "")
                    if not img_url:
                        img_url = photo.get("src", {}).get("large", "")

                    image = PexelsImage(
                        id=photo.get("id"),
                        url=img_url,
                        photographer=photo.get("photographer", ""),
                        alt=photo.get("alt", keyword),
                        width=photo.get("width", 800),
                        height=photo.get("height", 600)
                    )
                    images.append(image)

                if len(images) >= count:
                    break

            logger.info(f"Found {len(images)} images for style: {image_style or 'default'}")
            return images

        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching images: {e}")
            return []

    def _get_default_search_terms(self, keyword: str) -> str:
        """
        한글 키워드를 영문 검색어로 변환 (기본 매핑)
        """
        keyword_map = {
            # 재테크
            "연말정산": "office documents tax",
            "세금": "tax calculator money",
            "주식": "stock market trading",
            "투자": "investment finance",
            "부동산": "real estate house",
            "대출": "bank loan money",
            "적금": "savings money bank",
            "신용점수": "credit score finance",
            "청약": "apartment building",
            "전세": "apartment interior",
            "금리": "bank interest rate",

            # IT/테크
            "아이폰": "iphone smartphone",
            "갤럭시": "samsung smartphone",
            "노트북": "laptop computer",
            "맥북": "macbook laptop",
            "AI": "artificial intelligence",
            "인공지능": "artificial intelligence robot",
            "코딩": "programming code",
            "스마트폰": "smartphone mobile",

            # 연예
            "BTS": "concert stage lights",
            "아이돌": "music performance stage",
            "드라마": "tv drama filming",
            "콘서트": "concert audience lights",

            # 건강
            "다이어트": "healthy food diet",
            "운동": "fitness exercise gym",
            "영양제": "vitamins supplements",
            "건강": "healthy lifestyle",
            "수면": "sleep bedroom night",

            # 라이프
            "여행": "travel vacation",
            "맛집": "restaurant food",
            "카페": "coffee cafe",
            "요리": "cooking kitchen",
            "육아": "parenting baby",
            "청소": "cleaning home",
            "인테리어": "interior design home",

            # 취업
            "취업": "job interview office",
            "면접": "job interview",
            "이력서": "resume document",

            # 기본
            "트렌드": "trending modern",
        }

        for kr_key, en_terms in keyword_map.items():
            if kr_key in keyword:
                return en_terms

        return "modern technology business"

    def search_images_for_category(
        self,
        keyword: str,
        category_name: str,
        count: int = 4
    ) -> list[PexelsImage]:
        """
        카테고리에 맞는 이미지 검색

        Args:
            keyword: 블로그 키워드
            category_name: 카테고리 이름 (재테크, IT테크 등)
            count: 필요한 이미지 수

        Returns:
            PexelsImage 리스트
        """
        categories = self.categories_config.get("categories", {})
        category_info = categories.get(category_name, {})
        image_style = category_info.get("image_style", "ai_general")

        return self.search_images(
            keyword=keyword,
            count=count,
            image_style=image_style
        )

    def download_image(self, url: str) -> Optional[bytes]:
        """이미지 다운로드"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    def generate_image_html(
        self,
        image: PexelsImage,
        keyword: str,
        caption: str = None
    ) -> str:
        """
        이미지 HTML 생성

        Args:
            image: PexelsImage 객체
            keyword: 키워드 (alt 태그용)
            caption: 이미지 캡션

        Returns:
            HTML 문자열
        """
        if caption is None:
            caption = f"{keyword} 관련 이미지"

        alt_text = f"{keyword} - {image.alt}" if image.alt else keyword

        html = f'''
<figure style="text-align: center; margin: 30px 0;">
    <img src="{image.url}"
         alt="{alt_text}"
         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
         loading="lazy" />
    <figcaption style="margin-top: 10px; color: #666; font-size: 14px;">
        {caption} (Photo by {image.photographer} on Pexels)
    </figcaption>
</figure>
'''
        return html


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)
    fetcher = ImageFetcher()

    # 카테고리별 이미지 검색 테스트
    print("=== 재테크 카테고리 (연말정산) ===")
    images = fetcher.search_images_for_category("연말정산", "재테크", count=4)
    for i, img in enumerate(images, 1):
        print(f"{i}. {img.url[:50]}... by {img.photographer}")

    print("\n=== IT테크 카테고리 (아이폰) ===")
    images = fetcher.search_images_for_category("아이폰16", "IT테크", count=4)
    for i, img in enumerate(images, 1):
        print(f"{i}. {img.url[:50]}... by {img.photographer}")

    print("\n=== 연예 카테고리 (BTS) ===")
    images = fetcher.search_images_for_category("BTS", "연예", count=4)
    for i, img in enumerate(images, 1):
        print(f"{i}. {img.url[:50]}... by {img.photographer}")
