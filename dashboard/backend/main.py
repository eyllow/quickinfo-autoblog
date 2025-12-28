"""
QuickInfo Dashboard API
반자동/자동 통합 발행 대시보드 백엔드
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# 기존 autoblog 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from routers import keywords, articles, images, publish, settings

app = FastAPI(
    title="QuickInfo Dashboard API",
    description="반자동/자동 통합 발행 대시보드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(keywords.router, prefix="/api/keywords", tags=["keywords"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(publish.router, prefix="/api/publish", tags=["publish"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
def root():
    return {"message": "QuickInfo Dashboard API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
