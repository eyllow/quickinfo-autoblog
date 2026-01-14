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
    AdjustLengthRequest,
    AdjustLengthResponse,
    NaturalEditRequest,
    NaturalEditResponse,
    ElementEditRequest,
    ElementEditResponse,
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
    섹션은 ContentGenerator에서 직접 파싱하여 반환

    custom_context가 있으면 "직접 작성" 모드로 사용자 지정 방향 반영
    """
    # 실시간 로그 임포트
    from dashboard.backend.utils.log_manager import (
        log_info, log_success, log_error, log_progress, log_warning
    )

    try:
        logger.info(f"Generating article for keyword: {request.keyword}")

        # 로그: 키워드 선택
        category_str = request.category or "자동 분류"
        await log_info("keyword", f"키워드 선택: '{request.keyword}' (카테고리: {category_str})")

        # 직접 작성 모드 확인
        if request.custom_context:
            logger.info(f"Custom context mode: {request.custom_context[:100]}...")
            await log_info("keyword", f"직접 작성 모드: 사용자 방향 적용")

        generator = ContentGenerator()

        # 에버그린 모드 확인 (is_evergreen 또는 mode로 판단)
        is_evergreen = request.is_evergreen or request.mode == "evergreen" or generator.is_evergreen_keyword(request.keyword)

        # 로그: 콘텐츠 생성 시작
        await log_progress("generate", "AI 콘텐츠 생성 시작...")

        # 실제 글 생성 (섹션 포함)
        # custom_context가 있으면 직접 작성 모드
        post = generator.generate_full_post(
            keyword=request.keyword,
            news_data="",  # 대시보드에서는 뉴스 데이터 없이 생성
            custom_context=request.custom_context,  # 사용자 작성 방향
            force_category=request.category  # 사용자 지정 카테고리
        )

        # 로그: 콘텐츠 생성 완료
        await log_success("generate", f"콘텐츠 생성 완료 ({len(post.content)}자)", {"title": post.title[:30]})

        # 고유 ID 생성
        article_id = str(uuid.uuid4())[:8]

        # 섹션을 딕셔너리로 변환 (GeneratedPost.sections는 Section 객체 리스트)
        sections_dict = [
            {"id": s.id, "index": s.index, "type": s.type, "html": s.html}
            for s in post.sections
        ] if post.sections else []

        # 로그: 섹션 처리
        await log_info("generate", f"섹션 분리 완료: {len(sections_dict)}개 섹션")

        # 호환성을 위해 기존 Section 모델도 생성
        legacy_sections = []
        for i, s in enumerate(sections_dict):
            # 제목 추출 (h 태그에서)
            title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', s["html"], re.IGNORECASE | re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else f"섹션 {i+1}"

            legacy_sections.append(Section(
                id=s["id"],
                title=title,
                content=s["html"],
                order=i
            ))

        article = {
            "id": article_id,
            "keyword": request.keyword,
            "title": post.title,
            "sections": [s.model_dump() for s in legacy_sections],  # 기존 호환용
            "sections_v2": sections_dict,  # 새 섹션 구조
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

        logger.info(f"Article generated successfully: {article_id} - {post.title} ({len(sections_dict)} sections)")

        # 로그: 완료
        await log_success("generate", f"글 생성 완료! (ID: {article_id})")

        return ArticleResponse(
            id=article_id,
            keyword=request.keyword,
            title=post.title,
            sections=legacy_sections,
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
        await log_error("generate", f"글 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"글 생성 실패: {str(e)}")


@router.get("/recent")
async def get_recent_posts(limit: int = 5):
    """최근 발행된 글 목록"""
    try:
        import sqlite3

        db_path = PROJECT_ROOT / "data" / "blog.db"

        if not db_path.exists():
            return {"posts": []}

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, category, url, created_at as published_at
            FROM posts
            WHERE status = 'published'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"posts": posts}
    except Exception as e:
        logger.error(f"Failed to get recent posts: {e}")
        return {"posts": []}


@router.get("/stats")
async def get_article_stats():
    """발행 통계"""
    try:
        import sqlite3
        from datetime import timedelta

        db_path = PROJECT_ROOT / "data" / "blog.db"

        if not db_path.exists():
            return {
                "today": 0,
                "thisWeek": 0,
                "total": 0,
                "pending": 0,
                "yesterdayTotal": 0
            }

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")

        # 오늘 발행 수
        cursor.execute("SELECT COUNT(*) FROM posts WHERE status='published' AND date(created_at)=?", (today,))
        today_count = cursor.fetchone()[0]

        # 어제 발행 수
        cursor.execute("SELECT COUNT(*) FROM posts WHERE status='published' AND date(created_at)=?", (yesterday,))
        yesterday_count = cursor.fetchone()[0]

        # 이번 주 발행 수
        cursor.execute("SELECT COUNT(*) FROM posts WHERE status='published' AND date(created_at)>=?", (week_start,))
        week_count = cursor.fetchone()[0]

        # 전체 발행 수
        cursor.execute("SELECT COUNT(*) FROM posts WHERE status='published'")
        total_count = cursor.fetchone()[0]

        # 대기 중
        cursor.execute("SELECT COUNT(*) FROM posts WHERE status='draft' OR status='pending'")
        pending_count = cursor.fetchone()[0]

        conn.close()

        return {
            "today": today_count,
            "thisWeek": week_count,
            "total": total_count,
            "pending": pending_count,
            "yesterdayTotal": yesterday_count
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "today": 0,
            "thisWeek": 0,
            "total": 0,
            "pending": 0,
            "yesterdayTotal": 0
        }


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


@router.put("/{article_id}/content")
async def update_content(article_id: str, request: dict):
    """
    글 내용 업데이트 (발행 전 로컬 수정사항 동기화용)
    """
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    content = request.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    article = articles_store[article_id]
    article["raw_content"] = content
    article["sections"] = [s.model_dump() for s in parse_sections(content)]

    logger.info(f"Article content updated: {article_id}")

    return {"success": True, "message": "Content updated"}


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


@router.post("/{article_id}/adjust-length", response_model=AdjustLengthResponse)
async def adjust_article_length(article_id: str, request: AdjustLengthRequest):
    """
    글 길이 조절

    target_length: "short" (줄이기) 또는 "long" (늘리기)
    """
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]
    current_length = len(article["raw_content"])

    try:
        generator = ContentGenerator()

        if request.target_length == "short":
            target = int(current_length * 0.7)
            instruction = "내용을 더 간결하게 요약하고, 핵심만 남겨주세요. 약 30% 줄여주세요."
        else:  # long
            target = int(current_length * 1.3)
            instruction = "내용을 더 상세하게 보충하고, 예시나 설명을 추가해주세요. 약 30% 늘려주세요."

        edit_prompt = f"""다음 블로그 글을 수정해주세요.

