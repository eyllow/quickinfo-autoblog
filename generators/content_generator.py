"""
Claude AI 콘텐츠 생성 모듈
키워드를 받아 고품질 블로그 글을 생성합니다.
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass

import anthropic

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.categories import get_category_for_keyword, is_coupang_allowed
from crawlers.web_search import search_and_get_context
from generators.prompts import (
    HUMAN_PERSONA_PROMPT,
    SYSTEM_PROMPT,
    generate_content_prompt,
    generate_title_prompt,
    get_random_template,
)
from generators.humanizer import humanize_content

logger = logging.getLogger(__name__)


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
    """Claude AI를 사용한 콘텐츠 생성기"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

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
            use_persona: 인간 페르소나 사용 여부

        Returns:
            생성된 텍스트
        """
        try:
            # 인간 페르소나 프롬프트 추가 (AI 탐지 회피)
            if use_persona:
                full_system = HUMAN_PERSONA_PROMPT + "\n\n" + system_prompt
            else:
                full_system = system_prompt

            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=full_system,
                messages=[{"role": "user", "content": user_prompt}]
            )

            return message.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Claude API 에러: {e}")
            raise

    def generate_title(self, keyword: str) -> str:
        """
        블로그 제목 생성

        Args:
            keyword: 키워드

        Returns:
            생성된 제목
        """
        prompt = generate_title_prompt(keyword)
        title = self._call_claude(prompt, max_tokens=200, use_persona=False)
        return title.strip().strip('"\'')

    def generate_content(
        self,
        keyword: str,
        category: str,
        is_evergreen: bool = False
    ) -> tuple:
        """
        블로그 본문 생성

        Args:
            keyword: 키워드
            category: 카테고리
            is_evergreen: 에버그린 콘텐츠 여부

        Returns:
            (HTML 본문, 템플릿 이름) 튜플
        """
        # 웹검색으로 최신 정보 수집
        web_context = ""
        if settings.google_api_key:
            print("  🔍 웹검색 중...")
            web_context = search_and_get_context(keyword)
            if web_context:
                print(f"  ✅ 검색 결과 수집 완료 ({len(web_context)}자)")

        # 랜덤 템플릿 선택
        template_key, template_info = get_random_template()
        print(f"  📝 선택된 템플릿: {template_info['name']}")

        # 프롬프트 생성
        prompt = generate_content_prompt(
            keyword=keyword,
            category=category,
            template_key=template_key,
            web_context=web_context,
            is_evergreen=is_evergreen
        )

        # 콘텐츠 생성
        content = self._call_claude(prompt, max_tokens=8000)

        # HTML 코드 블록 제거
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

        # 인간화 처리
        print("  🧑 인간화 처리 중...")
        content = humanize_content(content, keyword)

        return content.strip(), template_info['name']

    def _extract_meta(self, content: str) -> str:
        """메타 설명 추출"""
        match = re.search(r'\[META\](.*?)\[/META\]', content, re.DOTALL)
        if match:
            return match.group(1).strip()[:160]
        return ""

    def _clean_content(self, content: str) -> str:
        """태그 정리"""
        # 메타 태그 제거
        content = re.sub(r'\[META\].*?\[/META\]', '', content, flags=re.DOTALL)
        # 남은 플레이스홀더 제거
        content = re.sub(r'\[COUPANG\]', '', content)
        content = re.sub(r'\[IMAGE_\d+\]', '', content)
        return content.strip()

    def generate_full_post(
        self,
        keyword: str,
        is_evergreen: bool = False
    ) -> GeneratedPost:
        """
        완전한 블로그 포스트 생성

        Args:
            keyword: 키워드
            is_evergreen: 에버그린 콘텐츠 여부

        Returns:
            GeneratedPost 객체
        """
        print(f"\n{'='*60}")
        print(f"📝 블로그 글 생성 시작: {keyword}")
        print(f"{'='*60}")

        # 카테고리 분류
        category = get_category_for_keyword(keyword)
        print(f"\n[1/4] 카테고리 분류: {category}")

        # 제목 생성
        print("\n[2/4] 제목 생성 중...")
        title = self.generate_title(keyword)
        print(f"  ✅ 제목: {title}")

        # 본문 생성
        print("\n[3/4] 본문 생성 중...")
        content, template_name = self.generate_content(
            keyword=keyword,
            category=category,
            is_evergreen=is_evergreen
        )
        print(f"  ✅ 본문 생성 완료 ({len(content)}자)")

        # 메타 설명 추출
        excerpt = self._extract_meta(content)
        if not excerpt:
            excerpt = f"{keyword}에 대한 완벽 가이드! 핵심 정보와 꿀팁을 한 번에 알아보세요."

        # 쿠팡 허용 여부
        has_coupang = is_coupang_allowed(category)

        # 콘텐츠 정리
        content = self._clean_content(content)

        print("\n[4/4] 최종 결과")
        print(f"  └─ 제목: {title}")
        print(f"  └─ 카테고리: {category}")
        print(f"  └─ 템플릿: {template_name}")
        print(f"  └─ 쿠팡: {'✅ 허용' if has_coupang else '❌ 비허용'}")
        print(f"  └─ 글자수: {len(content)}자")

        print(f"\n{'='*60}")
        print("✅ 블로그 글 생성 완료!")
        print(f"{'='*60}\n")

        return GeneratedPost(
            title=title,
            content=content,
            excerpt=excerpt,
            category=category,
            template=template_name,
            has_coupang=has_coupang,
        )


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    generator = ContentGenerator()

    # 트렌드 키워드 테스트
    post = generator.generate_full_post("연말정산", is_evergreen=True)

    print("\n=== 생성 결과 ===")
    print(f"제목: {post.title}")
    print(f"카테고리: {post.category}")
    print(f"템플릿: {post.template}")
    print(f"쿠팡: {post.has_coupang}")
    print(f"본문 미리보기:\n{post.content[:500]}...")
