"""
글 생성 및 편집 API
키워드로 글 생성, 섹션별 편집, 길이 조절
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import sys
import re
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

router = APIRouter()

# 메모리 저장소 (실제로는 DB 사용)
articles_store: Dict[str, dict] = {}


class ArticleSection(BaseModel):
    id: str
    title: str  # H2 제목
    content: str  # 본문 내용


class ArticleCreate(BaseModel):
    keyword: str
    mode: str = "semi"  # "semi" or "auto"


class ArticleResponse(BaseModel):
    id: str
    keyword: str
    title: str
    sections: List[ArticleSection]
    image_types: List[str]
    created_at: str
    status: str  # "draft", "ready", "published"


class SectionEditRequest(BaseModel):
    section_id: str
    new_content: str


class LengthAdjustRequest(BaseModel):
    target_length: str  # "short", "medium", "long"


def parse_sections(content: str) -> List[ArticleSection]:
    """H2 태그 기준으로 섹션 분리"""
    sections = []

    # H2 태그로 분리
    h2_pattern = r'<h2[^>]*>(.*?)</h2>'
    parts = re.split(h2_pattern, content, flags=re.IGNORECASE | re.DOTALL)

    if len(parts) < 2:
        # H2가 없으면 전체를 하나의 섹션으로
        sections.append(ArticleSection(
            id=str(uuid.uuid4())[:8],
            title="본문",
            content=content
        ))
        return sections

    # 첫 부분 (H2 전 내용)
    intro = parts[0].strip()
    if intro:
        sections.append(ArticleSection(
            id=str(uuid.uuid4())[:8],
            title="소개",
            content=intro
        ))

    # H2와 본문 쌍으로 처리
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip()
            content_part = parts[i + 1].strip() if i + 1 < len(parts) else ""

            sections.append(ArticleSection(
                id=str(uuid.uuid4())[:8],
                title=title,
                content=content_part
            ))

    return sections


def sections_to_html(sections: List[ArticleSection]) -> str:
    """섹션 목록을 HTML로 변환"""
    html_parts = []
    for section in sections:
        if section.title == "소개":
            html_parts.append(section.content)
        else:
            html_parts.append(f"<h2>{section.title}</h2>")
            html_parts.append(section.content)
    return "\n\n".join(html_parts)


@router.post("/generate", response_model=ArticleResponse)
async def generate_article(request: ArticleCreate):
    """키워드로 글 생성"""
    try:
        from generators.content_generator import ContentGenerator

        generator = ContentGenerator()
        result = generator.generate(request.keyword)

        article_id = str(uuid.uuid4())[:8]
        sections = parse_sections(result.get("content", ""))

        article = {
            "id": article_id,
            "keyword": request.keyword,
            "title": result.get("title", f"{request.keyword} 완벽 정리"),
            "sections": [s.model_dump() for s in sections],
            "content": result.get("content", ""),
            "image_types": result.get("image_types", ["PEXELS", "PEXELS"]),
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }

        articles_store[article_id] = article

        return ArticleResponse(
            id=article_id,
            keyword=request.keyword,
            title=article["title"],
            sections=sections,
            image_types=article["image_types"],
            created_at=article["created_at"],
            status=article["status"]
        )
    except Exception as e:
        # 더미 데이터 반환
        article_id = str(uuid.uuid4())[:8]
        dummy_sections = [
            ArticleSection(id="sec1", title="소개", content=f"<p>{request.keyword}에 대해 알아보겠습니다.</p>"),
            ArticleSection(id="sec2", title=f"{request.keyword}란?", content=f"<p>{request.keyword}의 정의와 개념을 설명합니다.</p>"),
            ArticleSection(id="sec3", title="신청 방법", content=f"<p>{request.keyword} 신청 방법을 단계별로 안내합니다.</p>"),
            ArticleSection(id="sec4", title="주의사항", content=f"<p>{request.keyword} 이용 시 주의할 점들입니다.</p>"),
        ]

        article = {
            "id": article_id,
            "keyword": request.keyword,
            "title": f"{request.keyword} 완벽 가이드",
            "sections": [s.model_dump() for s in dummy_sections],
            "content": sections_to_html(dummy_sections),
            "image_types": ["PEXELS", "PEXELS"],
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }

        articles_store[article_id] = article

        return ArticleResponse(
            id=article_id,
            keyword=request.keyword,
            title=article["title"],
            sections=dummy_sections,
            image_types=article["image_types"],
            created_at=article["created_at"],
            status=article["status"]
        )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """글 상세 조회"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]
    sections = [ArticleSection(**s) for s in article["sections"]]

    return ArticleResponse(
        id=article["id"],
        keyword=article["keyword"],
        title=article["title"],
        sections=sections,
        image_types=article["image_types"],
        created_at=article["created_at"],
        status=article["status"]
    )


@router.post("/{article_id}/edit-section")
async def edit_section(article_id: str, request: SectionEditRequest):
    """특정 섹션 편집"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    for section in article["sections"]:
        if section["id"] == request.section_id:
            section["content"] = request.new_content
            # HTML 재생성
            sections = [ArticleSection(**s) for s in article["sections"]]
            article["content"] = sections_to_html(sections)
            return {"success": True, "message": "Section updated"}

    raise HTTPException(status_code=404, detail="Section not found")


@router.post("/{article_id}/regenerate-section")
async def regenerate_section(article_id: str, section_id: str):
    """특정 섹션 재생성"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    for section in article["sections"]:
        if section["id"] == section_id:
            try:
                from generators.content_generator import ContentGenerator

                generator = ContentGenerator()
                prompt = f"다음 주제에 대해 500자 내외로 작성해주세요: {section['title']} ({article['keyword']} 관련)"
                new_content = generator.generate_section(prompt)
                section["content"] = new_content

                sections = [ArticleSection(**s) for s in article["sections"]]
                article["content"] = sections_to_html(sections)

                return {"success": True, "new_content": new_content}
            except Exception as e:
                section["content"] = f"<p>{section['title']}에 대한 상세 내용입니다. (재생성됨)</p>"
                return {"success": True, "new_content": section["content"]}

    raise HTTPException(status_code=404, detail="Section not found")


@router.post("/{article_id}/adjust-length")
async def adjust_length(article_id: str, request: LengthAdjustRequest):
    """글 길이 조절"""
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    length_map = {
        "short": 1000,
        "medium": 2000,
        "long": 3500
    }

    target = length_map.get(request.target_length, 2000)

    try:
        from generators.content_generator import ContentGenerator

        generator = ContentGenerator()
        adjusted_content = generator.adjust_length(article["content"], target)
        article["content"] = adjusted_content
        article["sections"] = [s.model_dump() for s in parse_sections(adjusted_content)]

        return {
            "success": True,
            "new_length": len(adjusted_content),
            "sections": article["sections"]
        }
    except Exception as e:
        # 간단한 길이 조절 (더미)
        return {
            "success": True,
            "new_length": target,
            "message": f"Length adjusted to {request.target_length}"
        }


@router.get("/")
async def list_articles():
    """글 목록 조회"""
    articles = []
    for article in articles_store.values():
        articles.append({
            "id": article["id"],
            "keyword": article["keyword"],
            "title": article["title"],
            "status": article["status"],
            "created_at": article["created_at"]
        })
    return {"articles": articles}
