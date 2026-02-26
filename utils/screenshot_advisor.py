"""AI 기반 스크린샷 추천 시스템"""
import anthropic
import json
import re
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings

logger = logging.getLogger(__name__)


def get_screenshot_recommendation(keyword: str, category: str) -> dict:
    """
    스크린샷 필요 여부 판단 — 비활성화됨
    (정부사이트 대부분 봇 차단으로 깨진 이미지 발생하여 항상 불필요 반환)
    """
    logger.info(f"Screenshot disabled for '{keyword}' - always returning False")
    print(f"  🚫 스크린샷 비활성화 (봇 차단 이슈)")
    return {"need_screenshot": False, "reason": "스크린샷 기능 비활성화", "url": None, "site_name": None, "is_person": False}

    # === 아래는 기존 코드 (비활성화) ===
    client = anthropic.Anthropic(api_key=settings.claude_api_key)

    prompt = f"""당신은 블로그 콘텐츠 전문가입니다.

키워드: {keyword}
카테고리: {category}

이 키워드에 대한 블로그 글에 "실시간 웹사이트 스크린샷"이 필요한지 판단해주세요.

[스크린샷이 유용한 경우]
- 실시간 데이터가 중요한 주제 (환율, 주식, 암호화폐 시세)
- 공식 사이트 안내가 필요한 주제 (정부 서비스, 신청 방법)
- 특정 웹사이트 사용법 설명

[인물/연예인 키워드의 경우 - 중요!]
- 연예인, 배우, 가수, 정치인, 스포츠 선수 등 인물 키워드인 경우:
  - ✅ 네이버 인물 검색 페이지 추천: https://search.naver.com/search.naver?where=nexearch&query=인물이름
  - ✅ 네이버 뉴스 검색 페이지 추천: https://search.naver.com/search.naver?where=news&query=인물이름
  - ❌ 나무위키 절대 금지 (Cloudflare 차단으로 캡처 불가)
  - ❌ 인스타그램, 페이스북 등 SNS 금지 (저작권/봇차단)
  - ❌ 연예인 얼굴 사진이 메인인 페이지 피하기 (초상권)

[스크린샷이 불필요한 경우]
- 일반적인 정보/팁 (다이어트, 건강, 여행)
- 개념 설명 (투자 방법론, 자기계발)
- 리뷰/비교 콘텐츠

[절대 추천 금지 도메인]
- namu.wiki (나무위키) - Cloudflare 인증으로 캡처 불가
- namuwiki.kr
- instagram.com, facebook.com, twitter.com, x.com

[URL 추천 시 규칙]
- 반드시 실제 존재하는 공식 사이트 URL
- 로그인 없이 접근 가능한 페이지
- 한국 사이트 우선
- 추천 URL 예시:
  * 환율: https://finance.naver.com/marketindex/
  * 비트코인: https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC
  * 주식/코스피: https://finance.naver.com/sise/
  * 연말정산/세금: https://www.hometax.go.kr/
  * 날씨: https://weather.naver.com/
  * 부동산: https://land.naver.com/
  * 인물/연예인: https://search.naver.com/search.naver?where=nexearch&query=인물이름

JSON 형식으로만 응답하세요:
{{
    "need_screenshot": true 또는 false,
    "reason": "판단 이유 (한 문장)",
    "url": "스크린샷할 URL (필요한 경우만, 아니면 null)",
    "site_name": "사이트 이름 (예: 나무위키, 홈택스, 업비트)",
    "is_person": true 또는 false
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # JSON 파싱
        if result_text.startswith('{'):
            result = json.loads(result_text)
        else:
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                logger.warning("Failed to parse AI screenshot recommendation")
                return {"need_screenshot": False, "reason": "파싱 실패", "is_person": False}

        # 인물 키워드 로깅
        if result.get('is_person'):
            print(f"  👤 인물 키워드 감지: {keyword}")

        logger.info(f"Screenshot AI decision: {result.get('need_screenshot')} - {result.get('reason')}")
        print(f"  🤖 스크린샷 AI 판단: {'필요' if result.get('need_screenshot') else '불필요'}")
        print(f"     └─ 이유: {result.get('reason')}")

        if result.get('need_screenshot') and result.get('url'):
            print(f"     └─ 추천 URL: {result.get('url')} ({result.get('site_name')})")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {"need_screenshot": False, "reason": f"JSON 파싱 오류: {e}", "is_person": False}
    except Exception as e:
        logger.error(f"Screenshot recommendation error: {e}")
        print(f"  ⚠️ 스크린샷 추천 에러: {e}")
        return {"need_screenshot": False, "reason": str(e), "is_person": False}


def validate_screenshot_url(url: str) -> bool:
    """
    URL 유효성 검증

    Args:
        url: 검증할 URL

    Returns:
        유효하면 True
    """
    if not url or not url.startswith("http"):
        return False

    # 차단된 도메인 (로그인 필요, 봇 차단 등)
    blocked_domains = [
        "instagram.com",
        "facebook.com",
        "twitter.com",
        "x.com",
        "tiktok.com",
        "youtube.com",
        "namu.wiki",        # Cloudflare 인증으로 캡처 불가
        "namuwiki.kr",
        "namu.moe",
        "login",
        "signin",
        "auth",
        "mypage",
        "member",
    ]

    url_lower = url.lower()
    for blocked in blocked_domains:
        if blocked in url_lower:
            logger.warning(f"Blocked domain detected: {blocked}")
            print(f"  ⚠️ 차단된 도메인: {blocked}")
            return False

    return True


# 기본 URL 매핑 (AI 추천 실패 시 폴백)
DEFAULT_SCREENSHOT_URLS = {
    "환율": {
        "url": "https://finance.naver.com/marketindex/",
        "site_name": "네이버 금융",
        "selector": "#exchangeList"
    },
    "비트코인": {
        "url": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC",
        "site_name": "업비트",
        "selector": ".chart"
    },
    "이더리움": {
        "url": "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-ETH",
        "site_name": "업비트",
        "selector": ".chart"
    },
    "주식": {
        "url": "https://finance.naver.com/sise/",
        "site_name": "네이버 금융",
        "selector": ".kospi_area"
    },
    "코스피": {
        "url": "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",
        "site_name": "네이버 금융",
        "selector": "#chart_area"
    },
    "코스닥": {
        "url": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",
        "site_name": "네이버 금융",
        "selector": "#chart_area"
    },
    "날씨": {
        "url": "https://weather.naver.com/",
        "site_name": "네이버 날씨",
        "selector": ".weather_area"
    },
    "부동산": {
        "url": "https://land.naver.com/",
        "site_name": "네이버 부동산",
        "selector": ".section_price"
    },
    "연말정산": {
        "url": "https://www.hometax.go.kr/",
        "site_name": "홈택스",
        "selector": None
    },
    "금리": {
        "url": "https://finance.naver.com/marketindex/interestDailyQuote.naver",
        "site_name": "네이버 금융",
        "selector": None
    },
    "금값": {
        "url": "https://finance.naver.com/marketindex/goldDetail.naver",
        "site_name": "네이버 금융",
        "selector": None
    },
}


def get_fallback_url(keyword: str) -> dict:
    """
    키워드 기반 폴백 URL 반환

    Args:
        keyword: 검색 키워드

    Returns:
        URL 정보 딕셔너리 또는 빈 딕셔너리
    """
    for key, info in DEFAULT_SCREENSHOT_URLS.items():
        if key in keyword:
            logger.info(f"Fallback URL found for '{keyword}': {info['url']}")
            return {
                "need_screenshot": True,
                "url": info["url"],
                "site_name": info["site_name"],
                "selector": info.get("selector"),
                "reason": f"키워드 '{key}' 매칭 (폴백)"
            }
    return {}


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== AI 스크린샷 추천 테스트 ===\n")

    test_cases = [
        ("비트코인 시세", "재테크"),
        ("환율 전망", "트렌드"),
        ("다이어트 식단", "건강"),
        ("봄 여행지 추천", "생활정보"),
        ("연말정산 방법", "재테크"),
    ]

    for keyword, category in test_cases:
        print(f"\n테스트: {keyword} ({category})")
        print("-" * 40)
        result = get_screenshot_recommendation(keyword, category)
        print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
