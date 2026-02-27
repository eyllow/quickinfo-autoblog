"""QuickInfo Dashboard API - FastAPI 메인 앱"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.backend.routers import articles_router, publish_router, images_router, sections_router
from dashboard.backend.routers.keywords import router as keywords_router
from dashboard.backend.routers.settings import router as settings_router
from dashboard.backend.routers.logs import router as logs_router
from dashboard.backend.routers.scheduler import router as scheduler_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    logger.info("QuickInfo Dashboard API starting...")
    yield
    logger.info("QuickInfo Dashboard API shutting down...")


# FastAPI 앱 생성
app = FastAPI(
    title="QuickInfo Dashboard API",
    description="블로그 자동 발행 대시보드 API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  # 307 리다이렉트 방지
)

# 프록시 헤더 처리 미들웨어 (Apache/Nginx 뒤에서 HTTPS 인식)
class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Apache/Nginx 리버스 프록시 뒤에서 HTTPS 스킴 올바르게 인식"""
    async def dispatch(self, request: Request, call_next):
        # X-Forwarded-Proto 헤더가 https면 스킴 변경
        if request.headers.get("x-forwarded-proto") == "https":
            request.scope["scheme"] = "https"
        response = await call_next(request)
        return response

# 미들웨어 등록 순서: 나중에 등록된 것이 먼저 실행됨
# ProxyHeaders → CORS 순서로 실행되도록 CORS 먼저 등록

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://admin.quickinfo.kr",
        "http://admin.quickinfo.kr",
        "*"  # 개발용 - 프로덕션에서는 제거
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프록시 헤더 미들웨어 추가
app.add_middleware(ProxyHeadersMiddleware)

# 라우터 등록
app.include_router(articles_router, prefix="/api")
app.include_router(publish_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(sections_router, prefix="/api")
app.include_router(keywords_router, prefix="/api/keywords", tags=["keywords"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(logs_router, prefix="/api", tags=["logs"])
app.include_router(scheduler_router, prefix="/api", tags=["scheduler"])


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "message": "QuickInfo Dashboard API is running",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """상세 헬스 체크"""
    return {
        "status": "healthy",
        "services": {
            "articles": "ok",
            "publish": "ok",
            "images": "ok"
        }
    }


@app.get("/api/stats")
async def get_stats():
    """대시보드 통계 (WP + DB 기반)"""
    import requests as _req
    import sqlite3
    from datetime import datetime as _dt, timedelta

    try:
        from config.settings import settings as _s

        # WP에서 글 수 조회
        published_count = 0
        draft_count = 0
        categories = {}

        for status in ["publish", "draft"]:
            resp = _req.get(
                f"{_s.wp_url}/wp-json/wp/v2/posts",
                params={"status": status, "per_page": 1, "_fields": "id"},
                auth=(_s.wp_user, _s.wp_app_password),
                timeout=5,
            )
            if resp.status_code == 200:
                total = int(resp.headers.get("X-WP-Total", 0))
                if status == "publish":
                    published_count = total
                else:
                    draft_count = total

        # DB에서 카테고리 통계
        db_path = Path(__file__).resolve().parent.parent.parent / "database" / "blog_publisher.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT category, COUNT(*) FROM published_posts GROUP BY category")
                for row in cursor.fetchall():
                    categories[row[0] or "트렌드"] = row[1]
            except Exception:
                pass
            conn.close()

        # 에버그린 키워드 풀 크기
        import json
        eg_path = Path(__file__).resolve().parent.parent.parent / "config" / "evergreen_keywords.json"
        keyword_pool = 0
        if eg_path.exists():
            eg_data = json.load(open(eg_path, encoding="utf-8"))
            keyword_pool = len(eg_data.get("keywords", []))

        return {
            "total_articles": published_count + draft_count,
            "published_count": published_count,
            "draft_count": draft_count,
            "categories": categories,
            "keyword_pool": keyword_pool,
            "target_for_adsense": 20,
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_articles": 0,
            "published_count": 0,
            "draft_count": 0,
            "categories": {},
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
