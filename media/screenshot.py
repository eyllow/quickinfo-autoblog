"""
스크린샷 캡처 모듈
Puppeteer를 사용하여 웹페이지 스크린샷을 캡처합니다.
"""
import json
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# 현재 파일 디렉토리
SCRIPT_DIR = Path(__file__).resolve().parent
SCREENSHOT_SCRIPT = SCRIPT_DIR / "screenshot.js"

# Puppeteer/Chrome 실행 옵션 (서버 환경 호환)
CHROME_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--single-process',
    '--no-zygote',
    '--disable-extensions',
    '--disable-background-networking',
]

# 인물/연예인 키워드 패턴
PERSON_KEYWORDS = [
    # 연예인
    "혜리", "손흥민", "BTS", "블랙핑크", "아이유", "박보검", "송혜교",
    "김수현", "이민호", "전지현", "수지", "아이브", "뉴진스", "에스파",
    # 정치인
    "윤석열", "이재명", "한동훈",
    # 스포츠
    "김민재", "이강인", "황희찬",
]

# 정보성 키워드와 공식 사이트 매핑
OFFICIAL_SITES = {
    "연말정산": {
        "url": "https://www.hometax.go.kr/",
        "name": "홈택스",
    },
    "청년도약계좌": {
        "url": "https://www.kinfa.or.kr/",
        "name": "서민금융진흥원",
    },
    "청년미래적금": {
        "url": "https://www.kinfa.or.kr/",
        "name": "서민금융진흥원",
    },
    "주택청약": {
        "url": "https://www.applyhome.co.kr/",
        "name": "청약홈",
    },
    "환율": {
        "url": "https://finance.naver.com/marketindex/",
        "name": "네이버 금융",
    },
    "코스피": {
        "url": "https://finance.naver.com/sise/",
        "name": "네이버 증권",
    },
    "코스닥": {
        "url": "https://finance.naver.com/sise/",
        "name": "네이버 증권",
    },
    "비트코인": {
        "url": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC",
        "name": "업비트",
    },
    "이더리움": {
        "url": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-ETH",
        "name": "업비트",
    },
    "날씨": {
        "url": "https://weather.naver.com/",
        "name": "네이버 날씨",
    },
    "자동차보험": {
        "url": "https://www.knia.or.kr/",
        "name": "손해보험협회",
    },
    "실비보험": {
        "url": "https://www.klia.or.kr/",
        "name": "생명보험협회",
    },
    "건강보험": {
        "url": "https://www.nhis.or.kr/",
        "name": "국민건강보험공단",
    },
    "국민연금": {
        "url": "https://www.nps.or.kr/",
        "name": "국민연금공단",
    },
    "고용보험": {
        "url": "https://www.ei.go.kr/",
        "name": "고용보험",
    },
}


