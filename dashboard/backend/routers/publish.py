"""WordPress 발행 API 라우터"""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from publishers.wordpress import WordPressPublisher, generate_tags
from dashboard.backend.models import PublishRequest, PublishResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publish", tags=["publish"])


@router.get("/stats")
async def get_publish_stats():
    """
    발행 통계 조회

    오늘, 이번 주, 전체 발행 수 반환
    """
    from dashboard.backend.routers.articles import articles_store
    from datetime import datetime, timedelta

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    today_published = 0
    this_week = 0
    total_published = 0
    drafts = 0

    for article in articles_store.values():
        created_at = datetime.fromisoformat(article["created_at"])

        if article["status"] == "published":
            total_published += 1
            if created_at >= today_start:
                today_published += 1
            if created_at >= week_start:
                this_week += 1
        else:
            drafts += 1

    return {
        "today_published": today_published,
        "this_week": this_week,
        "total_published": total_published,
        "drafts": drafts
    }


@router.post("/", response_model=PublishResponse)
async def publish_article(request: PublishRequest):
    """
    실제 WordPress에 글 발행

    articles_store에서 글을 가져와 WordPress REST API로 발행
    """
    # articles_store 가져오기
    from dashboard.backend.routers.articles import articles_store

    if request.article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[request.article_id]

    try:
        publisher = WordPressPublisher()

        # 태그 생성
        tags = generate_tags(
            keyword=article["keyword"],
            category=article.get("category", "트렌드")
        )

        # 실제 발행
        result = publisher.publish_post(
            title=article["title"],
            content=article["raw_content"],
            status=request.status,
            categories=[article.get("category", "트렌드")],
            tags=tags,
            excerpt=article.get("excerpt", "")
        )

        if result.success and result.url:
            # 글 상태 업데이트
            article["status"] = "published" if request.status == "publish" else "draft"
            article["wp_url"] = result.url
            article["wp_id"] = result.post_id

            logger.info(f"Article published: {result.url}")

            return PublishResponse(
                success=True,
                url=result.url,
                post_id=result.post_id
            )
        else:
            error_msg = result.error or "WordPress 발행 실패"
            logger.error(f"Publish failed: {error_msg}")
            return PublishResponse(
                success=False,
                error=error_msg
            )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Publish error: {e}\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"발행 실패: {str(e)}\n{error_detail}")


@router.post("/{article_id}/draft")
async def save_as_draft(article_id: str):
    """
    WordPress에 임시저장 (draft)
    """
    return await publish_article(PublishRequest(
        article_id=article_id,
        status="draft"
    ))


@router.post("/{article_id}/publish")
async def publish_immediately(article_id: str):
    """
    WordPress에 즉시 발행
    """
    return await publish_article(PublishRequest(
        article_id=article_id,
        status="publish"
    ))


@router.get("/status/{article_id}")
async def get_publish_status(article_id: str):
    """
    발행 상태 확인
    """
    from dashboard.backend.routers.articles import articles_store

    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    return {
        "article_id": article_id,
        "status": article["status"],
        "wp_url": article.get("wp_url"),
        "wp_id": article.get("wp_id")
    }
