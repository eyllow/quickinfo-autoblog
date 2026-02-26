"""Claude AI 콘텐츠 생성기 - 카테고리별 고품질 블로그 글 생성"""
import json
import logging
import re
import uuid
from typing import Optional, List
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# AI 메타 응답 제거 패턴
AI_META_PATTERNS = [
    r"^.*?제공해주신.*?작성하겠습니다\.?\s*",
    r"^.*?가이드라인.*?따라.*?작성.*?\s*",
    r"^.*?HTML 문서를 작성.*?\s*",
    r"^.*?아래.*?구조로.*?작성.*?\s*",
    r"^.*?말씀하신.*?대로.*?\s*",
    r"^.*?요청하신.*?내용.*?\s*",
    r"^.*?블로그 글을 작성해.*?\s*",
    r"^.*?다음과 같이.*?작성.*?\s*",
]


def clean_ai_response(content: str) -> str:
    """
    AI 메타 응답 제거

    Args:
        content: AI가 생성한 콘텐츠

    Returns:
        정리된 콘텐츠
    """
    # 메타 패턴 제거
    for pattern in AI_META_PATTERNS:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)

    # HTML 태그로 시작하도록 정리
    # <div, <h2, <p 등으로 시작하는 부분 찾기
    html_start = re.search(r'<(?:div|h[1-6]|p|section)', content, re.IGNORECASE)
    if html_start:
        content = content[html_start.start():]

    # 앞뒤 공백 정리
    content = content.strip()

    return content


def clean_html_styles(html_content: str) -> str:
    """
    발행 전 불필요한 스타일 제거 (왼쪽 검은 라인 등)

    WordPress에서 blockquote/border-left 스타일이
    왼쪽 검은 라인으로 표시되는 문제 해결

    Args:
        html_content: HTML 콘텐츠

    Returns:
        정리된 HTML 콘텐츠
    """
    # blockquote 태그를 일반 div로 변환
    html_content = re.sub(
        r'<blockquote[^>]*>',
        '<div class="info-box">',
        html_content
    )
    html_content = html_content.replace('</blockquote>', '</div>')

    # border-left 인라인 스타일 제거 (강조 박스의 4px solid 색상은 유지)
    # 강조 박스용 border-left (4px solid #색상)는 보존하고 나머지만 제거
    html_content = re.sub(
        r'border-left:\s*(?!4px\s+solid\s+#)[^;"]+;?',
        '',
        html_content,
        flags=re.IGNORECASE
    )

    # border-l-* Tailwind 클래스 제거
    html_content = re.sub(
        r'\bborder-l-\d+\b',
        '',
        html_content
    )

    # border: 스타일에서 왼쪽만 있는 경우 제거
    html_content = re.sub(
        r'border:\s*\d+px\s+solid\s+[^;"]+\s*;\s*border-(?:right|top|bottom):\s*none\s*;',
        '',
        html_content,
        flags=re.IGNORECASE
    )

    # 빈 style 속성 정리
    html_content = re.sub(r'\s*style="\s*"', '', html_content)

    return html_content

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings
from utils.image_fetcher import ImageFetcher
from utils.google_sheets import get_coupang_products
from utils.product_matcher import match_products_for_content, generate_product_html
from utils.web_search import GoogleSearcher
from utils.humanizer import humanize_full
from .prompts import (
    SYSTEM_PROMPT,
    STRUCTURE_PROMPT,
    get_title_prompt,
    CATEGORY_TEMPLATES,
    get_template,
    OFFICIAL_BUTTON_TEMPLATE,
    get_card_colors,
    COUPANG_BUTTON_TEMPLATE,
    COUPANG_DISCLAIMER,
    HEALTH_DISCLAIMER,
    AFFILIATE_NOTICE,
    CATEGORY_BADGE_TEMPLATE,
    PROFESSIONAL_PERSONA,
    post_process_content,
)
from .template_prompts import generate_template_prompt, get_template_info_log, PERSON_TITLE_PROMPT
from generators.humanizer import humanize_content
from media.link_matcher import insert_related_links

logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_DIR = Path(settings.config_dir)

# 쿠팡 제외 키워드 (금융/투자 관련 - 카테고리 설정과 무관하게 항상 제외)
COUPANG_EXCLUDE_KEYWORDS = [
    "비트코인", "이더리움", "코인", "암호화폐", "가상화폐", "블록체인",
    "주식", "투자", "펀드", "ETF", "배당", "증권",
    "대출", "금리", "환율", "외환",
    "연말정산", "세금", "환급",
]

# 쿠팡 제외 카테고리
COUPANG_EXCLUDE_CATEGORIES = ["연예", "트렌드", "재테크", "취업교육"]


def is_person_keyword(keyword: str) -> bool:
    """
    인물 키워드인지 판단

    Args:
        keyword: 검사할 키워드

    Returns:
        인물 키워드 여부
    """
    # 1. 한글 이름 패턴 (2-4글자, 성+이름)
    korean_name_pattern = r'^[가-힣]{2,4}$'
    if re.match(korean_name_pattern, keyword):
        # 일반 명사 제외 (키워드가 일반 단어일 가능성)
        common_words = [
            "연말정산", "비트코인", "이더리움", "주식", "부동산", "아파트",
            "날씨", "환율", "금리", "대출", "보험", "연금", "청약",
            "다이어트", "건강", "운동", "여행", "맛집", "카페",
            "자동차", "스마트폰", "노트북", "게임", "영화", "드라마"
        ]
        if keyword in common_words:
            return False
        return True

    # 2. 인물 관련 직함/직업 포함 여부
    person_indicators = [
        "선수", "배우", "가수", "사장", "대표", "의원", "장관", "감독",
        "교수", "작가", "감독", "아나운서", "MC", "코치", "회장",
        "총장", "원장", "소장", "부장", "차장", "과장"
    ]
    for indicator in person_indicators:
        if indicator in keyword:
            return True

    # 3. 유명인 이름 패턴 (영문 포함)
    celebrity_patterns = [
        # 연예인
        "손흥민", "BTS", "블랙핑크", "뉴진스", "아이브", "에스파",
        "박보검", "송혜교", "김수현", "이민호", "전지현", "수지",
        "아이유", "임영웅", "박서준", "정해인", "차은우",
        # 스포츠
        "이강인", "김민재", "황희찬", "오타니",
        # 정치인
        "윤석열", "이재명", "한동훈",
    ]
    for celeb in celebrity_patterns:
        if celeb in keyword or keyword in celeb:
            return True

    return False


