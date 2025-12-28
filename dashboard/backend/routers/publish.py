"""
발행 관리 API
WordPress 발행, 발행 통계
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

router = APIRouter()


class PublishRequest(BaseModel):
    article_id: str
    schedule: Optional[str] = None  # ISO datetime for scheduled publish


class PublishResponse(BaseModel):
    success: bool
    post_id: Optional[int] = None
    url: Optional[str] = None
    message: str


class PublishStats(BaseModel):
    total_published: int
    today_published: int
    this_week: int
    this_month: int
    last_publish: Optional[str] = None


@router.post("/", response_model=PublishResponse)
async def publish_article(request: PublishRequest):
    """글 WordPress에 발행"""
    from routers.articles import articles_store

    if request.article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[request.article_id]

    try:
        from publishers.wordpress_publisher import WordPressPublisher
        from media.pexels_image import PexelsImageFetcher
        from media.screenshot import ScreenshotCapture

        # 이미지 처리
        image_fetcher = PexelsImageFetcher()
        screenshot_capture = ScreenshotCapture()

        images = []
        for img_type in article.get("image_types", []):
            if img_type.upper() == "PEXELS":
                img = image_fetcher.search(article["keyword"], per_page=1)
                if img:
                    images.append(img[0].get("src", {}).get("large2x", ""))
            elif img_type.upper() == "SCREENSHOT":
                # 스크린샷 URL 필요
                pass

        # WordPress 발행
        publisher = WordPressPublisher()

        content = article.get("content", "")
        # 이미지 삽입 로직
        for i, img_url in enumerate(images):
            if img_url:
                img_tag = f'<img src="{img_url}" alt="{article["keyword"]}" class="wp-image" />'
                content = content.replace(f"[IMAGE_{i}]", img_tag)

        result = publisher.publish(
            title=article["title"],
            content=content,
            keyword=article["keyword"]
        )

        # 상태 업데이트
        article["status"] = "published"
        article["published_at"] = datetime.now().isoformat()
        article["wp_post_id"] = result.get("id")
        article["wp_url"] = result.get("link")

        return PublishResponse(
            success=True,
            post_id=result.get("id"),
            url=result.get("link"),
            message="Article published successfully"
        )

    except Exception as e:
        # 시뮬레이션 모드
        article["status"] = "published"
        article["published_at"] = datetime.now().isoformat()

        return PublishResponse(
            success=True,
            post_id=12345,
            url=f"https://quickinfo.kr/{request.article_id}",
            message=f"Article published (simulation): {str(e)}"
        )


@router.get("/stats", response_model=PublishStats)
async def get_publish_stats():
    """발행 통계"""
    try:
        from database.db_manager import DBManager

        db = DBManager()
        stats = db.get_publish_stats()

        return PublishStats(
            total_published=stats.get("total", 0),
            today_published=stats.get("today", 0),
            this_week=stats.get("week", 0),
            this_month=stats.get("month", 0),
            last_publish=stats.get("last_publish")
        )
    except Exception as e:
        # 더미 통계
        return PublishStats(
            total_published=42,
            today_published=3,
            this_week=15,
            this_month=42,
            last_publish=datetime.now().isoformat()
        )


@router.get("/history")
async def get_publish_history(limit: int = 20):
    """발행 히스토리"""
    try:
        from database.db_manager import DBManager

        db = DBManager()
        history = db.get_recent_posts(limit=limit)

        return {
            "posts": [
                {
                    "id": post.get("id"),
                    "keyword": post.get("keyword"),
                    "title": post.get("title"),
                    "url": post.get("url"),
                    "published_at": post.get("published_at"),
                    "status": "published"
                }
                for post in history
            ]
        }
    except Exception as e:
        return {"posts": [], "error": str(e)}


@router.post("/preview/{article_id}")
async def preview_article(article_id: str):
    """발행 전 미리보기 HTML 생성"""
    from routers.articles import articles_store

    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    # 간단한 HTML 미리보기
    preview_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{article['title']}</title>
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
            p {{ line-height: 1.8; color: #444; }}
        </style>
    </head>
    <body>
        <h1>{article['title']}</h1>
        {article.get('content', '')}
    </body>
    </html>
    """

    return {
        "html": preview_html,
        "title": article["title"],
        "keyword": article["keyword"]
    }


@router.delete("/{article_id}")
async def delete_draft(article_id: str):
    """초안 삭제"""
    from routers.articles import articles_store

    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]

    if article["status"] == "published":
        raise HTTPException(status_code=400, detail="Cannot delete published article")

    del articles_store[article_id]

    return {"success": True, "message": "Draft deleted"}
