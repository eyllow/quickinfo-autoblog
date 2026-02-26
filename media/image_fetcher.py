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

# 한국어 → 영어 Pexels 검색어 매핑 (다양성을 위해 리스트 사용)
KEYWORD_TO_PEXELS = {
    # === 정부/행정 관련 ===
    "정부24": ["government office document", "official paperwork", "document signing"],
    "등본": ["official document paperwork", "certificate document", "administrative office"],
    "민원": ["customer service office", "document filing", "public service"],
    "주민등록": ["id card document", "official certificate", "administrative paperwork"],

    # === 고용/실업 관련 ===
    "실업급여": ["job search interview", "career planning", "business meeting", "office professional"],
    "고용보험": ["employment office", "business professional", "career planning", "workplace"],
    "구직": ["job search resume", "interview preparation", "career planning professional"],
    "취업": ["job interview professional", "office worker success", "business professional"],
    "육아휴직": ["family work balance", "parent working home", "home office family"],
    "출산휴가": ["maternity family", "newborn care", "work life balance family"],

    # === 연금/보험 관련 ===
    "국민연금": ["retirement planning senior", "pension savings elderly", "financial planning retirement"],
    "건강보험": ["health insurance document", "medical healthcare", "hospital document"],
    "의료보험": ["medical insurance healthcare", "doctor patient consultation", "hospital care"],
    "자동차보험": ["car insurance document", "automobile safety", "vehicle protection"],
    "실비보험": ["health insurance medical", "healthcare document", "medical bill"],
    "암보험": ["health protection medical", "healthcare insurance", "medical document"],
    "보험": ["insurance document protection", "financial security", "document signing"],

    # === 세금/금융 관련 ===
    "연말정산": ["tax document calculator", "accounting office financial", "tax return form"],
    "종합소득세": ["tax filing document", "financial accounting", "tax calculator professional"],
    "부가세": ["business tax invoice", "accounting financial", "business document"],
    "양도소득세": ["real estate document", "property sale", "home transaction"],
    "증여세": ["family finance planning", "inheritance document", "legal financial"],
    "상속세": ["inheritance document legal", "estate planning", "family wealth"],
    "세금": ["tax documents calculator", "accounting professional", "financial planning"],

    # === 청년/금융상품 ===
    "청년도약계좌": ["young professional saving", "piggy bank savings", "financial planning youth"],
    "청년": ["young professional success", "career start office", "business professional young"],
    "적금": ["savings account money", "piggy bank financial", "money growth savings"],
    "주택청약": ["house keys new home", "real estate apartment", "home purchase"],

    # === 투자/금융정보 ===
    "주식": ["stock market chart graph", "trading investment", "finance analysis"],
    "투자": ["investment growth chart", "financial portfolio", "money growth"],
    "부동산": ["real estate property", "apartment building", "home sale house"],
    "비트코인": ["cryptocurrency digital", "blockchain technology", "digital finance"],
    "코스피": ["stock exchange trading", "financial market graph", "investment chart"],
    "환율": ["currency exchange money", "forex trading", "international finance"],

    # === 라이프스타일 ===
    "다이어트": ["healthy food nutrition", "fitness meal", "healthy eating lifestyle"],
    "운동": ["fitness exercise gym", "workout sports", "healthy lifestyle active"],
    "건강": ["healthy lifestyle wellness", "fitness active", "medical checkup"],
    "자동차": ["car automobile modern", "driving road", "vehicle transportation"],
    "여행": ["travel vacation destination", "tourism adventure", "airplane journey"],
    "맛집": ["restaurant food gourmet", "dining delicious", "food photography"],

    # === 테크 ===
    "아이폰": ["smartphone mobile technology", "mobile phone app", "technology device"],
    "갤럭시": ["smartphone android mobile", "mobile technology", "phone device"],
    "노트북": ["laptop computer work", "technology workspace", "office desk computer"],

    # === 기타 ===
    "인테리어": ["home interior design", "room furniture modern", "living space"],
    "요리": ["cooking food kitchen", "chef preparing", "home cooking"],
    "뷰티": ["beauty skincare cosmetics", "makeup self care", "beauty routine"],
    "패션": ["fashion style outfit", "clothing trendy", "style modern"],
    "날씨": ["weather sky clouds", "sunshine outdoor", "nature weather"],

    # === 인물/연예 관련 (직접 인물 대신 맥락 이미지) ===
    "배우": ["film camera clapperboard", "movie scene filming", "spotlight stage", "drama filming set"],
    "가수": ["concert stage performance", "microphone music", "music recording studio", "concert crowd"],
    "아이돌": ["concert stage lights", "kpop performance stage", "music performance", "fan concert"],
    "연예인": ["camera spotlight", "interview microphone", "entertainment media", "press conference"],
    "선수": ["stadium sports arena", "sports competition", "athletic performance", "sports award trophy"],
    "축구선수": ["soccer stadium football", "football field goal", "soccer match", "sports competition"],
    "야구선수": ["baseball stadium game", "baseball diamond", "sports competition", "stadium crowd"],
    "감독": ["film directing scene", "movie camera crew", "director chair", "filmmaking"],
    "정치인": ["government building capitol", "political conference", "press conference microphone", "parliament building"],
    "의원": ["parliament government building", "political meeting", "government official", "conference room"],
    "장관": ["government meeting official", "conference room politics", "official document signing"],
    "대표": ["business executive meeting", "corporate boardroom", "ceo office", "business professional"],
    "사장": ["executive office business", "ceo corporate", "business meeting room", "corporate leadership"],
    "회장": ["corporate boardroom executive", "business leadership", "ceo office modern", "business professional"],
    "교수": ["university lecture classroom", "academic professor", "education university", "research laboratory"],

    # === 조직/회사 관련 ===
    "공항": ["airport terminal departure", "airplane aviation", "airport gate", "travel airport"],
    "인천공항": ["airport terminal korea", "international airport", "airplane gate departure"],
    "회사": ["corporate office building", "business meeting", "modern office workspace"],
}