@dataclass
class Section:
    """섹션 데이터"""
    id: str
    index: int
    type: str  # heading, image, paragraph, list, table, quote
    html: str


@dataclass
class GeneratedPost:
    """생성된 포스트 데이터"""
    title: str
    content: str
    excerpt: str
    category: str
    template: str
    has_coupang: bool = False
    sources: list = None  # 웹검색 출처 목록
    sections: List[Section] = field(default_factory=list)  # 섹션 배열

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.sections is None:
            self.sections = []

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (API 응답용)"""
        return {
            "title": self.title,
            "content": self.content,
            "excerpt": self.excerpt,
            "category": self.category,
            "template": self.template,
            "has_coupang": self.has_coupang,
            "sources": self.sources,
            "sections": [
                {"id": s.id, "index": s.index, "type": s.type, "html": s.html}
                for s in self.sections
            ]
        }


class ContentGenerator:
    """Claude AI를 사용한 카테고리별 고품질 콘텐츠 생성기"""

    def __init__(self):
        self.ai_provider = settings.ai_provider.lower()
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model

        # Gemini 초기화
        if self.ai_provider == "gemini" and HAS_GEMINI:
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(settings.gemini_model)
                logger.info(f"AI Provider: Gemini ({settings.gemini_model})")
            else:
                logger.warning("Gemini selected but GOOGLE_API_KEY not set, falling back to Claude")
                self.ai_provider = "claude"
        elif self.ai_provider == "gemini" and not HAS_GEMINI:
            logger.warning("google-generativeai not installed, falling back to Claude")
            self.ai_provider = "claude"

        if self.ai_provider == "claude":
            logger.info(f"AI Provider: Claude ({self.model})")
        self.coupang_id = settings.coupang_partner_id
        self.image_fetcher = ImageFetcher()
        self.web_searcher = GoogleSearcher()

        # 트렌드 맥락 수집용 크롤러
        from crawlers.google_trends import GoogleTrendsCrawler
        self.trend_crawler = GoogleTrendsCrawler()

        # 설정 파일 로드
        self.categories_config = self._load_json("categories.json")
        self.official_links = self._load_json("official_links.json")
        self.coupang_links = self._load_json("coupang_links.json")
        self.coupang_defaults = self._load_json("coupang_defaults.json")
        self.evergreen_config = self._load_json("evergreen_keywords.json")

    def _load_json(self, filename: str) -> dict:
        """JSON 설정 파일 로드"""
        try:
            filepath = CONFIG_DIR / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {filename}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing {filename}: {e}")
            return {}

    def is_evergreen_keyword(self, keyword: str) -> bool:
        """
        에버그린 키워드인지 확인

        Args:
            keyword: 검사할 키워드

        Returns:
            에버그린 키워드 여부
        """
        detection_keywords = self.evergreen_config.get("detection_keywords", [])

        for eg_keyword in detection_keywords:
            if eg_keyword.lower() in keyword.lower():
                logger.info(f"Evergreen keyword detected: '{keyword}' matches '{eg_keyword}'")
                return True

        return False

    def get_trend_context(self, keyword: str) -> str:
        """
        키워드의 트렌드 맥락 수집 (왜 지금 이 키워드가 화제인지)

        Args:
            keyword: 검색 키워드

        Returns:
            트렌드 맥락 문자열 (프롬프트에 삽입용)
        """
        try:
            context = self.trend_crawler.get_trend_context(keyword)

            if context.get("news_titles"):
                news_list = '\n'.join([f'- {title}' for title in context['news_titles'][:5]])
                return f"""
[트렌드 배경 - 이 키워드가 지금 화제인 이유]
{news_list}