[원본 내용]
{article["raw_content"]}

[수정 요청]
{instruction}

[키워드]
{article["keyword"]}

[규칙]
1. HTML 형식 유지
2. 자연스럽고 친근한 어투 유지
3. 수정된 HTML 내용만 출력 (다른 설명 없이)
4. 원본 구조(h2, p 태그 등) 유지
"""

        edited_content = generator._call_claude(edit_prompt, max_tokens=8000)

        # HTML 코드 블록 제거
        edited_content = re.sub(r'^```html\s*', '', edited_content, flags=re.MULTILINE)
        edited_content = re.sub(r'\s*```$', '', edited_content, flags=re.MULTILINE)
        edited_content = edited_content.strip()

        # 업데이트
        article["raw_content"] = edited_content
        article["sections"] = [s.model_dump() for s in parse_sections(edited_content)]

        new_length = len(edited_content)
        logger.info(f"Article length adjusted: {current_length} -> {new_length}")

        return AdjustLengthResponse(
            success=True,
            new_length=new_length
        )

    except Exception as e:
        logger.error(f"Adjust length failed: {e}")
        return AdjustLengthResponse(
            success=False,
            error=str(e)
        )


@router.post("/edit-element", response_model=ElementEditResponse)
async def edit_element(request: ElementEditRequest):
    """
    개별 요소 수정 (서버 저장 없음)

    프론트엔드에서 섹션 단위로 수정 요청을 보내면,
    AI가 해당 요소만 수정하여 반환합니다.
    서버의 article_store는 건드리지 않습니다.
    """
    try:
        generator = ContentGenerator()

        type_labels = {
            'title': '제목',
            'paragraph': '문단',
            'list': '리스트',
            'table': '표',
            'quote': '인용문',
            'image': '이미지',
            'other': '요소'
        }
        type_label = type_labels.get(request.element_type, '요소')

        edit_prompt = f"""다음 블로그 {type_label}을 수정해주세요.

[현재 내용]
{request.element_content}

[수정 요청]
{request.instruction}

{f'[키워드] {request.keyword}' if request.keyword else ''}

