"""Pexels API를 사용한 AI 기반 컨텍스트 이미지 검색 + Puppeteer 스크린샷"""
import json
import logging
import random
import re
import requests
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings
from utils.unique_image import (
    generate_unique_screenshot,
    should_use_screenshot,
    cleanup_old_screenshots
)
from utils.screenshot_advisor import (
    get_screenshot_recommendation,
    validate_screenshot_url,
    get_fallback_url
)

logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_DIR = Path(settings.config_dir)

# =============================================================================
# 키워드별 영문 이미지 검색어 매핑 (확장판)
# =============================================================================
IMAGE_KEYWORD_MAPPING = {
    # 재테크/금융
    "비트코인": ["bitcoin cryptocurrency", "bitcoin trading chart", "crypto coins gold", "digital currency blockchain"],
    "코인": ["cryptocurrency trading", "bitcoin digital", "crypto investment", "blockchain technology"],
    "암호화폐": ["cryptocurrency market", "bitcoin ethereum", "crypto trading screen", "digital currency"],
    "주식": ["stock market chart", "trading screen monitor", "investment graph", "stock exchange floor"],
    "투자": ["investment portfolio", "money growth chart", "financial planning", "wealth management"],
    "연말정산": ["tax documents calculator", "financial paperwork office", "tax refund money", "accounting spreadsheet"],
    "세금": ["tax calculator documents", "financial forms", "tax payment receipt", "accounting office"],
    "부동산": ["apartment building exterior", "real estate house", "modern home interior", "property keys hand"],
    "대출": ["bank loan approval", "money lending documents", "credit application", "financial contract signing"],
    "청약": ["apartment construction", "housing complex aerial", "new building apartment", "modern apartment exterior"],
    "전세": ["apartment living room", "house interior modern", "real estate contract", "home keys"],
    "월세": ["apartment rental", "house keys contract", "modern studio apartment", "rental agreement"],
    "국민연금": ["retirement senior happy", "elderly couple smiling", "pension retirement", "senior citizen lifestyle"],
    "건강보험": ["health insurance card", "medical documents", "hospital healthcare", "insurance paperwork"],
    "실업급여": ["job search computer", "career change", "job hunting office", "unemployment office"],
    "신용점수": ["credit score report", "credit card finance", "financial documents", "banking app phone"],
    "신용카드": ["credit card payment", "card transaction pos", "shopping wallet", "credit card hand"],
    "적금": ["savings piggy bank", "money jar coins", "bank savings account", "financial growth"],
    "ETF": ["stock market monitor", "investment trading", "financial chart analysis", "portfolio management"],
    "연금저축": ["retirement planning", "pension fund", "senior couple happy", "financial security"],

    # IT/테크
    "아이폰": ["iphone smartphone hand", "apple iphone screen", "smartphone technology", "mobile phone white"],
    "갤럭시": ["samsung galaxy phone", "android smartphone", "mobile device screen", "smartphone technology"],
    "노트북": ["laptop computer desk", "macbook workspace", "laptop keyboard typing", "computer screen office"],
    "맥북": ["macbook laptop desk", "apple computer", "laptop workspace coffee", "macbook screen"],
    "AI": ["artificial intelligence robot", "AI technology circuit", "machine learning concept", "digital brain network"],
    "인공지능": ["AI robot futuristic", "artificial intelligence", "machine learning data", "technology innovation"],
    "챗GPT": ["AI chatbot screen", "artificial intelligence", "computer conversation", "technology innovation"],
    "스마트폰": ["smartphone hand holding", "mobile phone screen", "smartphone technology", "mobile device"],

    # 연예/드라마/영화
    "드라마": ["tv remote living room", "streaming service screen", "movie watching couch", "television entertainment"],
    "영화": ["cinema popcorn movie", "movie theater seats", "film camera production", "cinema screen dark"],
    "아이돌": ["concert stage lights", "music performance live", "microphone spotlight", "concert crowd audience"],
    "콘서트": ["concert audience lights", "music festival stage", "live performance crowd", "stage spotlight"],
    "BTS": ["concert stage lights", "music performance", "kpop stage", "audience concert"],
    "예능": ["tv studio set", "talk show stage", "entertainment studio", "variety show"],
    "넷플릭스": ["streaming service tv", "netflix watching", "movie night couch", "entertainment screen"],

    # 건강/다이어트
    "다이어트": ["healthy salad food", "weight loss fitness", "healthy eating vegetables", "diet meal prep"],
    "운동": ["gym workout fitness", "exercise training", "fitness equipment gym", "workout routine"],
    "헬스": ["gym fitness equipment", "workout training", "health club exercise", "fitness center"],
    "영양제": ["vitamin supplements bottle", "health pills capsules", "nutrition supplements", "wellness products"],
    "건강": ["healthy lifestyle nature", "wellness fitness", "healthy living", "active lifestyle outdoor"],
    "수면": ["sleep bedroom peaceful", "sleeping comfortable bed", "restful night bedroom", "peaceful sleep"],
    "탈모": ["hair care products", "scalp treatment", "hair growth", "hair wellness"],

    # 생활정보
    "운전면허": ["driving car interior", "car steering wheel", "driving lesson instructor", "road driving view"],
    "여행": ["travel vacation beach", "airplane window view", "tourist destination landmark", "vacation luggage"],
    "맛집": ["restaurant food delicious", "gourmet dining table", "food cuisine plate", "restaurant interior"],
    "카페": ["coffee cafe cozy", "cafe interior design", "coffee shop latte", "barista coffee"],
    "요리": ["cooking kitchen chef", "food preparation", "home cooking kitchen", "recipe ingredients"],
    "날씨": ["weather sky clouds", "sunny day outdoor", "rain umbrella", "weather forecast phone"],
    "육아": ["parenting baby child", "mother child happy", "family baby care", "parent child love"],
    "청소": ["cleaning home organized", "house cleaning supplies", "tidy room interior", "organized home"],
    "인테리어": ["interior design modern", "living room stylish", "home decoration", "apartment design"],
    "자동차": ["car automobile modern", "driving vehicle road", "car interior dashboard", "modern car exterior"],
    "자동차보험": ["car insurance document", "auto protection safety", "vehicle key hand", "car accident prevention"],
    "여권": ["passport travel documents", "airport departure board", "international travel", "passport stamps"],

    # 취업/교육
    "취업": ["job interview office", "career success business", "handshake meeting", "professional work"],
    "면접": ["job interview handshake", "business meeting office", "interview conversation", "career opportunity"],
    "이력서": ["resume document writing", "job application", "career documents", "CV preparation"],
    "자격증": ["certificate diploma", "achievement award", "professional certification", "graduation success"],
    "공무원": ["government building", "public service office", "official work desk", "administrative office"],

    # 트렌드/기타
    "트렌드": ["trending popular culture", "modern lifestyle", "contemporary style", "viral content"],
    "키스": ["romantic couple", "love relationship", "romance drama", "couple happiness"],
}

