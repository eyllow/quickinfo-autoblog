"""
WordPress 발행 API 라우터
SQLite DB 연동으로 발행 통계 영구 저장
"""
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from publishers.wordpress import WordPressPublisher, generate_tags
from dashboard.backend.models import PublishRequest, PublishResponse
from dashboard.backend.utils.log_manager import (
    log_info_sync, log_success_sync, log_error_sync, log_progress_sync
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publish", tags=["publish"])

# DB 경로 설정
DB_PATH = PROJECT_ROOT / "data" / "posts.db"


def get_db_connection():
    """SQLite DB 연결"""
    # data 폴더 없으면 생성
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """DB 테이블 초기화"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            keyword TEXT,
            category TEXT,
            wp_post_id INTEGER,
            wp_url TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info(f"SQLite DB initialized: {DB_PATH}")


# 앱 시작시 DB 초기화
init_db()


@router.get("/stats")
async def get_publish_stats():
    """
    발행 통계 조회 (SQLite DB 기반)

    오늘, 이번 주, 전체 발행 수 반환
    """
    try:
        conn = get_db_connection()

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        # 오늘 발행 수
        today_published = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published' AND created_at >= ?",
            (today_start.isoformat(),)
        ).fetchone()[0]

        # 이번 주 발행 수
        this_week = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published' AND created_at >= ?",
            (week_start.isoformat(),)
        ).fetchone()[0]

        # 전체 발행 수
        total_published = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status='published'"
        ).fetchone()[0]

        # 대기 중 (draft)
        drafts = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status='draft'"
        ).fetchone()[0]

        conn.close()

        return {
            "today_published": today_published,
            "this_week": this_week,
            "total_published": total_published,
            "drafts": drafts
        }
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        return {
            "today_published": 0,
            "this_week": 0,
            "total_published": 0,
            "drafts": 0
        }


@router.post("/", response_model=PublishResponse)
async def publish_article(request: PublishRequest):
    """
    실제 WordPress에 글 발행 및 DB 기록

    articles_store에서 글을 가져와 WordPress REST API로 발행
    """
    # articles_store 가져오기
    from dashboard.backend.routers.articles import articles_store

    if request.article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[request.article_id]
    title_short = article["title"][:30] + "..." if len(article["title"]) > 30 else article["title"]

    try:
        log_progress_sync("publish", f"WordPress 발행 준비 중: {title_short}")

        publisher = WordPressPublisher()

        # 태그 생성
        tags = generate_tags(
            keyword=article["keyword"],
            category=article.get("category", "트렌드")
        )

        log_info_sync("publish", f"카테고리: {article.get('category', '트렌드')}, 상태: {request.status}")

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
            # 글 상태 업데이트 (메모리)
            article["status"] = "published" if request.status == "publish" else "draft"
            article["wp_url"] = result.url
            article["wp_id"] = result.post_id

            # SQLite DB에 기록
            try:
                conn = get_db_connection()
                conn.execute(
                    """INSERT INTO posts (title, keyword, category, wp_post_id, wp_url, status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        article["title"],
                        article.get("keyword", ""),
                        article.get("category", "트렌드"),
                        result.post_id,
                        result.url,
                        "published" if request.status == "publish" else "draft"
                    )
                )
                conn.commit()
                conn.close()
                logger.info(f"Post recorded to DB: {article['title']}")
            except Exception as db_error:
                logger.error(f"DB 기록 실패: {db_error}")

            logger.info(f"Article published: {result.url}")
            log_success_sync("publish", f"✨ 발행 완료! Post ID: {result.post_id}", {"url": result.url})

            return PublishResponse(
                success=True,
                url=result.url,
                post_id=result.post_id
            )
        else:
            error_msg = result.error or "WordPress 발행 실패"
            logger.error(f"Publish failed: {error_msg}")
            log_error_sync("publish", f"발행 실패: {error_msg}")
            return PublishResponse(
                success=False,
                error=error_msg
            )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Publish error: {e}\n{error_detail}")
        log_error_sync("publish", f"발행 오류: {str(e)}")
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


@router.get("/recent")
async def get_recent_posts(limit: int = 10):
    """최근 발행 글 목록 (SQLite DB 기반)"""
    try:
        conn = get_db_connection()
        posts = conn.execute(
            """SELECT * FROM posts ORDER BY created_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        conn.close()

        return {
            "posts": [dict(post) for post in posts]
        }
    except Exception as e:
        logger.error(f"최근 글 조회 오류: {e}")
        return {"posts": []}
