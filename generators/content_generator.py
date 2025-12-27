"""
Claude AI 콘텐츠 생성 모듈
프롬프트 기반으로 AI가 스스로 판단하여 고품질 블로그 글을 생성합니다.
"""
import re
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass

import anthropic

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.categories import get_category_for_keyword, is_coupang_allowed
from crawlers.web_search import search_and_get_context
from generators.prompts import (
    SYSTEM_PROMPT,
    get_content_prompt,
    get_title_prompt,
    get_expand_prompt,
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
    image_types: List[str] = None  # AI가 판단한 이미지 타입들
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
        max_tokens: int = 8000
    ) -> str:
        """
        Claude API 호출

        Args:
            user_prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수

        Returns:
            생성된 텍스트
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
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
        prompt = get_title_prompt(keyword)
        title = self._call_claude(prompt, max_tokens=200)
        return title.strip().strip('"\'')

    def generate_content(
        self,
        keyword: str,
        category: str,
        is_evergreen: bool = False
    ) -> Tuple[str, List[str]]:
        """
        블로그 본문 생성

        Args:
            keyword: 키워드
            category: 카테고리
            is_evergreen: 에버그린 콘텐츠 여부

        Returns:
            (HTML 본문, 이미지 타입 리스트) 튜플
        """
        # 웹검색으로 최신 정보 수집
        web_context = ""
        if settings.google_api_key:
            print("  🔍 웹검색 중...")
            web_context = search_and_get_context(keyword)
            if web_context:
                print(f"  ✅ 검색 결과 수집 완료 ({len(web_context)}자)")

        # 프롬프트 생성
        prompt = get_content_prompt(
            keyword=keyword,
            category=category,
            search_context=web_context,
            is_evergreen=is_evergreen
        )

        # 콘텐츠 생성
        print("  🤖 AI 콘텐츠 생성 중...")
        content = self._call_claude(prompt, max_tokens=8000)

        # HTML 코드 블록 제거
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

        # AI가 판단한 이미지 타입 파싱
        image_types = self._parse_image_types(content)
        print(f"  🖼️ AI 이미지 타입 판단: {image_types}")

        # 이미지 타입 태그 제거 (실제 HTML에서는 제거)
        content = re.sub(r'\[IMAGE_TYPE:(SCREENSHOT|PEXELS)\]\s*', '', content)

        # 글자수 확인 및 확장
        target_length = 6000 if is_evergreen else 5000
        if len(content) < target_length:
            print(f"  ⚠️ 글자수 부족 ({len(content)}자), 확장 중...")
            content = self._expand_content(content, keyword, target_length)
            print(f"  ✅ 확장 완료 ({len(content)}자)")

        # 인간화 처리
        print("  🧑 인간화 처리 중...")
        content = humanize_content(content, keyword)

        return content.strip(), image_types

    def _parse_image_types(self, content: str) -> List[str]:
        """
        AI가 지정한 이미지 타입 파싱 (폴백 강화)

        Args:
            content: 생성된 콘텐츠

        Returns:
            이미지 타입 리스트 (예: ["SCREENSHOT", "PEXELS", "PEXELS"])
        """
        pattern = r'\[IMAGE_TYPE:(SCREENSHOT|PEXELS)\]'
        matches = re.findall(pattern, content)

        # [IMAGE_N] 태그 개수 확인
        image_tags = re.findall(r'\[IMAGE_\d+\]', content)
        image_count = len(image_tags)

        # 매치가 없거나 부족하면 기본값(PEXELS)으로 채움
        if not matches:
            logger.warning(f"IMAGE_TYPE 태그 없음, 기본값 PEXELS {max(image_count, 2)}개 사용")
            return ["PEXELS"] * max(image_count, 2)  # 최소 2개

        # 매치 개수가 이미지 태그보다 적으면 PEXELS로 채움
        if len(matches) < image_count:
            logger.info(f"IMAGE_TYPE {len(matches)}개, IMAGE 태그 {image_count}개 - PEXELS로 보충")
            matches.extend(["PEXELS"] * (image_count - len(matches)))

        # 이미지 타입이 있지만 IMAGE 태그가 없으면 최소 2개 반환
        if image_count == 0 and matches:
            return matches[:2] if len(matches) >= 2 else matches + ["PEXELS"] * (2 - len(matches))

        # 최종 폴백: 아무것도 없으면 PEXELS 2개
        return matches if matches else ["PEXELS", "PEXELS"]

    def _expand_content(self, content: str, keyword: str, target_length: int) -> str:
        """
        글자수가 부족한 경우 콘텐츠 확장

        Args:
            content: 현재 콘텐츠
            keyword: 키워드
            target_length: 목표 글자수

        Returns:
            확장된 콘텐츠
        """
        prompt = get_expand_prompt(
            content=content,
            keyword=keyword,
            current_length=len(content),
            target_length=target_length
        )

        expanded = self._call_claude(prompt, max_tokens=8000)

        # HTML 코드 블록 제거
        expanded = re.sub(r'^```html\s*', '', expanded, flags=re.MULTILINE)
        expanded = re.sub(r'\s*```$', '', expanded, flags=re.MULTILINE)

        return expanded.strip()

    def _extract_meta(self, content: str) -> str:
        """메타 설명 추출 또는 생성"""
        # [META] 태그 확인
        match = re.search(r'\[META\](.*?)\[/META\]', content, re.DOTALL)
        if match:
            return match.group(1).strip()[:160]

        # 첫 번째 <p> 태그 내용에서 추출
        p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
        if p_match:
            text = re.sub(r'<[^>]+>', '', p_match.group(1))
            return text[:160].strip()

        return ""

    def _clean_content(self, content: str) -> str:
        """태그 정리 (이미지 태그는 유지!)"""
        # 메타 태그 제거
        content = re.sub(r'\[META\].*?\[/META\]', '', content, flags=re.DOTALL)
        # 이미지 타입 태그 제거
        content = re.sub(r'\[IMAGE_TYPE:(SCREENSHOT|PEXELS)\]\s*', '', content)
        # [COUPANG] 태그는 coupang.py에서 처리
        # [IMAGE_X] 태그는 wordpress.py에서 처리
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

        # 본문 생성 (이미지 타입 포함)
        print("\n[3/4] 본문 생성 중...")
        content, image_types = self.generate_content(
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

        # 콘텐츠 타입 (템플릿 대신 사용)
        content_type = "에버그린" if is_evergreen else "트렌드"

        print("\n[4/4] 최종 결과")
        print(f"  └─ 제목: {title}")
        print(f"  └─ 카테고리: {category}")
        print(f"  └─ 콘텐츠 타입: {content_type}")
        print(f"  └─ 이미지 타입: {image_types}")
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
            template=content_type,
            image_types=image_types,
            has_coupang=has_coupang,
        )


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    generator = ContentGenerator()

    # 트렌드 키워드 테스트
    post = generator.generate_full_post("혜리", is_evergreen=False)

    print("\n=== 생성 결과 ===")
    print(f"제목: {post.title}")
    print(f"카테고리: {post.category}")
    print(f"이미지 타입: {post.image_types}")
    print(f"쿠팡: {post.has_coupang}")
    print(f"본문 미리보기:\n{post.content[:500]}...")