중요: 위 뉴스 내용을 반영하여 "왜 지금 이 키워드가 뜨는지" 설명해주세요.
단순한 일반론이 아닌, 현재 상황에 맞는 시의성 있는 내용을 작성해주세요.
"""
            return ""

        except Exception as e:
            logger.warning(f"트렌드 맥락 수집 실패: {e}")
            return ""

    def _call_claude(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 8000,
        use_persona: bool = True
    ) -> str:
        """
        Claude API 호출

        Args:
            user_prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            use_persona: 전문가 페르소나 프롬프트 사용 여부

        Returns:
            Claude 응답 텍스트
        """
        try:
            # 전문가 페르소나 프롬프트 추가 (AdSense 최적화)
            if use_persona:
                full_system_prompt = PROFESSIONAL_PERSONA + "\n\n" + system_prompt
            else:
                full_system_prompt = system_prompt

            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=full_system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            raise

    def _call_gemini(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 8000,
        use_persona: bool = True
    ) -> str:
        """Gemini API 호출"""
        try:
            if use_persona:
                full_prompt = PROFESSIONAL_PERSONA + "\n\n" + system_prompt + "\n\n" + user_prompt
            else:
                full_prompt = system_prompt + "\n\n" + user_prompt

            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def _call_ai(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 8000,
        use_persona: bool = True
    ) -> str:
        """통합 AI 호출 - ai_provider 설정에 따라 Claude/Gemini 선택"""
        if self.ai_provider == "gemini":
            return self._call_gemini(user_prompt, system_prompt, max_tokens, use_persona)
        return self._call_claude(user_prompt, system_prompt, max_tokens, use_persona)

    def classify_category(self, keyword: str) -> tuple[str, dict]:
        """
        키워드 기반 카테고리 자동 분류

        Returns:
            (카테고리명, 카테고리 설정) 튜플
        """
        categories = self.categories_config.get("categories", {})

        best_match = "트렌드"
        best_priority = 999
        best_config = categories.get("트렌드", {})

        for category_name, config in categories.items():
            if config.get("is_default"):
                continue

            keywords = config.get("keywords", [])
            priority = config.get("priority", 99)

            for kw in keywords:
                if kw.lower() in keyword.lower() and priority < best_priority:
                    best_match = category_name
                    best_priority = priority
                    best_config = config
                    break

        logger.info(f"Category classified: '{keyword}' -> {best_match} (template: {best_config.get('template', 'trend')})")
        return best_match, best_config

    def generate_title(self, keyword: str, news_data: str = "", is_person: bool = False) -> str:
        """
        블로그 제목 생성

        Args:
            keyword: 키워드
            news_data: 뉴스/웹검색 데이터 (인물 키워드용)
            is_person: 인물 키워드 여부

        Returns:
            생성된 제목
        """
        if is_person and news_data:
            # 인물 전용 제목 프롬프트 사용
            prompt = PERSON_TITLE_PROMPT.format(
                keyword=keyword,
                news_summary=news_data[:800]  # 뉴스 요약 전달
            )
            logger.info(f"Using person title prompt for: {keyword}")
        else:
            # 기존 제목 프롬프트
            prompt = get_title_prompt(keyword)

        # 제목 생성에는 페르소나 미사용
        title = self._call_ai(prompt, max_tokens=200, use_persona=False)
        title = title.strip().strip('"\'')
        
        # Gemini 제목 잘림 보정: 제목이 너무 짧으면 키워드 기반 재생성
        if len(title) < 15:
            logger.warning(f"Title too short ({len(title)} chars): '{title}', regenerating...")
            fallback_prompt = f"'{keyword}'에 대한 블로그 글 제목을 40자 이내로 작성하세요. 제목만 한 줄로 출력하세요."
            title = self._call_ai(fallback_prompt, max_tokens=100, use_persona=False)
            title = title.strip().strip('"\'')
            # 여전히 짧으면 키워드 직접 활용
            if len(title) < 15:
                title = f"{keyword}, 꼭 알아야 할 핵심 정보"
        
        # 제목 중복 단어 제거 (예: "총정리 총정리" → "총정리")
        import re as _re
        title = _re.sub(r'(\S+)\s+\1', r'\1', title)
        
        return title

    def perform_web_search(self, keyword: str) -> dict:
        """
        트렌드 키워드에 대해 웹검색 수행

        Args:
            keyword: 검색 키워드

        Returns:
            웹검색 결과 딕셔너리
        """
        if not self.web_searcher.is_configured():
            logger.warning("Google Search API not configured - skipping web search")
            return {"keyword": keyword, "sources": [], "content": ""}

        logger.info(f"Performing web search for: {keyword}")
        result = self.web_searcher.search_and_crawl(keyword, num_results=5)

        if result.get("sources"):
            logger.info(f"  Found {len(result['sources'])} sources")
            for src in result['sources'][:3]:
                logger.info(f"    - {src['title'][:40]}...")
        else:
            logger.warning(f"  No web search results found")

        return result

    def generate_content_with_template(
        self,
        keyword: str,
        news_data: str,
        template_name: str,
        category_name: str = "트렌드",
        is_evergreen: bool = False,
        web_data: dict = None,
        trend_context: str = ""
    ) -> tuple[str, list, dict]:
        """
        템플릿 다양화 시스템으로 본문 생성 (저품질 방지)

        Args:
            keyword: 키워드
            news_data: 뉴스 데이터
            template_name: 기존 템플릿 이름 (호환용, 실제 사용 안 함)
            category_name: 카테고리명
            is_evergreen: 에버그린 콘텐츠 여부
            web_data: 웹검색 결과 (트렌드 키워드용)
            trend_context: 트렌드 맥락 (왜 지금 이 키워드가 화제인지)

        Returns:
            (HTML 본문, 출처 목록, 템플릿 정보) 튜플
        """
        # 웹검색 결과가 있으면 참고 자료로 추가
        sources = []
        web_data_content = ""

        # 트렌드 맥락이 있으면 먼저 추가 (시의성 있는 글 작성을 위해)
        if trend_context:
            web_data_content = trend_context + "\n\n"
            logger.info("Added trend context to prompt")

        if web_data and web_data.get("content"):
            web_content = web_data["content"][:6000]  # 토큰 제한 고려
            sources = web_data.get("sources", [])

            web_data_content += f"""
[웹검색 결과 - 최신 정보 (반드시 이 내용을 바탕으로 작성)]
{web_content}

[기존 뉴스 데이터]
{news_data}

