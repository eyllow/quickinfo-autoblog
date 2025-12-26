"""
설정 관리 모듈
환경 변수를 로드하고 전역 설정을 관리합니다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
load_dotenv(BASE_DIR / ".env")


class Settings:
    """애플리케이션 설정 클래스"""

    def __init__(self):
        # WordPress 설정
        self.wp_url = os.getenv("WP_URL", "")
        self.wp_user = os.getenv("WP_USER", "")
        self.wp_app_password = os.getenv("WP_APP_PASSWORD", "")

        # Claude API
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.claude_model = "claude-3-5-haiku-latest"

        # Google Custom Search
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID", "")

        # Pexels
        self.pexels_api_key = os.getenv("PEXELS_API_KEY", "")

        # 쿠팡 파트너스
        self.coupang_partner_id = os.getenv("COUPANG_PARTNER_ID", "")

        # 디렉토리 설정
        self.project_root = BASE_DIR
        self.logs_dir = BASE_DIR / "logs"
        self.log_path = self.logs_dir / "autoblog.log"
        self.db_path = BASE_DIR / "published_posts.db"

        # 로그 디렉토리 생성
        self.logs_dir.mkdir(exist_ok=True)

    def validate(self) -> bool:
        """필수 설정값 검증"""
        required = [
            ("WP_URL", self.wp_url),
            ("WP_USER", self.wp_user),
            ("WP_APP_PASSWORD", self.wp_app_password),
            ("ANTHROPIC_API_KEY", self.anthropic_api_key),
        ]

        missing = [name for name, value in required if not value]

        if missing:
            print(f"❌ 필수 환경 변수 누락: {', '.join(missing)}")
            return False

        return True

    def print_status(self):
        """설정 상태 출력"""
        print("\n📋 설정 상태:")
        print(f"  WordPress URL: {self.wp_url}")
        print(f"  WordPress User: {self.wp_user}")
        print(f"  Claude API: {'✅ 설정됨' if self.anthropic_api_key else '❌ 미설정'}")
        print(f"  Google Search: {'✅ 설정됨' if self.google_api_key else '❌ 미설정'}")
        print(f"  Pexels: {'✅ 설정됨' if self.pexels_api_key else '❌ 미설정'}")
        print(f"  쿠팡 파트너스 ID: {self.coupang_partner_id or '❌ 미설정'}")
        print()


# 전역 설정 인스턴스
settings = Settings()
