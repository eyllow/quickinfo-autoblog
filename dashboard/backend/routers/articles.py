"""글 생성 및 관리 API 라우터"""
import re
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from generators.content_generator import ContentGenerator
from dashboard.backend.models import (
    ArticleCreate,
    ArticleResponse,
    Section,
    SectionEditRequest,
    SectionEditResponse,
    KeywordSuggestion,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/articles", tags=["articles"])

# 메모리 저장소 (실제 운영에서는 DB 사용 권장)
articles_store: Dict[str, dict] = {}


def parse_sections(content: str) -> List[Section]:
    """
    HTML 콘텐츠를 섹션으로 파싱

    h2 태그를 기준으로 섹션 분리
    """
    sections = []

    # h2 태그로 섹션 분리
    pattern = r'(<h2[^>]*>.*?</h2>)(.*?)(?=<h2|$)'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

    if matches:
        for i, (h2_tag, section_content) in enumerate(matches, 1):
            # h2 태그에서 제목 추출
            title_match = re.search(r'<h2[^>]*>(.*?)</h2>', h2_tag, re.DOTALL | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else f"섹션 {i}"
            # HTML 태그 제거
            title = re.sub(r'<[^>]+>', '', title)

            sections.append(Section(
                id=f"section_{i}",
                title=title,
                content=h2_tag + section_content.strip(),
                order=i
            ))
    else:
        # h2가 없으면 전체를 하나의 섹션으로
        sections.append(Section(
            id="section_1",
            title="본문",
            content=content,
            order=1
        ))

    return sections


@router.post("/generate", response_model=ArticleResponse)
async def generate_article(request: ArticleCreate):
    """
    실제 AI로 블로그 글 생성

    ContentGenerator를 사용하여 고품질 콘텐츠 생성
    """
    try:
        logger.info(f"Generating article for keyword: {request.keyword}")

        generator = ContentGenerator()

        # 에버그린 모드 확인
        is_evergreen = request.mode == "evergreen" or generator.is_evergreen_keyword(request.keyword)

        # 실제 글 생성
        post = generator.generate_full_post(
            keyword=request.keyword,
            news_data=""  # 대시보드에서는 뉴스 데이터 없이 생성
        )

        # 섹션 파싱
        sections = parse_sections(post.content)

        # 고유 ID 생성
        article_id = str(uuid.uuid4())[:8]

        article = {
            "id": article_id,
            "keyword": request.keyword,
            "title": post.title,
            "sections": [s.model_dump() for s in sections],
            "raw_content": post.content,
            "category": post.category,
            "template": post.template,
            "has_coupang": post.has_coupang,
            "sources": post.sources,
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "wp_url": None,
            "wp_id": None
        }

        # 저장소에 저장
        articles_store[article_id] = article

        logger.info(f"Article generated successfully: {article_id} - {post.title}")

        return ArticleResponse(
            id=article_id,
            keyword=request.keyword,
            title=post.title,
            sections=sections,
            raw_content=post.content,
            category=post.category,
            template=post.template,
            has_coupang=post.has_coupang,
            sources=post.sources,
            created_at=article["created_at"],
            status="draft"
        )

    except Exception as e:
        logger.error(f"Article generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"글 생성 실패: {str(e)}")


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """글 조회"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    # sections를 Section 객체로 변환
    sections = [Section(**s) for s in article["sections"]]

    return ArticleResponse(
        id=article["id"],
        keyword=article["keyword"],
        title=article["title"],
        sections=sections,
        raw_content=article["raw_content"],
        category=article.get("category", "트렌드"),
        template=article.get("template", "trend"),
        has_coupang=article.get("has_coupang", False),
        sources=article.get("sources", []),
        created_at=article["created_at"],
        status=article["status"],
        wp_url=article.get("wp_url"),
        wp_id=article.get("wp_id")
    )


@router.get("/", response_model=List[ArticleResponse])
async def list_articles():
    """모든 글 목록 조회"""
    articles = []
    for article in articles_store.values():
        sections = [Section(**s) for s in article["sections"]]
        articles.append(ArticleResponse(
            id=article["id"],
            keyword=article["keyword"],
            title=article["title"],
            sections=sections,
            raw_content=article["raw_content"],
            category=article.get("category", "트렌드"),
            template=article.get("template", "trend"),
            has_coupang=article.get("has_coupang", False),
            sources=article.get("sources", []),
            created_at=article["created_at"],
            status=article["status"],
            wp_url=article.get("wp_url"),
            wp_id=article.get("wp_id")
        ))

    # 최신순 정렬
    articles.sort(key=lambda x: x.created_at, reverse=True)
    return articles


@router.delete("/{article_id}")
async def delete_article(article_id: str):
    """글 삭제"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    del articles_store[article_id]
    return {"success": True, "message": "Article deleted"}


@router.post("/{article_id}/edit-section", response_model=SectionEditResponse)
async def edit_section(article_id: str, request: SectionEditRequest):
    """
    AI로 섹션 수정

    수정 지시에 따라 특정 섹션의 내용을 AI가 수정
    """
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    # 해당 섹션 찾기
    section_idx = None
    section = None
    for i, s in enumerate(article["sections"]):
        if s["id"] == request.section_id:
            section_idx = i
            section = s
            break

    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        # 직접 수정된 내용이 있으면 사용
        if request.new_content:
            edited_content = request.new_content
        else:
            # AI로 섹션 수정
            generator = ContentGenerator()

            edit_prompt = f"""다음 블로그 섹션 내용을 수정해주세요.

[원본 내용]
{section["content"]}

[수정 요청]
{request.instruction}

[키워드]
{article["keyword"]}

[규칙]
1. HTML 형식 유지
2. 자연스럽고 친근한 어투 유지
3. 수정된 HTML 내용만 출력 (다른 설명 없이)
4. 원본 구조(h2, p 태그 등) 유지
"""

            edited_content = generator._call_claude(edit_prompt, max_tokens=2000)

            # HTML 코드 블록 제거
            edited_content = re.sub(r'^```html\s*', '', edited_content, flags=re.MULTILINE)
            edited_content = re.sub(r'\s*```$', '', edited_content, flags=re.MULTILINE)
            edited_content = edited_content.strip()

        # 섹션 업데이트
        article["sections"][section_idx]["content"] = edited_content

        # raw_content도 업데이트 (섹션들을 다시 합침)
        article["raw_content"] = "".join([s["content"] for s in article["sections"]])

        updated_section = Section(**article["sections"][section_idx])

        logger.info(f"Section {request.section_id} edited successfully")

        return SectionEditResponse(
            success=True,
            section=updated_section
        )

    except Exception as e:
        logger.error(f"Section edit failed: {e}")
        return SectionEditResponse(
            success=False,
            error=str(e)
        )


@router.put("/{article_id}/title")
async def update_title(article_id: str, title: str):
    """제목 수정"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]
    article["title"] = title

    return {"success": True, "title": title}


@router.get("/keywords/suggestions", response_model=List[KeywordSuggestion])
async def get_keyword_suggestions():
    """
    키워드 추천 목록 반환

    Google Trends + 에버그린 키워드
    """
    try:
        suggestions = []

        # 에버그린 키워드 로드
        generator = ContentGenerator()
        evergreen_config = generator.evergreen_config

        for category, keywords in evergreen_config.get("keywords", {}).items():
            for kw in keywords[:3]:  # 카테고리당 3개
                suggestions.append(KeywordSuggestion(
                    keyword=kw,
                    category=category,
                    is_evergreen=True,
                    source="evergreen_config"
                ))

        # TODO: Google Trends 연동 (선택적)
        # from crawlers.google_trends import GoogleTrendsCrawler
        # trends = GoogleTrendsCrawler().get_trends()
        # for trend in trends[:5]:
        #     suggestions.append(KeywordSuggestion(
        #         keyword=trend["keyword"],
        #         category="트렌드",
        #         is_evergreen=False,
        #         source="google_trends"
        #     ))

        return suggestions

    except Exception as e:
        logger.error(f"Keyword suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
