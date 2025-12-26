"""
스크린샷 캡쳐 모듈 (선택적 기능)
특정 URL의 스크린샷을 캡쳐합니다.

참고: 이 기능은 Puppeteer/Node.js가 필요합니다.
서버 환경에서는 별도 설치가 필요할 수 있습니다.
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 키워드별 스크린샷 대상 URL
SCREENSHOT_TARGETS = {
    "환율": {
        "url": "https://finance.naver.com/marketindex/",
        "name": "네이버 금융",
    },
    "비트코인": {
        "url": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC",
        "name": "업비트",
    },
    "코스피": {
        "url": "https://finance.naver.com/sise/",
        "name": "네이버 증권",
    },
    "날씨": {
        "url": "https://weather.naver.com/",
        "name": "네이버 날씨",
    },
    "연말정산": {
        "url": "https://www.hometax.go.kr/",
        "name": "홈택스",
    },
}


def get_screenshot_url(keyword: str) -> Optional[dict]:
    """
    키워드에 맞는 스크린샷 대상 URL 반환

    Args:
        keyword: 키워드

    Returns:
        URL 정보 또는 None
    """
    for key, info in SCREENSHOT_TARGETS.items():
        if key in keyword:
            return info
    return None


def capture_screenshot(url: str, output_path: str = None) -> Optional[str]:
    """
    URL 스크린샷 캡쳐

    참고: 이 함수는 Puppeteer가 설치되어 있어야 합니다.
    실제 사용 시에는 별도의 스크린샷 스크립트가 필요합니다.

    Args:
        url: 캡쳐할 URL
        output_path: 저장 경로 (없으면 임시 파일)

    Returns:
        스크린샷 파일 경로 또는 None
    """
    logger.info(f"스크린샷 기능은 별도 설정이 필요합니다: {url}")
    logger.info("Puppeteer 또는 Selenium 설치 후 사용하세요.")

    # 실제 구현은 별도 Node.js 스크립트 또는 Selenium 사용
    # 여기서는 플레이스홀더만 제공

    return None


def is_screenshot_available() -> bool:
    """
    스크린샷 기능 사용 가능 여부 확인

    Returns:
        사용 가능 여부
    """
    # Node.js/Puppeteer 또는 Selenium 설치 확인
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 스크린샷 기능 테스트 ===\n")

    print(f"스크린샷 기능 사용 가능: {is_screenshot_available()}")
    print()

    # 키워드별 대상 URL 확인
    keywords = ["환율", "비트코인", "연말정산", "다이어트"]
    for kw in keywords:
        target = get_screenshot_url(kw)
        if target:
            print(f"{kw}: {target['name']} ({target['url']})")
        else:
            print(f"{kw}: 스크린샷 대상 없음")