class ScreenshotCapture:
    """Puppeteer 기반 스크린샷 캡처"""

    def __init__(self):
        self.script_path = SCREENSHOT_SCRIPT
        self.output_dir = Path(tempfile.gettempdir()) / "autoblog_screenshots"
        self.output_dir.mkdir(exist_ok=True)

    def is_available(self) -> bool:
        """
        스크린샷 기능 사용 가능 여부 확인
        Node.js와 Puppeteer가 설치되어 있어야 함
        """
        try:
            # Node.js 확인
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False

            # 스크립트 파일 존재 확인
            if not self.script_path.exists():
                logger.warning(f"스크린샷 스크립트 없음: {self.script_path}")
                return False

            return True

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_person_keyword(self, keyword: str) -> bool:
        """인물/연예인 키워드인지 확인"""
        for person in PERSON_KEYWORDS:
            if person in keyword:
                return True
        return False

    def get_official_site(self, keyword: str) -> Optional[Dict]:
        """키워드에 맞는 공식 사이트 정보 반환"""
        for key, info in OFFICIAL_SITES.items():
            if key in keyword:
                return info
        return None

    def capture(
        self,
        keyword: str,
        url: str = None,
        is_person: bool = None
    ) -> Optional[Dict]:
        """
        스크린샷 캡처

        Args:
            keyword: 키워드 (URL 없으면 검색용으로 사용)
            url: 캡처할 URL (없으면 키워드로 자동 결정)
            is_person: 인물 키워드 여부 (None이면 자동 판단)

        Returns:
            스크린샷 정보 딕셔너리 또는 None
        """
        if not self.is_available():
            logger.warning("스크린샷 기능을 사용할 수 없습니다. Node.js/Puppeteer를 설치하세요.")
            return None

        # 인물 키워드 여부 자동 판단
        if is_person is None:
            is_person = self.is_person_keyword(keyword)

        # URL 결정
        if not url:
            if is_person:
                # 인물이면 네이버 뉴스 검색
                url = keyword  # Node.js에서 검색 URL로 변환
            else:
                # 공식 사이트 확인
                site_info = self.get_official_site(keyword)
                if site_info:
                    url = site_info["url"]
                else:
                    # 그 외에는 뉴스 검색
                    url = keyword

        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in "가-힣")[:20]
        output_path = self.output_dir / f"screenshot_{safe_keyword}_{timestamp}.png"

        try:
            logger.info(f"스크린샷 캡처 중: {keyword} -> {url}")

            # Node.js 스크립트 실행
            result = subprocess.run(
                [
                    "node",
                    str(self.script_path),
                    url,
                    str(output_path),
                    "true" if is_person else "false",
                    keyword
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(SCRIPT_DIR)
            )

            if result.returncode != 0:
                logger.error(f"스크린샷 캡처 실패: {result.stderr}")
                return None

            # JSON 결과 파싱
            try:
                output_lines = result.stdout.strip().split('\n')
                json_output = output_lines[-1]  # 마지막 줄이 JSON
                response = json.loads(json_output)

                if response.get("success"):
                    logger.info(f"스크린샷 저장 완료: {output_path}")
                    return {
                        "type": "screenshot",
                        "path": str(output_path),
                        "url": response.get("url", url),
                        "keyword": keyword,
                        "alt": f"{keyword} 관련 스크린샷",
                        "source": "네이버 뉴스 검색" if is_person else self.get_official_site(keyword).get("name", "웹사이트") if self.get_official_site(keyword) else "웹사이트"
                    }
                else:
                    logger.error(f"스크린샷 실패: {response.get('error')}")
                    return None

            except json.JSONDecodeError:
                # JSON 파싱 실패해도 파일이 생성되었으면 성공
                if output_path.exists():
                    logger.info(f"스크린샷 저장 완료: {output_path}")
                    return {
                        "type": "screenshot",
                        "path": str(output_path),
                        "url": url,
                        "keyword": keyword,
                        "alt": f"{keyword} 관련 스크린샷",
                        "source": "웹사이트"
                    }
                return None

        except subprocess.TimeoutExpired:
            logger.error("스크린샷 캡처 시간 초과")
            return None
        except Exception as e:
            logger.error(f"스크린샷 캡처 오류: {e}")
            return None

    def capture_news_search(self, keyword: str) -> Optional[Dict]:
        """네이버 뉴스 검색 결과 스크린샷"""
        return self.capture(keyword, is_person=True)

    def capture_official_site(self, keyword: str) -> Optional[Dict]:
        """공식 사이트 스크린샷"""
        site_info = self.get_official_site(keyword)
        if not site_info:
            return None
        return self.capture(keyword, url=site_info["url"], is_person=False)


def capture_screenshot(keyword: str, is_person: bool = None) -> Optional[Dict]:
    """
    스크린샷 캡처 편의 함수

    Args:
        keyword: 키워드
        is_person: 인물 키워드 여부

    Returns:
        스크린샷 정보 또는 None
    """
    capturer = ScreenshotCapture()
    return capturer.capture(keyword, is_person=is_person)


def is_screenshot_available() -> bool:
    """스크린샷 기능 사용 가능 여부"""
    capturer = ScreenshotCapture()
    return capturer.is_available()


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 스크린샷 기능 테스트 ===\n")

    capturer = ScreenshotCapture()

    print(f"스크린샷 기능 사용 가능: {capturer.is_available()}")
    print()

    # 인물 키워드 테스트
    test_keywords = ["혜리", "손흥민", "연말정산", "비트코인"]

    for kw in test_keywords:
        is_person = capturer.is_person_keyword(kw)
        official = capturer.get_official_site(kw)

        print(f"{kw}:")
        print(f"  인물 키워드: {is_person}")
        print(f"  공식 사이트: {official['name'] if official else '없음'}")
        print()

    # 실제 스크린샷 테스트 (Node.js 필요)
    if capturer.is_available():
        print("\n실제 스크린샷 테스트...")
        result = capturer.capture("혜리")
        if result:
            print(f"성공: {result['path']}")
        else:
            print("실패")
