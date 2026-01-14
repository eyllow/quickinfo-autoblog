"""
이미지 처리 통합 모듈
스크린샷과 Pexels 이미지를 통합 처리합니다.
"""
import logging
from typing import Dict, List, Optional

from media.screenshot import ScreenshotCapture
from media.image_fetcher import ImageFetcher
from media.link_matcher import LinkMatcher

logger = logging.getLogger(__name__)


class ImageProcessor:
    """콘텐츠 이미지 처리 통합"""

    def __init__(self):
        self.screenshot = ScreenshotCapture()
        self.pexels = ImageFetcher()
        self.link_matcher = LinkMatcher()

    def process_images(
        self,
        keyword: str,
        image_types: List[str],
        category: str = ""
    ) -> Dict[str, Dict]:
        """
        이미지 처리 통합
        1. SCREENSHOT 타입: 관련 사이트 스크린샷 시도
        2. PEXELS 타입: Pexels 이미지로 가져오기
        3. 스크린샷 실패 시 Pexels로 폴백

        Args:
            keyword: 키워드
            image_types: AI가 판단한 이미지 타입 리스트 (예: ["SCREENSHOT", "PEXELS", "PEXELS"])
            category: 카테고리

        Returns:
            이미지 정보 딕셔너리 (키: image_1, image_2, ...)
        """
        images = {}
        screenshot_done = False
        pexels_count = 0

        logger.info(f"이미지 처리 시작: {keyword}, 타입={image_types}")

        # 이미지 타입별 처리
        for idx, img_type in enumerate(image_types, 1):
            image_key = f"image_{idx}"

            if img_type == "SCREENSHOT" and not screenshot_done:
                # 스크린샷 시도 (한 번만)
                screenshot_result = self._capture_screenshot(keyword)
                if screenshot_result:
                    images[image_key] = screenshot_result
                    screenshot_done = True
                    logger.info(f"스크린샷 성공: {image_key}")
                else:
                    # 스크린샷 실패 시 Pexels로 폴백
                    logger.warning(f"스크린샷 실패, Pexels로 폴백: {image_key}")
                    pexels_image = self._fetch_pexels_image(keyword, pexels_count)
                    if pexels_image:
                        images[image_key] = pexels_image
                        pexels_count += 1
            else:
                # PEXELS 이미지
                pexels_image = self._fetch_pexels_image(keyword, pexels_count)
                if pexels_image:
                    images[image_key] = pexels_image
                    pexels_count += 1

        logger.info(f"이미지 처리 완료: 총 {len(images)}개")
        return images

    def _capture_screenshot(self, keyword: str) -> Optional[Dict]:
        """
        스크린샷 캡처

        Args:
            keyword: 키워드

        Returns:
            스크린샷 정보 또는 None
        """
        # 관련 사이트 찾기
        site = self.link_matcher.get_primary_site(keyword)
        if not site:
            logger.info(f"스크린샷용 관련 사이트 없음: {keyword}")
            return None

        # 스크린샷 캡처
        result = self.screenshot.capture_with_fallback(keyword, retry=2)
        if result:
            return {
                "type": "screenshot",
                "path": result.get("path"),
                "url": result.get("url"),
                "alt": f"{keyword} - {site['name']} 화면",
                "caption": f"{site['name']} 공식 사이트 화면",
                "source": site["name"]
            }
        return None

    def _fetch_pexels_image(self, keyword: str, index: int = 0) -> Optional[Dict]:
        """
        Pexels 이미지 가져오기

        Args:
            keyword: 키워드
            index: 이미지 인덱스 (다양성을 위해)

        Returns:
            이미지 정보 또는 None
        """
        # 페이지를 다르게 해서 다양한 이미지 가져오기
        page = (index // 2) + 1
        images = self.pexels.search_images(keyword, count=2, page=page)

        if images:
            img = images[index % len(images)] if len(images) > (index % 2) else images[0]
            return {
                "type": "pexels",
                "url": img["url"],
                "thumbnail": img.get("thumbnail"),
                "alt": f"{keyword} 관련 이미지",
                "caption": f"Photo by {img['photographer']} on Pexels",
                "photographer": img["photographer"],
                "photographer_url": img.get("photographer_url")
            }
        return None

    def get_screenshot_for_keyword(self, keyword: str) -> Optional[Dict]:
        """
        키워드에 맞는 스크린샷만 가져오기

        Args:
            keyword: 키워드

        Returns:
            스크린샷 정보 또는 None
        """
        return self._capture_screenshot(keyword)

    def get_pexels_images_for_keyword(self, keyword: str, count: int = 3) -> List[Dict]:
        """
        키워드에 맞는 Pexels 이미지만 가져오기

        Args:
            keyword: 키워드
            count: 이미지 개수

        Returns:
            이미지 정보 리스트
        """
        images = []
        for i in range(count):
            img = self._fetch_pexels_image(keyword, i)
            if img:
                images.append(img)
        return images


# 편의 함수
def process_post_images(keyword: str, image_types: List[str], category: str = "") -> Dict[str, Dict]:
    """
    포스트용 이미지 처리 편의 함수

    Args:
        keyword: 키워드
        image_types: 이미지 타입 리스트
        category: 카테고리

    Returns:
        이미지 정보 딕셔너리
    """
    processor = ImageProcessor()
    return processor.process_images(keyword, image_types, category)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 이미지 처리 테스트 ===\n")

    processor = ImageProcessor()

    # 테스트 키워드
    test_cases = [
        ("연말정산", ["SCREENSHOT", "PEXELS", "PEXELS"]),
        ("비트코인", ["PEXELS", "PEXELS"]),
        ("청년도약계좌", ["SCREENSHOT", "PEXELS"]),
    ]

    for keyword, image_types in test_cases:
        print(f"\n키워드: {keyword}")
        print(f"이미지 타입: {image_types}")

        images = processor.process_images(keyword, image_types)
        print(f"결과: {len(images)}개 이미지")

        for key, img in images.items():
            print(f"  {key}: {img['type']} - {img.get('alt', '')[:30]}")