[중요 규칙]
1. 위 참고 자료의 팩트만 사용하세요
2. 자료에 없는 내용은 추측하지 마세요
3. 최신 날짜, 금액, 수치를 정확히 반영하세요
4. 트렌드 배경이 있다면 "왜 지금 이 키워드가 화제인지" 꼭 언급하세요
"""
            logger.info(f"Added web search data: {len(web_content)} chars from {len(sources)} sources")
        elif news_data:
            web_data_content += news_data

        # 인물 키워드 여부 확인
        is_person = is_person_keyword(keyword)
        if is_person:
            logger.info(f"Person keyword detected: {keyword}")

        # 🆕 템플릿 다양화 시스템 사용 (저품질 방지)
        prompt, template_key, template, cta_config = generate_template_prompt(
            keyword=keyword,
            category=category_name,
            web_data=web_data_content,
            is_evergreen=is_evergreen,
            is_person=is_person
        )

        # 템플릿 정보 로깅
        template_info = get_template_info_log(template_key, template, cta_config)
        print(template_info)
        logger.info(f"Template selected: {template_key} ({template['name']})")
        logger.info(f"Target words: {template['selected_word_count']}, Images: {template['selected_image_count']}")

        # 모델 제한 내에서 최대치 사용 (Haiku: 8192)
        max_tokens = 8000

        content = self._call_ai(prompt, max_tokens=max_tokens)

        # HTML 코드 블록 제거
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

        # AI 메타 응답 제거
        content = clean_ai_response(content)

        # 본문 시작의 대제목 제거 (WP 테마가 별도로 제목 표시하므로 중복)
        content = re.sub(r'^\s*<h2[^>]*style="[^"]*text-align:\s*center[^"]*"[^>]*>.*?</h2>\s*', '', content, count=1, flags=re.DOTALL)

        # placeholder 이미지 제거
        content = re.sub(r'<p[^>]*>\s*<img[^>]*src="https://via\.placeholder\.com[^"]*"[^>]*/?\s*>\s*</p>', '', content, flags=re.DOTALL)
        content = re.sub(r'<img[^>]*src="https://via\.placeholder\.com[^"]*"[^>]*/?\s*>', '', content, flags=re.DOTALL)

        # 남은 IMAGE 태그 및 IMG_CONTEXT 주석 제거
        content = re.sub(r'<!-- IMG_CONTEXT: .+? -->\s*', '', content)
        content = re.sub(r'\[IMAGE_\d+[^\]]*\]', '', content)

        # AdSense 최적화 후처리 (금지 표현 제거, 이모지 제한)
        content = post_process_content(content)

        # 인간화 처리 (AI 탐지 회피)
        content = humanize_full(content, keyword)

        # 템플릿 정보 딕셔너리 반환
        template_info_dict = {
            "key": template_key,
            "name": template["name"],
            "word_count": template["selected_word_count"],
            "image_count": template["selected_image_count"],
            "cta_position": cta_config["position"]
        }

        return content.strip(), sources, template_info_dict

    def _extract_meta_description(self, content: str) -> str:
        """메타 설명 추출"""
        match = re.search(r'\[META\](.*?)\[/META\]', content, flags=re.DOTALL)
        if match:
            return match.group(1).strip()[:160]
        return ""

    def get_official_link(self, keyword: str) -> Optional[dict]:
        """공식 사이트 링크 찾기"""
        for key, info in self.official_links.items():
            if key in keyword:
                return info
        return None

    def get_coupang_link(self, keyword: str) -> Optional[dict]:
        """쿠팡 링크 찾기 (카테고리별)"""
        for category, info in self.coupang_links.items():
            keywords = info.get("keywords", [])
            for kw in keywords:
                if kw in keyword:
                    return {
                        "url": f"{info['url']}?lptag={self.coupang_id}",
                        "button_text": info.get("button_text", "쿠팡에서 확인하기")
                    }
        return None

    def should_exclude_coupang(self, keyword: str, category_name: str) -> bool:
        """
        쿠팡 배너 제외 여부 판단

        Args:
            keyword: 키워드
            category_name: 카테고리명

        Returns:
            True면 쿠팡 제외
        """
        # 1. 카테고리 기반 제외
        if category_name in COUPANG_EXCLUDE_CATEGORIES:
            logger.info(f"Coupang excluded: category '{category_name}' in exclude list")
            return True

        # 2. 키워드 기반 제외 (금융/투자 관련)
        keyword_lower = keyword.lower()
        for exclude_kw in COUPANG_EXCLUDE_KEYWORDS:
            if exclude_kw.lower() in keyword_lower:
                logger.info(f"Coupang excluded: keyword '{exclude_kw}' found in '{keyword}'")
                return True

        return False

    def insert_images(
        self,
        content: str,
        keyword: str,
        category_name: str,
        count: int = 2,
        use_mixed: bool = True
    ) -> str:
        """
        혼합 이미지 시스템으로 [IMAGE_N] 태그를 실제 이미지로 교체

        Phase 3: Puppeteer 스크린샷 + Pexels 혼합

        1. 스크린샷 조건 충족 시 첫 이미지를 스크린샷으로
        2. 나머지는 AI 기반 Pexels 검색

        Args:
            content: HTML 본문
            keyword: 키워드
            category_name: 카테고리 이름
            count: 필요한 이미지 개수
            use_mixed: 혼합 이미지 시스템 사용 여부

        Returns:
            이미지가 삽입된 HTML
        """
        images = {}

        try:
            # 혼합 이미지 시스템 사용 (Phase 3)
            if use_mixed:
                logger.info(f"Fetching mixed images for '{keyword}' (count: {count})")
                images = self.image_fetcher.fetch_mixed_images(
                    content, keyword, category_name, count
                )
            else:
                # 폴백: 기존 AI 기반 Pexels만 사용
                logger.info(f"Fetching contextual images for '{keyword}'")
                images = self.image_fetcher.fetch_contextual_images(content, keyword)
        except Exception as e:
            logger.error(f"Image fetching failed for '{keyword}': {e}")
            # 이미지 가져오기 실패해도 글 발행은 계속 진행
            images = {}

        if not images:
            logger.warning(f"No images found for {keyword}, continuing without images")
            # 이미지 태그 및 IMG_CONTEXT 주석 제거 (확장 패턴: 콜론 포함)
            content = re.sub(r'<!-- IMG_CONTEXT: .+? -->\s*', '', content)
            content = re.sub(r'\[IMAGE_\d+[^\]]*\]', '', content)  # [IMAGE_N: 설명] 포함
            return content

        # 각 이미지 태그를 실제 이미지로 교체
        for tag, img_data in images.items():
            # URL 유효성 확인
            if not img_data.get('url') or not img_data['url'].startswith('http'):
                logger.warning(f"Invalid image URL for {tag}: {img_data.get('url')}")
                continue

            # 캡션: 주제 관련 설명 (Pexels 출처 제거)
            caption = img_data.get('alt', keyword)

            img_html = f'''
<figure style="text-align: center; margin: 30px 0;">
    <img src="{img_data['url']}"
         alt="{img_data['alt']}"
         style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
         loading="lazy" />
    <figcaption style="margin-top: 10px; color: #666; font-size: 14px;">
        {caption}
    </figcaption>
</figure>
'''
            # tag에서 숫자 추출 (IMAGE_1 -> 1)
            tag_num = tag.replace("IMAGE_", "")

            # 패턴 1: IMG_CONTEXT 주석 + 이미지 태그 (콜론 포함)
            pattern1 = rf'<!-- IMG_CONTEXT: .+? -->\s*\[IMAGE_{tag_num}[^\]]*\]'

            # 패턴 2: 이미지 태그만 (콜론 포함) - [IMAGE_1: 설명] 또는 [IMAGE_1]
            pattern2 = rf'\[IMAGE_{tag_num}[^\]]*\]'

            if re.search(pattern1, content):
                content = re.sub(pattern1, img_html, content, count=1)
                logger.info(f"Inserted {tag} (with context): {img_data['search_query']}")
            elif re.search(pattern2, content):
                content = re.sub(pattern2, img_html, content, count=1)
                logger.info(f"Inserted {tag} (tag only): {img_data['search_query']}")
            else:
                logger.warning(f"Tag {tag} not found in content, inserting at section break")
                # 태그가 없으면 적절한 h3/h2 헤더 뒤에 삽입
                headers = list(re.finditer(r'</h[23]>', content))
                tag_idx = int(tag_num) if tag_num.isdigit() else 1
                # tag_idx번째 헤더 뒤에 삽입 (없으면 마지막 헤더 뒤)
                if headers:
                    insert_after = min(tag_idx, len(headers)) - 1
                    pos = headers[insert_after].end()
                    # 바로 뒤에 <p> 있으면 그 문단 뒤에 삽입
                    next_p = re.search(r'</p>', content[pos:])
                    if next_p:
                        pos = pos + next_p.end()
                    content = content[:pos] + img_html + content[pos:]
                    logger.info(f"Force-inserted {tag} after header #{insert_after+1}")

        # 남은 IMG_CONTEXT 주석 및 이미지 태그 제거 (확장 패턴)
        content = re.sub(r'<!-- IMG_CONTEXT: .+? -->\s*', '', content)
        content = re.sub(r'\[IMAGE_\d+[^\]]*\]', '', content)  # [IMAGE_N: 설명] 포함

        return content

    def insert_official_link(self, content: str, keyword: str) -> str:
        """[OFFICIAL_LINK] 태그를 카드형 공식 사이트 링크로 교체"""
        official = self.get_official_link(keyword)

        if official:
            url = official["url"]
            name = official["name"]
            description = official.get("description", f"{name} 공식 홈페이지")
            # 파비콘 URL 생성
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
            
            button_html = OFFICIAL_BUTTON_TEMPLATE.format(
                url=url,
                name=name,
                description=description,
                favicon_url=favicon_url
            )
            content = content.replace("[OFFICIAL_LINK]", button_html)
            logger.info(f"Official card link inserted: {name}")
        else:
            content = content.replace("[OFFICIAL_LINK]", "")

        return content

    def insert_disclaimer(self, content: str) -> str:
        """[DISCLAIMER] 태그를 건강 면책문구로 교체"""
        content = content.replace("[DISCLAIMER]", HEALTH_DISCLAIMER)
        return content

    def insert_affiliate_notice(self, content: str, has_coupang: bool = False) -> str:
        """
        [AFFILIATE_NOTICE] 태그를 파트너스 문구로 교체

        핵심 로직: 쿠팡 배너가 있을 때만 파트너스 문구 삽입
        """
        # 태그 제거 (열기/닫기 모두)
        content = content.replace("[AFFILIATE_NOTICE]", "")
        content = content.replace("[/AFFILIATE_NOTICE]", "")

        if has_coupang:
            # 쿠팡 배너가 있고, 아직 문구가 없을 때만 추가
            if "쿠팡 파트너스 활동" not in content:
                content += AFFILIATE_NOTICE
                logger.info("Affiliate notice inserted (coupang exists)")
        else:
            # 쿠팡 배너가 없으면 Claude가 자체 생성한 파트너스 문구도 제거
            patterns_to_remove = [
                r'<p[^>]*>.*?이 포스팅은 파트너십 및 광고 포함 콘텐츠.*?</p>',
                r'<p[^>]*>.*?이 포스팅은 제휴 마케팅 활동의 일환으로.*?</p>',
                r'<p[^>]*>.*?이 포스팅은 쿠팡 파트너스 활동의 일환으로.*?</p>',
                r'<p[^>]*>.*?파트너십 링크가 포함되어 있을 수 있.*?</p>',
                r'<p[^>]*>.*?이 글에는 제휴 링크가 포함.*?</p>',
                r'이 포스팅은 파트너십 및 광고 포함 콘텐츠이에요\.?',
                r'이 포스팅은 제휴 마케팅 활동의 일환으로.*?작성되었어요\.?',
                r': 이 글에는 파트너십 링크가 포함되어 있을 수 있어요\.?',
            ]

            for pattern in patterns_to_remove:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

            logger.info("Affiliate notice skipped and cleaned (no coupang)")

        return content

    def insert_category_badge(self, content: str, category_name: str) -> str:
        """글 상단에 카테고리 뱃지 삽입"""
        badge = CATEGORY_BADGE_TEMPLATE.format(category=category_name)

        # <div style="text-align: center; 바로 뒤에 삽입
        if '<div style="text-align: center;' in content:
            content = content.replace(
                '<div style="text-align: center; line-height: 2.0;">',
                f'<div style="text-align: center; line-height: 2.0;">\n{badge}',
                1  # 첫 번째만 교체
            )
        else:
            # 없으면 맨 앞에 추가
            content = badge + content

        return content

    def insert_coupang_products(
        self,
        content: str,
        keyword: str,
        category_config: dict,
        category_name: str = ""
    ) -> tuple[str, bool]:
        """
        [COUPANG] 태그를 쿠팡 상품으로 교체

        제외 조건 (우선 적용):
        - 카테고리: 연예, 트렌드, 재테크, 취업교육
        - 키워드: 비트코인, 주식, 투자 등 금융 관련

        삽입 순서:
        1순위: 구글 시트 상품 DB에서 매칭
        2순위: JSON 기반 쿠팡 링크 (키워드 매칭)
        3순위: 카테고리별 기본 링크 (coupang_defaults.json)

        Args:
            content: HTML 본문
            keyword: 키워드
            category_config: 카테고리 설정
            category_name: 카테고리 이름 (기본 링크 조회용)

        Returns:
            (수정된 콘텐츠, 쿠팡 삽입 여부) 튜플
        """
        # 쿠팡 제외 조건 확인 (카테고리 + 키워드 기반) - 가장 먼저 체크
        if self.should_exclude_coupang(keyword, category_name):
            content = content.replace("[COUPANG]", "")
            return content, False

        # 쿠팡이 필요없는 카테고리면 태그만 제거 (기존 설정 호환)
        if not category_config.get("requires_coupang", False):
            content = content.replace("[COUPANG]", "")
            return content, False

        # 쿠팡이 필요한 카테고리인데 [COUPANG] 태그가 없으면 콘텐츠 끝에 추가
        if "[COUPANG]" not in content:
            logger.info("Adding [COUPANG] tag for coupang-required category")
            # 마무리 섹션 앞에 추가 시도
            if "</div>" in content:
                # 마지막 </div> 앞에 삽입
                last_div = content.rfind("</div>")
                content = content[:last_div] + "\n[COUPANG]\n" + content[last_div:]
            else:
                content += "\n[COUPANG]\n"

        # 1순위: 구글 시트 상품 DB
        try:
            products = get_coupang_products()
            if products:
                matched = match_products_for_content(
                    keyword=keyword,
                    content_summary="",
                    products=products,
                    max_products=2
                )
                if matched:
                    products_html = generate_product_html(matched)
                    content = content.replace("[COUPANG]", products_html)
                    logger.info(f"Google Sheets products inserted: {len(matched)} items")
                    return content, True
        except Exception as e:
            logger.warning(f"Google Sheets product fetch failed: {e}")

        # 2순위: JSON 기반 쿠팡 링크 (키워드 매칭)
        coupang = self.get_coupang_link(keyword)
        if coupang:
            button_html = COUPANG_BUTTON_TEMPLATE.format(
                url=coupang["url"],
                button_text=coupang["button_text"]
            )
            content = content.replace("[COUPANG]", button_html)
            logger.info(f"Coupang button inserted: {coupang['button_text']}")
            return content, True

        # 3순위: 카테고리별 기본 링크
        default_link = self.coupang_defaults.get(category_name)
        if default_link:
            button_html = COUPANG_BUTTON_TEMPLATE.format(
                url=default_link["url"],
                button_text=default_link["text"]
            )
            content = content.replace("[COUPANG]", button_html)
            logger.info(f"Coupang default button inserted: {default_link['text']}")
            return content, True

        # 매칭 없음 - 쿠팡 링크 없으면 배너도 없음
        content = content.replace("[COUPANG]", "")
        logger.info("No coupang link found - tag removed")
        return content, False

    def clean_meta_tags(self, content: str) -> str:
        """메타 태그 및 남은 플레이스홀더 정리"""
        # [META] 태그 제거
        content = re.sub(r'\[META\].*?\[/META\]', '', content, flags=re.DOTALL)

        # 남은 플레이스홀더 태그 제거
        content = re.sub(r'\[OFFICIAL_LINK\]', '', content)
        content = re.sub(r'\[COUPANG\]', '', content)
        content = re.sub(r'\[DISCLAIMER\]', '', content)
        content = re.sub(r'\[/?AFFILIATE_NOTICE\]', '', content)  # 열기/닫기 태그 모두 제거
        content = re.sub(r'\[IMAGE_\d+[^\]]*\]', '', content)  # [IMAGE_N: 설명] 포함

        # IMG_CONTEXT 주석 제거 (혹시 남아있는 경우)
        content = re.sub(r'<!-- IMG_CONTEXT: .+? -->\s*', '', content)

        return content.strip()

    def _detect_section_type(self, html: str) -> str:
        """섹션 타입 감지"""
        html_lower = html.lower().strip()

        if html_lower.startswith('<h1') or html_lower.startswith('<h2') or html_lower.startswith('<h3'):
            return "heading"
        elif '<figure' in html_lower or html_lower.startswith('<img'):
            return "image"
        elif '<ul' in html_lower or '<ol' in html_lower:
            return "list"
        elif '<table' in html_lower:
            return "table"
        elif '<blockquote' in html_lower:
            return "quote"
        else:
            return "paragraph"

    def parse_content_to_sections(self, html: str) -> List[Section]:
        """
        HTML 콘텐츠를 섹션 배열로 분리

        각 섹션은 독립적으로 수정 가능한 단위
        """
        sections = []

        # 최상위 HTML 태그들을 매칭
        # h1-h6, p, div, figure, ul, ol, table, blockquote, section
        pattern = r'(<(?:h[1-6]|p|div|figure|ul|ol|table|blockquote|section)[^>]*>.*?</(?:h[1-6]|p|div|figure|ul|ol|table|blockquote|section)>)'

        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        if matches:
            for i, match in enumerate(matches):
                section_html = match.strip()
                if not section_html:
                    continue

                # 빈 콘텐츠 제외 (이미지는 예외)
                text_content = re.sub(r'<[^>]+>', '', section_html).strip()
                if not text_content and '<img' not in section_html.lower() and '<figure' not in section_html.lower():
                    continue

                section_type = self._detect_section_type(section_html)
                sections.append(Section(
                    id=f"section-{uuid.uuid4().hex[:8]}",
                    index=len(sections),
                    type=section_type,
                    html=section_html
                ))
        else:
            # 매칭 안 된 경우 전체를 하나의 섹션으로
            if html.strip():
                sections.append(Section(
                    id=f"section-{uuid.uuid4().hex[:8]}",
                    index=0,
                    type="paragraph",
                    html=html.strip()
                ))

        logger.info(f"Parsed {len(sections)} sections from content")
        return sections

    def generate_full_post(
        self,
        keyword: str,
        news_data: str = "",
        custom_context: str = None,
        force_category: str = None
    ) -> GeneratedPost:
        """
        카테고리별 전체 블로그 포스트 생성

        Args:
            keyword: 키워드
            news_data: 뉴스 요약 데이터
            custom_context: 사용자 지정 작성 방향 (직접 작성 모드)
            force_category: 강제 카테고리 지정 (직접 작성 모드)

        Returns:
            GeneratedPost 객체
        """
        print("\n" + "=" * 60)
        print("📝 블로그 글 생성 프로세스 시작")
        if custom_context:
            print("   [직접 작성 모드]")
        print("=" * 60)

        # Step 1: 키워드 분석 및 카테고리 분류
        print(f"\n[Step 1/8] 키워드 분석")
        print(f"  └─ 키워드: {keyword}")

        # 직접 작성 모드에서는 사용자 지정 카테고리 우선
        if force_category:
            category_name = force_category
            category_config = self.categories_config.get("categories", {}).get(force_category, {})
            if not category_config:
                # 기본 설정 사용
                category_config = {"template": "trend", "requires_coupang": False}
            print(f"  └─ 카테고리: {category_name} (사용자 지정)")
        else:
            category_name, category_config = self.classify_category(keyword)
            print(f"  └─ 카테고리: {category_name}")

        template_name = category_config.get("template", "trend")
        is_evergreen = self.is_evergreen_keyword(keyword)
        print(f"  └─ 에버그린: {'✅ Yes' if is_evergreen else '❌ No'}")
        print(f"  └─ 템플릿: {template_name}")

        # Step 1.5: 트렌드 맥락 수집 또는 사용자 지정 맥락 사용
        print(f"\n[Step 1.5/8] 트렌드 맥락 수집")
        trend_context = ""

        if custom_context:
            # 직접 작성 모드: 사용자 입력을 트렌드 맥락으로 사용
            trend_context = f"""
