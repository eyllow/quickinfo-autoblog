"""섹션 편집 API 라우터"""
import re
import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import anthropic

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sections", tags=["sections"])


# =============================================================================
# 요청/응답 모델
# =============================================================================

class SectionEditRequest(BaseModel):
    """섹션 수정 요청"""
    section_id: str
    section_html: str
    instruction: str
    section_type: str = "paragraph"
    keyword: str = ""  # 컨텍스트용


class SectionEditResponse(BaseModel):
    """섹션 수정 응답"""
    success: bool
    section_id: str
    updated_html: str
    error: Optional[str] = None


class ScreenshotRequest(BaseModel):
    """스크린샷 요청"""
    url: Optional[str] = None
    keyword: Optional[str] = None  # "홈택스" 같은 키워드


class ScreenshotResponse(BaseModel):
    """스크린샷 응답"""
    success: bool
    image_url: Optional[str] = None
    html: Optional[str] = None
    error: Optional[str] = None


# 키워드 → URL 매핑
URL_MAPPING = {
    "홈택스": "https://hometax.go.kr",
    "국세청": "https://nts.go.kr",
    "정부24": "https://gov.kr",
    "국민연금": "https://nps.or.kr",
    "건강보험": "https://nhis.or.kr",
    "고용보험": "https://ei.go.kr",
    "근로복지공단": "https://kcomwel.or.kr",
    "청년도약계좌": "https://ylaccount.kinfa.or.kr",
    "주택청약": "https://apt2you.com",
    "위택스": "https://wetax.go.kr",
    "대법원": "https://scourt.go.kr",
    "법원": "https://scourt.go.kr",
    "한국장학재단": "https://kosaf.go.kr",
}


# =============================================================================
# API 엔드포인트
# =============================================================================

@router.post("/edit", response_model=SectionEditResponse)
async def edit_section(request: SectionEditRequest):
    """
    단일 섹션만 AI로 수정

    핵심: 해당 섹션만 수정하고 반환, 다른 섹션은 절대 건드리지 않음
    """
    try:
        client = anthropic.Anthropic(api_key=settings.claude_api_key)

        type_labels = {
            'heading': '제목',
            'paragraph': '문단',
            'list': '리스트',
            'table': '표',
            'quote': '인용문',
            'image': '이미지',
        }
        type_label = type_labels.get(request.section_type, '콘텐츠')

        prompt = f"""당신은 HTML 섹션 수정 전문가입니다.

[절대 규칙]
1. 주어진 HTML 섹션만 수정하세요
2. 수정된 HTML만 출력하세요 (설명, 인사말, 부연설명 절대 없이)
3. HTML 태그 구조는 최대한 유지하세요
4. 요청된 수정사항만 반영하세요
5. 새로운 섹션을 추가하지 마세요
6. ```html 같은 코드 블록 마크다운을 사용하지 마세요

[현재 {type_label} HTML]
{request.section_html}

[수정 요청]
{request.instruction}

{f'[키워드 컨텍스트] {request.keyword}' if request.keyword else ''}

[출력]
수정된 HTML만 출력 (다른 텍스트 없이):"""

        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        updated_html = response.content[0].text.strip()

        # HTML 코드 블록 제거
        updated_html = re.sub(r'^```html\s*', '', updated_html, flags=re.MULTILINE)
        updated_html = re.sub(r'\s*```$', '', updated_html, flags=re.MULTILINE)
        updated_html = updated_html.strip()

        # HTML 태그로 시작하는지 검증
        if not updated_html.startswith('<'):
            # AI가 설명을 추가한 경우, HTML 부분만 추출 시도
            html_match = re.search(r'<[^>]+>.*</[^>]+>', updated_html, re.DOTALL)
            if html_match:
                updated_html = html_match.group()
            else:
                # 정말 HTML이 없으면 p 태그로 감싸기
                updated_html = f"<p>{updated_html}</p>"

        logger.info(f"Section {request.section_id} edited successfully")

        return SectionEditResponse(
            success=True,
            section_id=request.section_id,
            updated_html=updated_html
        )

    except Exception as e:
        logger.error(f"Section edit failed: {e}")
        return SectionEditResponse(
            success=False,
            section_id=request.section_id,
            updated_html=request.section_html,  # 실패 시 원본 유지
            error=str(e)
        )


@router.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshot(request: ScreenshotRequest):
    """
    URL 또는 키워드로 스크린샷 캡처

    키워드가 주어지면 URL 매핑에서 찾아서 캡처
    """
    try:
        # 키워드로 URL 찾기
        url = request.url
        keyword_match = None

        if not url and request.keyword:
            for key, mapped_url in URL_MAPPING.items():
                if key in request.keyword:
                    url = mapped_url
                    keyword_match = key
                    break

        if not url:
            return ScreenshotResponse(
                success=False,
                error=f"URL을 찾을 수 없습니다. 지원되는 키워드: {', '.join(URL_MAPPING.keys())}"
            )

        logger.info(f"Capturing screenshot: {url} (keyword: {keyword_match or 'N/A'})")

        # Puppeteer 스크린샷 캡처
        try:
            from utils.unique_image import generate_unique_screenshot
            screenshot_path = generate_unique_screenshot(keyword_match or "screenshot", url=url)
        except ImportError:
            # 폴백: 직접 스크린샷 함수 호출
            from utils.screenshot_generator import capture_url
            screenshot_path = capture_url(url)

        if not screenshot_path or not Path(screenshot_path).exists():
            return ScreenshotResponse(
                success=False,
                error="스크린샷 캡처 실패"
            )

        # WordPress에 업로드
        try:
            from utils.image_fetcher import ImageFetcher
            fetcher = ImageFetcher()
            image_url = fetcher.upload_to_wordpress_media(
                screenshot_path,
                alt_text=f"{keyword_match or url} 스크린샷"
            )
        except Exception as e:
            logger.error(f"WordPress upload failed: {e}")
            return ScreenshotResponse(
                success=False,
                error=f"이미지 업로드 실패: {str(e)}"
            )

        if not image_url:
            return ScreenshotResponse(
                success=False,
                error="이미지 업로드 실패"
            )

        # HTML 생성
        caption = f"{keyword_match or url} 메인 화면 (실시간 캡처)"
        html = f'''<figure style="text-align: center; margin: 30px 0;">
    <img src="{image_url}" alt="{keyword_match or url} 스크린샷" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" loading="lazy" />
    <figcaption style="margin-top: 10px; color: #666; font-size: 14px;">{caption}</figcaption>
</figure>'''

        logger.info(f"Screenshot captured and uploaded: {image_url}")

        return ScreenshotResponse(
            success=True,
            image_url=image_url,
            html=html
        )

    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return ScreenshotResponse(
            success=False,
            error=str(e)
        )


@router.get("/url-mapping")
async def get_url_mapping():
    """지원되는 키워드 → URL 매핑 목록 반환"""
    return {
        "mappings": URL_MAPPING,
        "keywords": list(URL_MAPPING.keys())
    }
