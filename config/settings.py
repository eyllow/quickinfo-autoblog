"""환경변수 및 설정 관리"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # WordPress 설정
    wp_url: str
    wp_user: str
    wp_app_password: str

    # Claude API 설정
    claude_api_key: str

    # Pexels API 설정
    pexels_api_key: str = ""

    # Google Sheets 설정 (쿠팡 상품 DB)
    google_sheets_spreadsheet_id: str = ""
    google_credentials_path: str = str(BASE_DIR / "config" / "google_credentials.json")

    # Google Custom Search 설정
    google_search_api_key: str = ""
    google_search_engine_id: str = ""

    # 쿠팡 파트너스 설정
    coupang_partner_id: str

    # 발행 설정
    posts_per_day: int = 3
    publish_hour: int = 7

    # 데이터베이스 경로
    database_path: str = str(BASE_DIR / "database" / "blog_publisher.db")

    # 설정 파일 경로
    config_dir: str = str(BASE_DIR / "config")

    # Google Trends RSS URL
    google_trends_rss_url: str = "https://trends.google.com/trending/rss?geo=KR"

    # 네이버 검색 URL
    naver_search_url: str = "https://search.naver.com/search.naver"

    # AI Provider 설정 (gemini 또는 claude)
    ai_provider: str = "gemini"

    # Gemini 설정
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Claude 모델
    claude_model: str = "claude-3-5-haiku-20241022"

    # Pexels API URL
    pexels_api_url: str = "https://api.pexels.com/v1/search"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # GOOGLE_API_KEY 환경변수에서 gemini_api_key 로드
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GOOGLE_API_KEY", "")


# 싱글톤 설정 인스턴스
settings = Settings()
