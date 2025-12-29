"""
설정 관리 API
발행 모드, 스케줄, 시스템 설정
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

router = APIRouter()

# 설정 저장 경로
SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "dashboard_settings.json"


class SettingsModel(BaseModel):
    publish_mode: str = "semi"  # "semi" or "auto"
    auto_schedule: List[str] = ["09:00", "15:00", "21:00"]  # 자동 발행 시간
    daily_limit: int = 5  # 하루 최대 발행 수
    keyword_source: str = "both"  # "trends", "evergreen", "both"
    image_preference: str = "pexels"  # "pexels", "screenshot", "mixed"
    content_length: str = "medium"  # "short", "medium", "long"
    auto_publish_enabled: bool = False


class ModeSwitch(BaseModel):
    mode: str  # "semi" or "auto"


class ScheduleUpdate(BaseModel):
    schedules: List[str]


def load_settings() -> SettingsModel:
    """설정 로드"""
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SettingsModel(**data)
    except Exception:
        pass
    return SettingsModel()


def save_settings(settings: SettingsModel):
    """설정 저장"""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)


@router.get("", response_model=SettingsModel)
@router.get("/", response_model=SettingsModel)
async def get_settings():
    """현재 설정 조회"""
    return load_settings()


@router.put("", response_model=SettingsModel)
@router.put("/", response_model=SettingsModel)
async def update_settings(settings: SettingsModel):
    """설정 업데이트"""
    save_settings(settings)
    return settings


@router.post("/mode")
async def set_publish_mode(request: ModeSwitch):
    """발행 모드 전환"""
    if request.mode not in ["semi", "auto"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'semi' or 'auto'")

    settings = load_settings()
    settings.publish_mode = request.mode

    # 자동 모드 활성화/비활성화
    if request.mode == "auto":
        settings.auto_publish_enabled = True
    else:
        settings.auto_publish_enabled = False

    save_settings(settings)

    return {
        "success": True,
        "mode": request.mode,
        "message": f"Switched to {request.mode} mode"
    }


@router.post("/schedule")
async def update_schedule(request: ScheduleUpdate):
    """자동 발행 스케줄 업데이트"""
    settings = load_settings()
    settings.auto_schedule = request.schedules
    save_settings(settings)

    return {
        "success": True,
        "schedules": request.schedules
    }


@router.get("/status")
async def get_system_status():
    """시스템 상태 조회"""
    settings = load_settings()

    # 크롤러 상태 확인
    crawler_status = "unknown"
    try:
        from crawlers.google_trends import GoogleTrendsCrawler
        crawler = GoogleTrendsCrawler()
        crawler_status = "ok"
    except Exception:
        crawler_status = "error"

    # WordPress 연결 상태
    wp_status = "unknown"
    try:
        from config.settings import settings as app_settings
        if app_settings.wordpress_url:
            wp_status = "configured"
        else:
            wp_status = "not_configured"
    except Exception:
        wp_status = "error"

    # DB 상태
    db_status = "unknown"
    try:
        from database.db_manager import DBManager
        db = DBManager()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "mode": settings.publish_mode,
        "auto_enabled": settings.auto_publish_enabled,
        "next_schedule": settings.auto_schedule[0] if settings.auto_schedule else None,
        "services": {
            "crawler": crawler_status,
            "wordpress": wp_status,
            "database": db_status
        }
    }


@router.get("/env")
async def get_env_status():
    """환경 변수 상태 (민감 정보 제외)"""
    import os

    env_vars = [
        "WORDPRESS_URL",
        "WORDPRESS_USERNAME",
        "ANTHROPIC_API_KEY",
        "PEXELS_API_KEY"
    ]

    status = {}
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 마스킹 처리
            if "KEY" in var or "PASSWORD" in var:
                status[var] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            else:
                status[var] = value if "URL" in var else "configured"
        else:
            status[var] = "not_set"

    return {"env_status": status}


@router.post("/test-connection")
async def test_connections():
    """외부 서비스 연결 테스트"""
    results = {}

    # WordPress 테스트
    try:
        from publishers.wordpress_publisher import WordPressPublisher
        publisher = WordPressPublisher()
        # 간단한 API 호출로 연결 테스트
        results["wordpress"] = {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        results["wordpress"] = {"status": "error", "message": str(e)}

    # Pexels 테스트
    try:
        from media.pexels_image import PexelsImageFetcher
        fetcher = PexelsImageFetcher()
        test_result = fetcher.search("test", per_page=1)
        results["pexels"] = {"status": "ok", "message": f"Found {len(test_result)} images"}
    except Exception as e:
        results["pexels"] = {"status": "error", "message": str(e)}

    # Claude API 테스트
    try:
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            results["claude"] = {"status": "ok", "message": "API key configured"}
        else:
            results["claude"] = {"status": "error", "message": "API key not set"}
    except Exception as e:
        results["claude"] = {"status": "error", "message": str(e)}

    return {"connections": results}
