"""QuickInfo Dashboard API - FastAPI 메인 앱"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.backend.routers import articles_router, publish_router, images_router
from dashboard.backend.routers.keywords import router as keywords_router
from dashboard.backend.routers.settings import router as settings_router

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
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # 개발용 - 프로덕션에서는 제거
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(articles_router, prefix="/api")
app.include_router(publish_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(keywords_router, prefix="/api/keywords", tags=["keywords"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])


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
    """대시보드 통계"""
    from dashboard.backend.routers.articles import articles_store

    # 카테고리별 통계
    categories = {}
    published_count = 0
    draft_count = 0

    for article in articles_store.values():
        cat = article.get("category", "트렌드")
        categories[cat] = categories.get(cat, 0) + 1

        if article["status"] == "published":
            published_count += 1
        else:
            draft_count += 1

    return {
        "total_articles": len(articles_store),
        "published_count": published_count,
        "draft_count": draft_count,
        "categories": categories
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
