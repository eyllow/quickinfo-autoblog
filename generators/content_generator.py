"""Claude AI 콘텐츠 생성기 - 카테고리별 고품질 블로그 글 생성"""
import json
import logging
import re
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings
from utils.image_fetcher import ImageFetcher
from utils.google_sheets import get_coupang_products
from utils.product_matcher import match_products_for_content, generate_product_html
from .prompts import (
    SYSTEM_PROMPT,
    STRUCTURE_PROMPT,
    TITLE_PROMPT,
    CATEGORY_TEMPLATES,
    get_template,
    OFFICIAL_BUTTON_TEMPLATE,
    COUPANG_BUTTON_TEMPLATE,
    COUPANG_DISCLAIMER,
    HEALTH_DISCLAIMER,
    AFFILIATE_NOTICE,
    CATEGORY_BADGE_TEMPLATE
)

logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_DIR = Path(settings.config_dir)


@dataclass
class GeneratedPost:
    """생성된 포스트 데이터"""
    title: str
    content: str
    excerpt: str
    category: str
    template: str
    has_coupang: bool = False


class ContentGenerator:
    """Claude AI를 사용한 카테고리별 고품질 콘텐츠 생성기"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
        self.coupang_id = settings.coupang_partner_id
        self.image_fetcher = ImageFetcher()

        # 설정 파일 로드
        self.categories_config = self._load_json("categories.json")
        self.official_links = self._load_json("official_links.json")
        self.coupang_links = self._load_json("coupang_links.json")

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

    def _call_claude(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = 8000
    ) -> str:
        """Claude API 호출"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
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

    def generate_title(self, keyword: str) -> str:
        """블로그 제목 생성"""
        prompt = TITLE_PROMPT.format(keyword=keyword)
        title = self._call_claude(prompt, max_tokens=200)
        return title.strip().strip('"\'')

    def generate_content_with_template(
        self,
        keyword: str,
        news_data: str,
        template_name: str
    ) -> str:
        """
        카테고리별 템플릿으로 본문 생성

        Args:
            keyword: 키워드
            news_data: 뉴스 데이터
            template_name: 템플릿 이름 (finance, product, celebrity 등)

        Returns:
            HTML 본문
        """
        template = get_template(template_name)

        prompt = template.format(
            keyword=keyword,
            news_data=news_data
        )

        content = self._call_claude(prompt, max_tokens=8000)

        # HTML 코드 블록 제거
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

        return content.strip()

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

    def insert_images(
        self,
        content: str,
        keyword: str,
        category_name: str
    ) -> str:
        """
        [IMAGE_N] 태그를 실제 이미지로 교체

        Args:
            content: HTML 본문
            keyword: 키워드
            category_name: 카테고리 이름

        Returns:
            이미지가 삽입된 HTML
        """
        # 카테고리에 맞는 이미지 검색
        images = self.image_fetcher.search_images_for_category(
            keyword=keyword,
            category_name=category_name,
            count=4
        )

        if not images:
            logger.warning(f"No images found for {keyword}")
            # 이미지 태그 제거
            for i in range(1, 5):
                content = content.replace(f"[IMAGE_{i}]", "")
            return content

        # 이미지 태그 교체
        for i, img in enumerate(images, 1):
            tag = f"[IMAGE_{i}]"
            if tag in content:
                img_html = self.image_fetcher.generate_image_html(
                    img, keyword, f"{keyword} 관련 이미지 {i}"
                )
                content = content.replace(tag, img_html)

        # 남은 태그 제거
        for i in range(1, 5):
            content = content.replace(f"[IMAGE_{i}]", "")

        return content

    def insert_official_link(self, content: str, keyword: str) -> str:
        """[OFFICIAL_LINK] 태그를 공식 사이트 버튼으로 교체"""
        official = self.get_official_link(keyword)

        if official:
            button_html = OFFICIAL_BUTTON_TEMPLATE.format(
                url=official["url"],
                name=official["name"]
            )
            content = content.replace("[OFFICIAL_LINK]", button_html)
            logger.info(f"Official link inserted: {official['name']}")
        else:
            content = content.replace("[OFFICIAL_LINK]", "")

        return content

    def insert_disclaimer(self, content: str) -> str:
        """[DISCLAIMER] 태그를 건강 면책문구로 교체"""
        content = content.replace("[DISCLAIMER]", HEALTH_DISCLAIMER)
        return content

    def insert_affiliate_notice(self, content: str) -> str:
        """[AFFILIATE_NOTICE] 태그를 파트너스 문구로 교체 (중복 방지)"""
        # 태그 제거
        content = content.replace("[AFFILIATE_NOTICE]", "")

        # 이미 파트너스 문구가 있으면 추가하지 않음
        if "쿠팡 파트너스 활동" not in content:
            content += AFFILIATE_NOTICE

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
        category_config: dict
    ) -> tuple[str, bool]:
        """
        [COUPANG] 태그를 쿠팡 상품으로 교체

        1순위: 구글 시트 상품 DB에서 매칭
        2순위: JSON 기반 쿠팡 링크

        Args:
            content: HTML 본문
            keyword: 키워드
            category_config: 카테고리 설정

        Returns:
            (수정된 콘텐츠, 쿠팡 삽입 여부) 튜플
        """
        # 쿠팡이 필요없는 카테고리면 태그만 제거
        if not category_config.get("requires_coupang", False):
            content = content.replace("[COUPANG]", "")
            return content, False

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

        # 2순위: JSON 기반 쿠팡 링크
        coupang = self.get_coupang_link(keyword)
        if coupang:
            button_html = COUPANG_BUTTON_TEMPLATE.format(
                url=coupang["url"],
                button_text=coupang["button_text"]
            )
            content = content.replace("[COUPANG]", button_html + COUPANG_DISCLAIMER)
            logger.info(f"Coupang button inserted: {coupang['button_text']}")
            return content, True

        # 매칭 없음
        content = content.replace("[COUPANG]", "")
        return content, False

    def clean_meta_tags(self, content: str) -> str:
        """메타 태그 및 남은 플레이스홀더 정리"""
        # [META] 태그 제거
        content = re.sub(r'\[META\].*?\[/META\]', '', content, flags=re.DOTALL)

        # 남은 플레이스홀더 태그 제거
        content = re.sub(r'\[OFFICIAL_LINK\]', '', content)
        content = re.sub(r'\[COUPANG\]', '', content)
        content = re.sub(r'\[DISCLAIMER\]', '', content)
        content = re.sub(r'\[AFFILIATE_NOTICE\]', '', content)
        content = re.sub(r'\[IMAGE_\d\]', '', content)

        return content.strip()

    def generate_full_post(
        self,
        keyword: str,
        news_data: str = ""
    ) -> GeneratedPost:
        """
        카테고리별 전체 블로그 포스트 생성

        Args:
            keyword: 키워드
            news_data: 뉴스 요약 데이터

        Returns:
            GeneratedPost 객체
        """
        logger.info(f"=" * 50)
        logger.info(f"Generating post for: {keyword}")

        # 1. 카테고리 분류
        logger.info("Step 1: Classifying category...")
        category_name, category_config = self.classify_category(keyword)
        template_name = category_config.get("template", "trend")
        logger.info(f"  Category: {category_name}, Template: {template_name}")

        # 2. 제목 생성
        logger.info("Step 2: Generating title...")
        title = self.generate_title(keyword)
        logger.info(f"  Title: {title}")

        # 3. 본문 생성 (카테고리별 템플릿)
        logger.info(f"Step 3: Generating content with '{template_name}' template...")
        content = self.generate_content_with_template(keyword, news_data, template_name)
        logger.info(f"  Raw content length: {len(content)} chars")

        # 4. 메타 설명 추출
        excerpt = self._extract_meta_description(content)
        if not excerpt:
            excerpt = f"{keyword}에 대한 완벽 가이드! 핵심 정보부터 실전 팁까지 한 번에 알아보세요."[:160]

        # 5. 이미지 삽입
        logger.info("Step 4: Inserting images...")
        content = self.insert_images(content, keyword, category_name)

        # 6. 공식 사이트 링크 삽입 (필요시)
        if category_config.get("requires_official_link", False):
            logger.info("Step 5: Inserting official link...")
            content = self.insert_official_link(content, keyword)
        else:
            content = content.replace("[OFFICIAL_LINK]", "")

        # 7. 건강 면책문구 삽입 (필요시)
        if category_config.get("requires_disclaimer", False):
            logger.info("Step 6: Inserting health disclaimer...")
            content = self.insert_disclaimer(content)
        else:
            content = content.replace("[DISCLAIMER]", "")

        # 8. 쿠팡 상품 삽입
        logger.info("Step 7: Inserting coupang products...")
        content, has_coupang = self.insert_coupang_products(content, keyword, category_config)

        # 9. 파트너스 문구 삽입 (중복 방지)
        content = self.insert_affiliate_notice(content)

        # 10. 카테고리 뱃지 삽입
        logger.info("Step 8: Inserting category badge...")
        content = self.insert_category_badge(content, category_name)

        # 11. 정리
        content = self.clean_meta_tags(content)

        logger.info(f"=" * 50)
        logger.info(f"Post generation complete!")
        logger.info(f"  Title: {title}")
        logger.info(f"  Category: {category_name}")
        logger.info(f"  Template: {template_name}")
        logger.info(f"  Content length: {len(content)} chars")
        logger.info(f"  Has Coupang: {has_coupang}")
        logger.info(f"=" * 50)

        return GeneratedPost(
            title=title,
            content=content,
            excerpt=excerpt,
            category=category_name,
            template=template_name,
            has_coupang=has_coupang
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