[작성 방향 - 사용자 요청]
{custom_context}

중요: 위 작성 방향에 맞춰서 글을 작성해주세요.
사용자가 요청한 톤, 스타일, 포함할 내용을 반드시 반영하세요.
"""
            print(f"  ✅ 사용자 지정 작성 방향 적용")
            print(f"     {custom_context[:80]}...")
        elif category_name == "트렌드" or not is_evergreen:
            trend_context = self.get_trend_context(keyword)
            if trend_context:
                print(f"  ✅ 트렌드 맥락 수집 완료 (뉴스 기반)")
            else:
                print(f"  ⚠️ 트렌드 맥락 없음")
        else:
            print(f"  ℹ️ 에버그린 키워드 - 트렌드 맥락 스킵")

        # 이미지 중복 방지 초기화
        self.image_fetcher.reset_used_images()

        # Step 2: 웹검색 (트렌드 + 에버그린 카테고리 모두 적용)
        print(f"\n[Step 2/8] 웹검색 실행")

        # 웹 검색 적용 카테고리 (트렌드 + 에버그린)
        web_search_categories = ["트렌드", "연예", "생활정보", "재테크", "건강", "IT/테크", "취업교육"]

        if category_name in web_search_categories:
            print(f"  🔍 웹 검색 수행: {keyword} (카테고리: {category_name})")
            web_data = self.perform_web_search(keyword)

            if web_data and web_data.get("content"):
                print(f"  ✅ 웹 검색 정보 취합 완료 ({len(web_data.get('content', ''))}자)")
            else:
                print(f"  ⚠️ 웹 검색 결과 없음, AI 기본 지식으로 작성")
        else:
            print(f"  ℹ️ 웹 검색 스킵 (카테고리: {category_name})")
            web_data = {"sources": [], "content": ""}

        sources = web_data.get("sources", []) if web_data else []
        if sources:
            print(f"  └─ 검색 결과: {len(sources)}개 출처")
            for src in sources[:3]:
                print(f"      • {src['title'][:40]}...")
        elif category_name in web_search_categories:
            print(f"  └─ 검색 결과: 없음")

        # Step 2.5a: 블로그 참조 분석
        print(f"\n[Step 2.5a/8] 블로그 참조 분석")
        blog_analysis = ""
        try:
            from crawlers.blog_reference import BlogReferenceCrawler
            blog_ref = BlogReferenceCrawler()
            blog_analysis = blog_ref.get_blog_analysis(keyword, count=3)
            if blog_analysis:
                print(f"  ✅ 블로그 참조 분석 완료")
                # trend_context에 블로그 분석 추가
                if not trend_context:
                    trend_context = ""
                trend_context += f"\n\n[참고 블로그 구조 분석]\n{blog_analysis}\n위 인기 블로그의 구조와 소제목 패턴을 참고하여 작성하세요."
            else:
                print(f"  ⚠️ 블로그 참조 결과 없음")
        except Exception as e:
            logger.warning(f"Blog reference failed: {e}")
            print(f"  ⚠️ 블로그 참조 실패: {e}")

        # Step 2.5b: 인물 키워드 감지 (제목 생성 전에 필요)
        is_person = is_person_keyword(keyword)
        if is_person:
            print(f"\n  👤 인물 키워드 감지: {keyword}")

        # Step 3: 제목 생성
        print(f"\n[Step 3/8] 제목 생성")
        print(f"  └─ Claude API 호출 중...")
        # 인물 키워드면 뉴스 데이터 전달하여 팩트 기반 제목 생성
        web_content_for_title = web_data.get("content", "")[:800] if web_data else ""
        title = self.generate_title(keyword, news_data=web_content_for_title, is_person=is_person)
        print(f"  └─ 생성된 제목: {title}")

        # Step 4: 본문 생성 (템플릿 다양화 시스템 + 트렌드 맥락)
        print(f"\n[Step 4/8] 본문 생성 (템플릿 다양화)")
        print(f"  └─ 에버그린: {'✅ Yes' if is_evergreen else '❌ No'}")
        if trend_context:
            print(f"  └─ 트렌드 맥락: 포함")
        print(f"  └─ Claude API 호출 중...")
        content, content_sources, template_info = self.generate_content_with_template(
            keyword, news_data, template_name,
            category_name=category_name,
            is_evergreen=is_evergreen,
            web_data=web_data,
            trend_context=trend_context  # 트렌드 맥락 추가
        )
        print(f"  └─ 생성 완료: {len(content)} chars")
        print(f"  └─ 사용된 템플릿: {template_info['name']} ({template_info['key']})")
        print(f"  └─ 목표 글자수: {template_info['word_count']}자, 이미지: {template_info['image_count']}개")
        sources = content_sources if content_sources else sources

        # Step 5: 메타 설명 추출
        excerpt = self._extract_meta_description(content)
        if not excerpt:
            excerpt = f"{keyword}에 대한 완벽 가이드! 핵심 정보부터 실전 팁까지 한 번에 알아보세요."[:160]

        # Step 5: 후처리 (이미지, 링크, 쿠팡)
        print(f"\n[Step 5/8] 후처리")

        # 이미지 삽입 (템플릿에서 지정한 이미지 개수 사용)
        image_count = template_info.get('image_count', 4)
        content = self.insert_images(content, keyword, category_name, image_count)
        print(f"  └─ 이미지 삽입 완료")

        # 관련 사이트 링크 자동 삽입 (카테고리 상관없이 항상)
        print("  🔗 관련 사이트 링크 삽입 중...")
        content = insert_related_links(content, keyword)
        print("  ✅ 링크 삽입 완료")

        # 건강 면책문구 삽입
        if category_config.get("requires_disclaimer", False):
            content = self.insert_disclaimer(content)
            print(f"  └─ 건강 면책문구 삽입 완료")
        else:
            content = content.replace("[DISCLAIMER]", "")

        # Step 6: 쿠팡 처리
        print(f"\n[Step 6/8] 쿠팡 처리")
        content, has_coupang = self.insert_coupang_products(
            content, keyword, category_config, category_name
        )
        print(f"  └─ 쿠팡 삽입: {'✅ Yes' if has_coupang else '❌ No'}")

        # 파트너스 문구 삽입
        content = self.insert_affiliate_notice(content, has_coupang)

        # 카테고리 뱃지 삽입
        content = self.insert_category_badge(content, category_name)

        # 정리
        content = self.clean_meta_tags(content)

        # Step 7: 섹션 분리
        print(f"\n[Step 7/8] 섹션 분리")
        sections = self.parse_content_to_sections(content)
        print(f"  └─ 섹션 수: {len(sections)}개")
        for s in sections[:5]:  # 처음 5개만 표시
            text_preview = re.sub(r'<[^>]+>', '', s.html)[:30].strip()
            print(f"      • [{s.type}] {text_preview}...")

        # Step 8: 최종 결과
        print(f"\n[Step 8/8] 최종 결과")
        print(f"  └─ 제목: {title}")
        print(f"  └─ 카테고리: {category_name}")
        print(f"  └─ 콘텐츠 길이: {len(content)} chars")
        print(f"  └─ 섹션 수: {len(sections)}개")
        print(f"  └─ 웹 출처: {len(sources)}개")
        print(f"  └─ 쿠팡: {'있음' if has_coupang else '없음'}")

        print("\n" + "=" * 60)
        print("✅ 블로그 글 생성 완료!")
        print("=" * 60 + "\n")

        # 기존 로거 호출 (파일 로그용)
        logger.info(f"Post generation complete: {title}")
        logger.info(f"  Category: {category_name}, Template: {template_name}")
        logger.info(f"  Content: {len(content)} chars, Sections: {len(sections)}, Sources: {len(sources)}, Coupang: {has_coupang}")

        return GeneratedPost(
            title=title,
            content=content,
            excerpt=excerpt,
            category=category_name,
            template=template_name,
            has_coupang=has_coupang,
            sources=sources,
            sections=sections
        )


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)
    generator = ContentGenerator()

    # 테스트 키워드들
    test_keywords = [
        ("연말정산", "재테크"),
        ("아이폰16", "IT테크"),
        ("BTS 컴백", "연예"),
        ("다이어트", "건강"),
    ]

    for keyword, expected_category in test_keywords[:1]:  # 첫 번째만 테스트
        print(f"\n{'='*60}")
        print(f"Testing: {keyword} (expected: {expected_category})")
        print(f"{'='*60}")

        post = generator.generate_full_post(keyword)

        print(f"\nResult:")
        print(f"  Title: {post.title}")
        print(f"  Category: {post.category}")
        print(f"  Template: {post.template}")
        print(f"  Excerpt: {post.excerpt}")
        print(f"  Has Coupang: {post.has_coupang}")
        print(f"  Content length: {len(post.content)} chars")
        print(f"\nContent preview:\n{post.content[:1500]}...")