# 카테고리별 기본 검색어 (키워드 매핑 없을 때 폴백)
CATEGORY_DEFAULT_KEYWORDS = {
    "재테크": ["money finance chart", "investment success", "financial planning office", "business growth"],
    "IT테크": ["technology gadget modern", "digital device screen", "innovation tech", "smart technology"],
    "연예": ["entertainment stage lights", "celebrity event red carpet", "award ceremony", "performance show"],
    "건강": ["health wellness nature", "fitness lifestyle", "healthy living outdoor", "wellness routine"],
    "생활정보": ["daily life tips", "home organization", "practical advice", "lifestyle modern"],
    "취업교육": ["career success office", "education learning", "professional growth", "job interview"],
    "트렌드": ["trending popular", "modern culture", "contemporary lifestyle", "viral content"]
}


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

    def get_image_count_for_category(self, category_name: str) -> int:
        """
        카테고리별 이미지 개수 반환

        Args:
            category_name: 카테고리 이름

        Returns:
            이미지 개수 (기본값 4)
        """
        categories = self.categories_config.get("categories", {})
        category_info = categories.get(category_name, {})
        return category_info.get("image_count", 4)

    def get_search_keywords_for_topic(self, keyword: str, category_name: str = None) -> list[str]:
        """
        키워드에 맞는 영문 검색어 리스트 반환

        Args:
            keyword: 한글 키워드
            category_name: 카테고리 이름 (폴백용)

        Returns:
            영문 검색어 리스트
        """
        # 1순위: 키워드 직접 매핑
        for ko_key, en_keywords in IMAGE_KEYWORD_MAPPING.items():
            if ko_key in keyword:
                logger.info(f"Keyword mapping found: '{keyword}' matches '{ko_key}'")
                return en_keywords

        # 2순위: 카테고리 기본 검색어
        if category_name and category_name in CATEGORY_DEFAULT_KEYWORDS:
            logger.info(f"Using category default: {category_name}")
            return CATEGORY_DEFAULT_KEYWORDS[category_name]

        # 3순위: 최종 폴백
        return ["lifestyle modern", "success achievement", "professional business", "technology innovation"]

    def search_images(
        self,
        keyword: str,
        count: int = 4,
        orientation: str = "landscape",
        category_name: str = None
    ) -> list[PexelsImage]:
        """
        Pexels에서 키워드에 맞는 이미지 검색 (중복 방지 포함)

        Args:
            keyword: 검색 키워드
            count: 반환할 이미지 수
            orientation: 이미지 방향 (landscape, portrait, square)
            category_name: 카테고리 이름 (폴백용)

        Returns:
            PexelsImage 리스트
        """
        if not self.api_key:
            logger.warning("Pexels API key not configured")
            return []

        try:
            # 키워드에 맞는 검색어 가져오기
            search_keywords = self.get_search_keywords_for_topic(keyword, category_name)
            print(f"🖼️ 이미지 검색어: '{keyword}' → {search_keywords}")

            images = []
            used_urls = set()  # 중복 방지용

            # 각 검색어로 이미지 검색
            for i, search_term in enumerate(search_keywords[:count]):
                params = {
                    "query": search_term,
                    "per_page": 10,  # 여러 결과 중 랜덤 선택
                    "orientation": orientation,
                    "size": "medium"
                }

                print(f"  └─ Pexels 검색: {search_term}")
                logger.info(f"Searching Pexels: {search_term}")

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
                    # 중복 제외하고 랜덤 선택
                    available = [p for p in photos if p.get("src", {}).get("medium", "") not in used_urls]

                    if available:
                        # 랜덤으로 선택
                        photo = random.choice(available)
                        img_url = photo.get("src", {}).get("medium", "")
                        if not img_url:
                            img_url = photo.get("src", {}).get("large", "")

                        print(f"      ✓ {img_url[:60]}...")

                        image = PexelsImage(
                            id=photo.get("id"),
                            url=img_url,
                            photographer=photo.get("photographer", ""),
                            alt=photo.get("alt", keyword),
                            width=photo.get("width", 800),
                            height=photo.get("height", 600)
                        )
                        images.append(image)
                        used_urls.add(img_url)

                if len(images) >= count:
                    break

            logger.info(f"Found {len(images)} unique images for: {keyword}")
            return images

        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching images: {e}")
            return []

    def search_images_for_category(
        self,
        keyword: str,
        category_name: str,
        count: int = None
    ) -> list[PexelsImage]:
        """
        카테고리에 맞는 이미지 검색 (키워드 매핑 우선)

        Args:
            keyword: 블로그 키워드
            category_name: 카테고리 이름 (재테크, IT테크 등)
            count: 필요한 이미지 수 (None이면 카테고리 설정 사용)

        Returns:
            PexelsImage 리스트
        """
        # 카테고리별 이미지 개수 적용
        if count is None:
            count = self.get_image_count_for_category(category_name)

        return self.search_images(
            keyword=keyword,
            count=count,
            category_name=category_name
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

    def verify_image_url(self, url: str) -> bool:
        """
        이미지 URL이 유효한지 검증

        Args:
            url: 검증할 이미지 URL

        Returns:
            URL이 유효하면 True
        """
        if not url or not url.startswith('http'):
            return False

        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    return True
            # HEAD 실패 시 GET으로 재시도 (일부 서버는 HEAD 미지원)
            response = requests.get(url, timeout=10, stream=True)
            response.close()
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"URL verification failed for {url[:50]}...: {e}")
            return False

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

    # =========================================================================
    # AI 기반 컨텍스트 이미지 검색 메서드
    # =========================================================================

    def extract_image_contexts(self, content: str) -> list:
        """
        글에서 이미지 컨텍스트 추출

        Args:
            content: HTML 콘텐츠

        Returns:
            이미지 위치와 컨텍스트 리스트
        """
        contexts = []

        # 1순위: IMG_CONTEXT 주석 사용
        pattern = r'<!-- IMG_CONTEXT: (.+?) -->\s*\[IMAGE_(\d+)\]'
        matches = re.findall(pattern, content)

        if matches:
            for context, num in matches:
                contexts.append({
                    'position': int(num),
                    'context': context.strip(),
                    'source': 'comment'
                })
            logger.info(f"Found {len(contexts)} IMG_CONTEXT comments")
        else:
            # 2순위: [IMAGE] 주변 텍스트 추출 (앞 200자)
            pattern = r'(.{50,300}?)\[IMAGE_(\d+)\]'
            matches = re.findall(pattern, content, re.DOTALL)

            for surrounding_text, num in matches:
                # HTML 태그 제거하고 텍스트만 추출
                clean_text = re.sub(r'<[^>]+>', ' ', surrounding_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                contexts.append({
                    'position': int(num),
                    'context': clean_text[-200:],  # 마지막 200자
                    'source': 'surrounding'
                })
            logger.info(f"Extracted {len(contexts)} contexts from surrounding text")

        # 정렬
        contexts.sort(key=lambda x: x['position'])
        return contexts

    def generate_image_search_query(self, context: str, keyword: str) -> str:
        """
        AI로 이미지 검색어 생성

        Args:
            context: 섹션 컨텍스트 (IMG_CONTEXT 또는 주변 텍스트)
            keyword: 블로그 키워드

        Returns:
            영문 이미지 검색어
        """
        try:
            client = anthropic.Anthropic(api_key=settings.claude_api_key)

            prompt = f"""다음 블로그 글의 한 섹션입니다. 이 내용에 어울리는 Pexels 이미지 검색어를 영문으로 1개만 추천해주세요.

[블로그 주제]: {keyword}
[섹션 내용]: {context}

규칙:
1. 영문 검색어만 출력 (2~4단어)
2. 실제 인물/연예인 이름 절대 포함 금지
3. Pexels에서 검색 가능한 일반적인 이미지 키워드
4. 추상적인 개념보다 구체적인 사물/장면
5. 검색어만 출력, 다른 설명 없이

예시 출력:
cryptocurrency trading chart
office desk documents
fitness workout gym
smartphone technology modern"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )

            search_query = response.content[0].text.strip()

            # 안전 검증
            if re.search(r'[가-힣]', search_query) or len(search_query) > 50:
                logger.warning(f"Invalid AI query: {search_query}, using fallback")
                return self._get_fallback_query(keyword)

            # 줄바꿈이나 여러 줄이면 첫 줄만
            search_query = search_query.split('\n')[0].strip()

            logger.info(f"AI generated query: '{search_query}'")
            return search_query

        except Exception as e:
            logger.error(f"AI query generation failed: {e}")
            return self._get_fallback_query(keyword)

    def _get_fallback_query(self, keyword: str) -> str:
        """폴백 검색어 반환"""
        # 기존 키워드 매핑에서 찾기
        for ko_key, en_keywords in IMAGE_KEYWORD_MAPPING.items():
            if ko_key in keyword:
                return random.choice(en_keywords)
        return "modern lifestyle professional"

    def search_pexels_single(self, query: str, per_page: int = 5) -> list:
        """
        Pexels 단일 검색어로 이미지 검색

        Args:
            query: 영문 검색어
            per_page: 결과 개수

        Returns:
            Pexels API 응답의 photos 리스트
        """
        if not self.api_key:
            return []

        try:
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",
                "size": "medium"
            }

            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return data.get("photos", [])

        except Exception as e:
            logger.error(f"Pexels search failed for '{query}': {e}")
            return []

    def fetch_contextual_images(self, content: str, keyword: str) -> dict:
        """
        글 내용 분석 후 맥락에 맞는 이미지 가져오기

        Args:
            content: HTML 콘텐츠
            keyword: 블로그 키워드

        Returns:
            {IMAGE_1: {url, alt, caption, search_query}, ...} 딕셔너리
        """
        print(f"\n🤖 AI 기반 이미지 검색 시작: '{keyword}'")

        contexts = self.extract_image_contexts(content)
        images = {}
        used_urls = set()

        if not contexts:
            logger.warning("No image contexts found, using fallback")
            # 폴백: 기존 방식 사용
            return self._fallback_images(keyword, count=4)

        for ctx in contexts:
            position = ctx['position']
            context_text = ctx['context']

            # AI로 검색어 생성
            if ctx['source'] == 'comment':
                # IMG_CONTEXT 주석은 이미 영문일 가능성이 높음
                search_query = context_text if self._is_english(context_text) else self.generate_image_search_query(context_text, keyword)
            else:
                search_query = self.generate_image_search_query(context_text, keyword)

            print(f"  🖼️ IMAGE_{position}: {search_query}")

            # Pexels 검색
            photos = self.search_pexels_single(search_query, per_page=8)

            if photos:
                # 미사용 이미지 중 랜덤 선택
                for photo in photos:
                    img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                    if img_url and img_url not in used_urls:
                        images[f"IMAGE_{position}"] = {
                            'url': img_url,
                            'alt': f"{keyword} 관련 이미지",
                            'photographer': photo.get('photographer', 'Unknown'),
                            'search_query': search_query
                        }
                        used_urls.add(img_url)
                        print(f"      ✓ {img_url[:50]}...")
                        break

            # 결과 없으면 폴백 검색
            if f"IMAGE_{position}" not in images:
                fallback_query = self._get_fallback_query(keyword)
                print(f"      ⚠️ 폴백 검색: {fallback_query}")
                fallback_photos = self.search_pexels_single(fallback_query, per_page=5)

                if fallback_photos:
                    for photo in fallback_photos:
                        img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                        if img_url and img_url not in used_urls:
                            images[f"IMAGE_{position}"] = {
                                'url': img_url,
                                'alt': f"{keyword} 관련 이미지",
                                'photographer': photo.get('photographer', 'Unknown'),
                                'search_query': f"fallback: {fallback_query}"
                            }
                            used_urls.add(img_url)
                            break

        print(f"  📸 총 {len(images)}개 이미지 확보\n")
        return images

    def _is_english(self, text: str) -> bool:
        """텍스트가 영문인지 확인"""
        return not bool(re.search(r'[가-힣]', text))

    def _fallback_images(self, keyword: str, count: int = 4) -> dict:
        """폴백 이미지 검색"""
        images = {}
        used_urls = set()
        search_keywords = self.get_search_keywords_for_topic(keyword)

        for i in range(1, count + 1):
            query = search_keywords[(i - 1) % len(search_keywords)]
            photos = self.search_pexels_single(query, per_page=5)

            if photos:
                for photo in photos:
                    img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                    if img_url and img_url not in used_urls:
                        images[f"IMAGE_{i}"] = {
                            'url': img_url,
                            'alt': f"{keyword} 관련 이미지",
                            'photographer': photo.get('photographer', 'Unknown'),
                            'search_query': query
                        }
                        used_urls.add(img_url)
                        break

        return images

    # =========================================================================
    # Phase 3: 혼합 이미지 시스템 (Puppeteer 스크린샷 + Pexels)
    # =========================================================================

    def upload_to_wordpress_media(self, local_path: str, alt_text: str = None) -> Optional[str]:
        """
        로컬 이미지를 워드프레스 미디어에 업로드

        Args:
            local_path: 로컬 파일 경로
            alt_text: 대체 텍스트

        Returns:
            업로드된 이미지 URL 또는 None
        """
        import os
        import base64

        if not os.path.exists(local_path):
            logger.warning(f"Local file not found: {local_path}")
            return None

        try:
            # 인증 헤더
            credentials = f"{settings.wp_user}:{settings.wp_app_password}"
            token = base64.b64encode(credentials.encode()).decode('utf-8')

            headers = {
                'Authorization': f'Basic {token}',
                'Content-Disposition': f'attachment; filename={os.path.basename(local_path)}',
                'Content-Type': 'image/png'
            }

            with open(local_path, 'rb') as img_file:
                response = requests.post(
                    f"{settings.wp_url}/wp-json/wp/v2/media",
                    headers=headers,
                    data=img_file,
                    timeout=60
                )

            if response.status_code == 201:
                media_url = response.json().get('source_url')
                logger.info(f"WordPress upload success: {media_url}")
                print(f"✅ 워드프레스 업로드 완료: {media_url[:50]}...")

                # 업로드된 URL 검증
                if self.verify_image_url(media_url):
                    return media_url
                else:
                    logger.warning(f"Uploaded URL verification failed: {media_url}")
                    print(f"⚠️ 업로드된 이미지 URL 접근 불가, 재시도 필요")
                    return None
            else:
                logger.warning(f"WordPress upload failed: {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return None

    def _capture_dynamic_screenshot(self, url: str, site_name: str, overlay_text: str) -> Optional[str]:
        """
        AI가 추천한 동적 URL로 스크린샷 캡쳐

        Args:
            url: 스크린샷할 URL
            site_name: 사이트 이름
            overlay_text: 오버레이 텍스트

        Returns:
            스크린샷 파일 경로 또는 None
        """
        import subprocess
        import os
        import random

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = random.randint(1000, 9999)
        output_path = f"temp_screenshots/ai_screenshot_{timestamp}_{random_suffix}.png"

        # 디렉토리 확인
        os.makedirs("temp_screenshots", exist_ok=True)

        script_path = Path(__file__).resolve().parent / "screenshot_generator.js"

        cmd = [
            'node', str(script_path),
            '--url', url,
            '--output', output_path,
            '--text', overlay_text
        ]

        try:
            print(f"  📸 동적 스크린샷 캡쳐 중: {url[:50]}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path(__file__).resolve().parent.parent)
            )

            if result.returncode == 0:
                # 출력에서 최종 파일 경로 추출
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('RESULT:'):
                        final_path = line.replace('RESULT:', '').strip()
                        if final_path != 'FAILED' and os.path.exists(final_path):
                            logger.info(f"Dynamic screenshot captured: {final_path}")
                            return final_path

                # RESULT 없이 output_path가 존재하면 사용
                if os.path.exists(output_path):
                    logger.info(f"Dynamic screenshot captured: {output_path}")
                    return output_path

                # 오버레이 버전 확인
                overlay_path = output_path.replace('.png', '_overlay.png')
                if os.path.exists(overlay_path):
                    logger.info(f"Dynamic screenshot with overlay: {overlay_path}")
                    return overlay_path

            logger.warning(f"Dynamic screenshot failed: {result.stderr[:200]}")
            return None

        except subprocess.TimeoutExpired:
            logger.warning("Dynamic screenshot timeout (60s)")
            return None
        except FileNotFoundError:
            logger.warning("Node.js not installed or script not found")
            return None
        except Exception as e:
            logger.error(f"Dynamic screenshot error: {e}")
            return None

    def fetch_mixed_images(
        self,
        content: str,
        keyword: str,
        category: str,
        count: int = 4
    ) -> dict:
        """
        AI 판단 기반 Pexels + 스크린샷 혼합 이미지 가져오기

        1. AI가 스크린샷 필요 여부 및 URL 동적 추천
        2. 나머지는 AI 기반 Pexels 검색

        Args:
            content: HTML 콘텐츠 (IMG_CONTEXT 추출용)
            keyword: 블로그 키워드
            category: 카테고리 이름
            count: 필요한 이미지 수

        Returns:
            {IMAGE_1: {url, alt, ...}, ...} 딕셔너리
        """
        print(f"\n🖼️ AI 기반 이미지 시스템 시작: '{keyword}' (카테고리: {category})")

        images = {}
        used_urls = set()
        screenshot_used = False

        # 오래된 스크린샷 정리
        cleanup_old_screenshots()

        # 1. AI에게 스크린샷 필요 여부 질문
        screenshot_rec = get_screenshot_recommendation(keyword, category)

        if screenshot_rec.get("need_screenshot"):
            url = screenshot_rec.get("url")
            site_name = screenshot_rec.get("site_name", keyword)

            # URL 검증
            if url and validate_screenshot_url(url):
                print(f"  📸 AI 추천 URL로 스크린샷 시도: {url}")
                overlay_text = f"{site_name} ({datetime.now().strftime('%Y.%m.%d')})"

                # 동적 URL 스크린샷 캡쳐
                screenshot_path = self._capture_dynamic_screenshot(url, site_name, overlay_text)

                if screenshot_path:
                    # 워드프레스에 업로드
                    uploaded_url = self.upload_to_wordpress_media(
                        screenshot_path,
                        alt_text=f"{keyword} 실시간 정보"
                    )

                    if uploaded_url:
                        images["IMAGE_1"] = {
                            'url': uploaded_url,
                            'alt': f"{keyword} 실시간 정보",
                            'photographer': "자동 캡쳐",
                            'search_query': f"screenshot: {url}",
                            'type': 'screenshot',
                            'site_name': site_name
                        }
                        used_urls.add(uploaded_url)
                        screenshot_used = True
                        print(f"  ✅ AI 추천 스크린샷 추가 (IMAGE_1)")
                    else:
                        print(f"  ⚠️ 워드프레스 업로드 실패, Pexels로 대체")
                else:
                    print(f"  ⚠️ 스크린샷 생성 실패, 폴백 시도")

                    # 폴백: 기존 키워드 기반 스크린샷
                    if should_use_screenshot(keyword, category):
                        fallback_path = generate_unique_screenshot(
                            keyword,
                            f"{keyword} 최신 정보 ({datetime.now().strftime('%Y.%m.%d')})"
                        )
                        if fallback_path:
                            uploaded_url = self.upload_to_wordpress_media(
                                fallback_path,
                                alt_text=f"{keyword} 실시간 정보"
                            )
                            if uploaded_url:
                                images["IMAGE_1"] = {
                                    'url': uploaded_url,
                                    'alt': f"{keyword} 실시간 정보",
                                    'photographer': "자동 캡쳐",
                                    'search_query': f"screenshot: {keyword}",
                                    'type': 'screenshot'
                                }
                                used_urls.add(uploaded_url)
                                screenshot_used = True
                                print(f"  ✅ 폴백 스크린샷 추가 (IMAGE_1)")
            else:
                print(f"  ⚠️ URL 검증 실패: {url}, 폴백 시도")

                # 폴백 URL 확인
                fallback = get_fallback_url(keyword)
                if fallback.get("url"):
                    print(f"  🔄 폴백 URL 사용: {fallback['url']}")
                    fallback_path = generate_unique_screenshot(
                        keyword,
                        f"{keyword} 최신 정보 ({datetime.now().strftime('%Y.%m.%d')})"
                    )
                    if fallback_path:
                        uploaded_url = self.upload_to_wordpress_media(
                            fallback_path,
                            alt_text=f"{keyword} 실시간 정보"
                        )
                        if uploaded_url:
                            images["IMAGE_1"] = {
                                'url': uploaded_url,
                                'alt': f"{keyword} 실시간 정보",
                                'photographer': "자동 캡쳐",
                                'search_query': f"screenshot: {keyword}",
                                'type': 'screenshot'
                            }
                            used_urls.add(uploaded_url)
                            screenshot_used = True
                            print(f"  ✅ 폴백 스크린샷 추가 (IMAGE_1)")
        else:
            print(f"  ℹ️ AI 판단: 스크린샷 불필요 → Pexels만 사용")

        # 2. 나머지: AI 기반 Pexels 이미지
        # 이미지 컨텍스트 추출
        contexts = self.extract_image_contexts(content)
        start_index = 2 if screenshot_used else 1

        # 컨텍스트가 있으면 컨텍스트 기반으로 검색
        if contexts:
            for ctx in contexts:
                position = ctx['position']

                # 스크린샷으로 이미 채워진 경우 스킵
                if f"IMAGE_{position}" in images:
                    continue

                context_text = ctx['context']

                # AI로 검색어 생성
                if ctx['source'] == 'comment':
                    search_query = context_text if self._is_english(context_text) else self.generate_image_search_query(context_text, keyword)
                else:
                    search_query = self.generate_image_search_query(context_text, keyword)

                print(f"  🖼️ IMAGE_{position}: {search_query}")

                # Pexels 검색
                photos = self.search_pexels_single(search_query, per_page=8)

                if photos:
                    for photo in photos:
                        img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                        if img_url and img_url not in used_urls:
                            images[f"IMAGE_{position}"] = {
                                'url': img_url,
                                'alt': f"{keyword} 관련 이미지",
                                'photographer': photo.get('photographer', 'Unknown'),
                                'search_query': search_query,
                                'type': 'pexels'
                            }
                            used_urls.add(img_url)
                            print(f"      ✓ {img_url[:50]}...")
                            break

                # 결과 없으면 폴백
                if f"IMAGE_{position}" not in images:
                    fallback_query = self._get_fallback_query(keyword)
                    print(f"      ⚠️ 폴백 검색: {fallback_query}")
                    fallback_photos = self.search_pexels_single(fallback_query, per_page=5)

                    if fallback_photos:
                        for photo in fallback_photos:
                            img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                            if img_url and img_url not in used_urls:
                                images[f"IMAGE_{position}"] = {
                                    'url': img_url,
                                    'alt': f"{keyword} 관련 이미지",
                                    'photographer': photo.get('photographer', 'Unknown'),
                                    'search_query': f"fallback: {fallback_query}",
                                    'type': 'pexels'
                                }
                                used_urls.add(img_url)
                                break

        # 3. 컨텍스트가 없거나 이미지가 부족하면 기본 검색으로 채우기
        remaining_count = count - len(images)
        if remaining_count > 0:
            print(f"  🔍 추가 Pexels 이미지 {remaining_count}개 검색 중...")
            search_keywords = self.get_search_keywords_for_topic(keyword)

            for i in range(remaining_count):
                # 다음 이미지 번호 결정
                next_position = start_index + i
                while f"IMAGE_{next_position}" in images:
                    next_position += 1

                query = search_keywords[i % len(search_keywords)]
                print(f"  🖼️ IMAGE_{next_position}: {query}")

                photos = self.search_pexels_single(query, per_page=8)

                if photos:
                    for photo in photos:
                        img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
                        if img_url and img_url not in used_urls:
                            images[f"IMAGE_{next_position}"] = {
                                'url': img_url,
                                'alt': f"{keyword} 관련 이미지",
                                'photographer': photo.get('photographer', 'Unknown'),
                                'search_query': query,
                                'type': 'pexels'
                            }
                            used_urls.add(img_url)
                            print(f"      ✓ {img_url[:50]}...")
                            break

        # 통계
        screenshot_count = sum(1 for img in images.values() if img.get('type') == 'screenshot')
        pexels_count = sum(1 for img in images.values() if img.get('type') == 'pexels')
        print(f"\n  📊 이미지 통계: 총 {len(images)}개 (스크린샷: {screenshot_count}, Pexels: {pexels_count})")

        return images


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