# 인물 키워드 맥락 추출용 매핑 (뉴스 맥락에서 관련 이미지 검색)
PERSON_CONTEXT_IMAGES = {
    "드라마": ["drama filming set", "tv production scene", "film camera"],
    "영화": ["movie cinema film", "film premiere", "movie theater"],
    "뮤지컬": ["musical theater stage", "broadway performance", "theater spotlight"],
    "콘서트": ["concert stage lights", "music performance live", "concert crowd"],
    "앨범": ["music album record", "recording studio", "music production"],
    "경기": ["sports stadium game", "sports competition", "athletic performance"],
    "대회": ["competition award trophy", "sports event", "championship"],
    "인터뷰": ["interview microphone media", "press conference", "media event"],
    "선임": ["business meeting corporate", "executive announcement", "corporate event"],
    "사장": ["ceo executive office", "corporate leadership", "business professional"],
    "취임": ["inauguration ceremony", "official ceremony", "leadership announcement"],
}

# 기본 검색어 (매핑 없을 때 사용)
DEFAULT_PEXELS_QUERIES = ["business office professional", "modern workspace", "technology office", "professional document"]

# 제외할 이미지 키워드 (부적절한 이미지 방지)
EXCLUDE_TERMS = [
    "police", "arrest", "crime", "sad", "crying", "angry",
    "funeral", "hospital bed", "accident", "violence", "gun",
    "stress", "headache", "frustrated", "worried", "anxious"
]


def get_person_image_query(keyword: str, news_context: str = "") -> str:
    """
    인물 키워드용 Pexels 검색어 생성 (뉴스 맥락 기반)

    인물 자체 이미지가 아닌 맥락 관련 이미지를 검색

    Args:
        keyword: 인물 키워드
        news_context: 뉴스/웹검색 맥락

    Returns:
        Pexels 검색어
    """
    # 1. 뉴스 맥락에서 키워드 추출하여 관련 이미지 찾기
    context_lower = (news_context + " " + keyword).lower()

    for context_keyword, queries in PERSON_CONTEXT_IMAGES.items():
        if context_keyword in context_lower:
            query = random.choice(queries)
            logger.info(f"인물 맥락 이미지: '{keyword}' + '{context_keyword}' → '{query}'")
            return query

    # 2. 직함/직업 키워드 매칭
    for kr_keyword, en_queries in KEYWORD_TO_PEXELS.items():
        if kr_keyword in context_lower:
            query = random.choice(en_queries)
            logger.info(f"인물 직업 이미지: '{keyword}' + '{kr_keyword}' → '{query}'")
            return query

    # 3. 기본 폴백 - 일반적인 미디어/뉴스 이미지
    default_person_queries = [
        "press conference media",
        "news media interview",
        "spotlight stage",
        "professional portrait silhouette",
        "business professional meeting"
    ]
    query = random.choice(default_person_queries)
    logger.info(f"인물 기본 이미지: '{keyword}' → '{query}'")
    return query


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
        한국어 키워드를 Pexels 검색어로 변환 (랜덤 선택으로 다양성 확보)

        Args:
            keyword: 한국어 키워드

        Returns:
            영어 Pexels 검색어
        """
        # 매핑된 키워드 확인
        for kr_keyword, en_queries in KEYWORD_TO_PEXELS.items():
            if kr_keyword in keyword:
                # 랜덤하게 하나 선택 (다양성)
                selected = random.choice(en_queries)
                logger.info(f"키워드 변환: '{keyword}' → '{selected}'")
                return selected

        # 매핑 없으면 기본 검색어에서 랜덤 선택
        default = random.choice(DEFAULT_PEXELS_QUERIES)
        logger.info(f"기본 검색어 사용: '{keyword}' → '{default}'")
        return default

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

            # 중복 제거 및 부적절한 이미지 필터링하면서 수집
            images = []
            for photo in photos:
                photo_id = photo["id"]

                # 이미 사용된 이미지 건너뛰기
                if photo_id in self._used_image_ids:
                    continue

                # 부적절한 이미지 필터링
                alt_text = photo.get("alt", "").lower()
                if any(term in alt_text for term in EXCLUDE_TERMS):
                    logger.debug(f"부적절한 이미지 제외: {alt_text[:50]}")
                    continue

                # 최소 해상도 체크 (width >= 800)
                width = photo.get("width", 0)
                if width < 800:
                    logger.debug(f"저해상도 이미지 제외: {width}px")
                    continue

                # 사용 기록에 추가
                self._used_image_ids.add(photo_id)

                # 주제 관련 설명 캡션 생성 (Pexels 출처 제거)
                raw_alt = photo.get("alt", "")
                caption_alt = raw_alt if raw_alt else keyword

                images.append({
                    "id": photo_id,
                    "url": photo["src"]["large"],  # 큰 이미지
                    "thumbnail": photo["src"]["medium"],
                    "alt": caption_alt,
                    "photographer": photo["photographer"],
                    "photographer_url": photo["photographer_url"],
                    "width": width,
                    "height": photo.get("height", 0),
                })

                if len(images) >= count:
                    break

            logger.info(f"이미지 {len(images)}개 수집 완료 (중복/부적절 제외)")
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