[규칙]
1. 같은 HTML 태그 구조 유지 (예: h2는 h2로, p는 p로)
2. 요청된 수정사항만 반영
3. 자연스럽고 친근한 어투 유지
4. 수정된 HTML만 출력 (설명 없이)
"""

        edited_content = generator._call_claude(edit_prompt, max_tokens=2000)

        # HTML 코드 블록 제거
        edited_content = re.sub(r'^```html\s*', '', edited_content, flags=re.MULTILINE)
        edited_content = re.sub(r'\s*```$', '', edited_content, flags=re.MULTILINE)
        edited_content = edited_content.strip()

        logger.info(f"Element edited successfully: {request.element_type}")

        return ElementEditResponse(
            success=True,
            updated_content=edited_content
        )

    except Exception as e:
        logger.error(f"Element edit failed: {e}")
        return ElementEditResponse(
            success=False,
            error=str(e)
        )


def extract_number_from_text(text: str) -> Optional[int]:
    """텍스트에서 숫자 추출 (첫 번째, 두 번째 등)"""
    korean_numbers = {
        '첫': 1, '첫번째': 1, '첫 번째': 1, '1번째': 1,
        '두': 2, '두번째': 2, '두 번째': 2, '2번째': 2,
        '세': 3, '세번째': 3, '세 번째': 3, '3번째': 3,
        '네': 4, '네번째': 4, '네 번째': 4, '4번째': 4,
        '다섯': 5, '다섯번째': 5, '다섯 번째': 5, '5번째': 5,
    }
    for k, v in korean_numbers.items():
        if k in text:
            return v
    # 숫자만 있는 경우
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None


@router.post("/{article_id}/natural-edit", response_model=NaturalEditResponse)
async def natural_edit(article_id: str, request: NaturalEditRequest):
    """
    자연어 수정 요청 처리

    다양한 수정 요청을 자연어로 받아 처리:
    - URL 스크린샷 요청
    - 이미지 삭제/교체
    - 섹션 수정
    - 전체 글 수정
    """
    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]
    instruction = request.instruction.strip()

    try:
        # 1. URL 스크린샷 요청 감지
        url_match = re.search(r'https?://[^\s]+', instruction)
        if url_match and ('스크린샷' in instruction or '캡처' in instruction or '화면' in instruction):
            url = url_match.group().rstrip('.,!?')
            logger.info(f"Screenshot request detected: {url}")

            try:
                from utils.unique_image import generate_unique_screenshot

                # 스크린샷 생성
                keyword = article["keyword"]
                screenshot_path = generate_unique_screenshot(keyword, url=url)

                if screenshot_path:
                    # WordPress에 업로드
                    from utils.image_fetcher import ImageFetcher
                    fetcher = ImageFetcher()
                    uploaded_url = fetcher.upload_to_wordpress_media(
                        screenshot_path,
                        alt_text=f"{keyword} 관련 스크린샷"
                    )

                    if uploaded_url:
                        # 콘텐츠에 이미지 추가 또는 교체
                        img_tag = f'<figure class="wp-block-image"><img src="{uploaded_url}" alt="{keyword} 스크린샷"/></figure>'

                        # 첫 번째 섹션 끝에 이미지 추가
                        if article["sections"]:
                            article["sections"][0]["content"] += img_tag
                            article["raw_content"] = "".join([s["content"] for s in article["sections"]])

                        return NaturalEditResponse(
                            success=True,
                            action_type="screenshot",
                            message=f"스크린샷이 추가되었습니다: {url}",
                            updated_content=article["raw_content"]
                        )
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                return NaturalEditResponse(
                    success=False,
                    action_type="screenshot",
                    error=f"스크린샷 생성 실패: {str(e)}"
                )

        # 2. 이미지 삭제 요청 감지
        if '이미지' in instruction and '삭제' in instruction:
            img_index = extract_number_from_text(instruction)
            if img_index is None:
                img_index = 1  # 기본값

            logger.info(f"Image delete request: index {img_index}")

            # 이미지 태그 찾아서 삭제
            content = article["raw_content"]
            img_patterns = [
                r'<figure[^>]*>.*?<img[^>]*>.*?</figure>',
                r'<img[^>]*/?>'
            ]

            for pattern in img_patterns:
                matches = list(re.finditer(pattern, content, re.DOTALL))
                if len(matches) >= img_index:
                    match = matches[img_index - 1]
                    content = content[:match.start()] + content[match.end():]
                    break

            article["raw_content"] = content
            article["sections"] = [s.model_dump() for s in parse_sections(content)]

            return NaturalEditResponse(
                success=True,
                action_type="image_delete",
                message=f"{img_index}번째 이미지가 삭제되었습니다.",
                updated_content=content
            )

        # 3. 이미지 검색/교체 요청 감지
        if '이미지' in instruction and ('바꿔' in instruction or '교체' in instruction or '변경' in instruction):
            # 검색어 추출 시도
            search_query = article["keyword"]  # 기본값

            # "세금 관련 이미지로" 같은 패턴에서 검색어 추출
            query_match = re.search(r'(.+?)\s*(관련|이미지|사진)', instruction)
            if query_match:
                search_query = query_match.group(1).strip()

            logger.info(f"Image replace request: query '{search_query}'")

            try:
                from utils.image_fetcher import ImageFetcher
                fetcher = ImageFetcher()
                photos = fetcher.search_pexels_single(search_query, per_page=1)

                if photos:
                    photo = photos[0]
                    img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")

                    if img_url:
                        img_index = extract_number_from_text(instruction) or 1

                        # 이미지 교체
                        content = article["raw_content"]
                        new_img = f'<figure class="wp-block-image"><img src="{img_url}" alt="{search_query}"/></figure>'

                        img_patterns = [
                            r'<figure[^>]*>.*?<img[^>]*>.*?</figure>',
                            r'<img[^>]*/?>'
                        ]

                        replaced = False
                        for pattern in img_patterns:
                            matches = list(re.finditer(pattern, content, re.DOTALL))
                            if len(matches) >= img_index:
                                match = matches[img_index - 1]
                                content = content[:match.start()] + new_img + content[match.end():]
                                replaced = True
                                break

                        if not replaced:
                            # 이미지가 없으면 첫 섹션에 추가
                            if article["sections"]:
                                article["sections"][0]["content"] += new_img
                                content = "".join([s["content"] for s in article["sections"]])

                        article["raw_content"] = content
                        article["sections"] = [s.model_dump() for s in parse_sections(content)]

                        return NaturalEditResponse(
                            success=True,
                            action_type="image_replace",
                            message=f"이미지가 '{search_query}' 검색 결과로 교체되었습니다.",
                            updated_content=content
                        )
            except Exception as e:
                logger.error(f"Image replace failed: {e}")

        # 4. 섹션 수정 요청 (AI 처리)
        section_index = extract_number_from_text(instruction)

        if section_index and section_index <= len(article["sections"]):
            # 특정 섹션 수정
            target_section = article["sections"][section_index - 1]
            logger.info(f"Section edit request: section {section_index}")
        elif request.section_id:
            # section_id로 지정된 경우
            target_section = None
            section_index = None
            for i, s in enumerate(article["sections"]):
                if s["id"] == request.section_id:
                    target_section = s
                    section_index = i + 1
                    break
        else:
            # 전체 글 수정
            target_section = None
            section_index = None

        generator = ContentGenerator()

        if target_section:
            # 특정 섹션만 수정
            edit_prompt = f"""다음 블로그 섹션을 수정해주세요.

[원본 내용]
{target_section["content"]}

[수정 요청]
{instruction}

[키워드]
{article["keyword"]}

[규칙]
1. HTML 형식 유지
2. 자연스럽고 친근한 어투
3. 수정된 HTML만 출력
"""
            edited = generator._call_claude(edit_prompt, max_tokens=3000)
            edited = re.sub(r'^```html\s*', '', edited, flags=re.MULTILINE)
            edited = re.sub(r'\s*```$', '', edited, flags=re.MULTILINE)
            edited = edited.strip()

            article["sections"][section_index - 1]["content"] = edited
            article["raw_content"] = "".join([s["content"] for s in article["sections"]])

            return NaturalEditResponse(
                success=True,
                action_type="section_edit",
                message=f"{section_index}번째 섹션이 수정되었습니다.",
                updated_content=article["raw_content"]
            )
        else:
            # 전체 글 수정
            edit_prompt = f"""다음 블로그 글 전체를 수정해주세요.

[원본 내용]
{article["raw_content"]}

[수정 요청]
{instruction}

[키워드]
{article["keyword"]}

[규칙]
1. HTML 형식 유지
2. 자연스럽고 친근한 어투
3. 기존 구조(h2, p 등) 유지
4. 수정된 HTML만 출력
"""
            edited = generator._call_claude(edit_prompt, max_tokens=8000)
            edited = re.sub(r'^```html\s*', '', edited, flags=re.MULTILINE)
            edited = re.sub(r'\s*```$', '', edited, flags=re.MULTILINE)
            edited = edited.strip()

            article["raw_content"] = edited
            article["sections"] = [s.model_dump() for s in parse_sections(edited)]

            return NaturalEditResponse(
                success=True,
                action_type="full_edit",
                message="전체 글이 수정되었습니다.",
                updated_content=edited
            )

    except Exception as e:
        logger.error(f"Natural edit failed: {e}")
        import traceback
        traceback.print_exc()
        return NaturalEditResponse(
            success=False,
            error=str(e)
        )


