#!/usr/bin/env python3
"""
애드센스 승인 준비: 기존 발행글 리라이트

DB에서 기존 발행글 12개를 선별하여 WP REST API로 가져온 뒤,
Claude API로 애드센스 기준에 맞게 리라이트하고 PUT으로 업데이트합니다.

사용법:
    python scripts/prepare_adsense.py --dry-run       # 변경 없이 미리보기
    python scripts/prepare_adsense.py --no-delay       # 딜레이 없이 실행
    python scripts/prepare_adsense.py                  # 실제 실행 (30초 간격)
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv 없으면 환경변수에서 직접 읽기

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai 패키지 필요: pip install google-generativeai")
    sys.exit(1)

logger = logging.getLogger(__name__)

# =============================================================================
# 설정
# =============================================================================

WP_BASE_URL = os.getenv("WP_BASE_URL", "https://quickinfo.kr/wp-json/wp/v2")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TARGET_COUNT = 12
DELAY_SECONDS = 30

REWRITE_PROMPT = """당신은 7년 경력의 한국 생활정보/금융 전문 에디터입니다.
아래 블로그 글을 애드센스 승인 기준에 맞게 대폭 개선하세요.

## 리라이트 핵심 원칙

### 1. 분량 확장 (최소 3,000자)
- 원문이 짧으면 관련 정보를 추가하여 최소 3,000자 이상으로 확장
- 각 섹션별 최소 300자 이상
- FAQ 섹션 추가 (5개 이상 Q&A)
- 구체적인 수치, 날짜, 조건 등 팩트 보강

### 2. 구조 개선
- 서론(400자): 주제 소개 + 왜 알아야 하는지 + 이 글에서 다룰 내용
- 본문: 소제목으로 명확히 구분, 각 섹션에 표/리스트/강조박스 혼합
- FAQ(500자): 실제 검색되는 질문 5개 이상, 상세 답변
- 마무리(200자): 핵심 요약 + 다음 행동 안내

### 3. 소제목 스타일 다양화 (border-left 세로바 금지!)
아래 5가지 중 하나를 랜덤 선택하여 전체 통일:
- 배경 그라디언트 바
- 좌측 아이콘 + 텍스트
- 밑줄 강조 (border-bottom)
- 번호 원형 배지 + 텍스트
- 카드형 박스

### 4. 강조 박스 다양화 (최소 2개 사용)
- 파란 정보 박스 (ℹ️ 참고)
- 노란 주의 박스 (⚠️ 주의)
- 녹색 팁 박스 (💡 팁)
- 회색 인용 박스

### 5. 어조/문체
- 친근한 해요체 (됩니다→돼요, 합니다→해요)
- 전문적이면서 읽기 쉽게
- 짧은 문장 (40자 이내)

### 6. 절대 금지
- ㅋㅋ, ㅎㅎ, 꿀팁, 솔직히, 삽질, 대박, 가성비, 핵꿀팁, 역대급
- 감탄사 남발, 과장 표현, 클릭베이트
- AI가 작성했다는 암시

### 7. HTML 규칙
- <div style="max-width: 700px; margin: 0 auto; ...">로 감싸기
- 기존 이미지/링크 유지
- 이모지는 소제목에만 최대 2개

## 원문 제목: {title}

## 원문 본문:
{content}

## 리라이트된 본문 (순수 HTML만 출력, 설명 없이):"""


def get_wp_auth():
    """WordPress 인증 정보 반환"""
    if not WP_USER or not WP_APP_PASSWORD:
        raise ValueError(
            "WP_USER, WP_APP_PASSWORD 환경변수를 설정하세요.\n"
            "export WP_USER='admin'\n"
            "export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx'"
        )
    return (WP_USER, WP_APP_PASSWORD)


def fetch_published_posts(count: int = TARGET_COUNT) -> list:
    """
    WP REST API로 발행된 글 가져오기
    가장 오래된 글부터 선택 (초기 품질이 낮을 가능성 높음)
    """
    params = {
        "status": "publish",
        "per_page": count,
        "orderby": "date",
        "order": "asc",
        "_fields": "id,title,content,link,date",
    }
    auth = get_wp_auth()
    resp = requests.get(f"{WP_BASE_URL}/posts", params=params, auth=auth, timeout=30)
    resp.raise_for_status()
    posts = resp.json()
    logger.info(f"가져온 글 수: {len(posts)}")
    return posts


def rewrite_with_gemini(title: str, content: str) -> str:
    """Gemini API로 콘텐츠 리라이트"""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경변수를 설정하세요.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = REWRITE_PROMPT.format(title=title, content=content)

    response = model.generate_content(prompt)
    return response.text


def update_post(post_id: int, new_content: str) -> dict:
    """WP REST API로 글 업데이트"""
    auth = get_wp_auth()
    resp = requests.post(
        f"{WP_BASE_URL}/posts/{post_id}",
        json={"content": new_content},
        auth=auth,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="애드센스 승인 준비 - 기존 글 리라이트")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 미리보기")
    parser.add_argument("--no-delay", action="store_true", help="딜레이 없이 실행")
    parser.add_argument("--count", type=int, default=TARGET_COUNT, help=f"처리할 글 수 (기본: {TARGET_COUNT})")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print(f"🔧 애드센스 준비 스크립트 시작 (dry-run={args.dry_run})")
    print(f"   대상: {args.count}개 글\n")

    # 1. 글 가져오기
    posts = fetch_published_posts(args.count)

    if not posts:
        print("❌ 발행된 글이 없습니다.")
        return

    results = []

    for i, post in enumerate(posts, 1):
        post_id = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]
        link = post.get("link", "")

        print(f"\n[{i}/{len(posts)}] {title}")
        print(f"  ID: {post_id} | URL: {link}")
        print(f"  원본 길이: {len(content)}자")

        if args.dry_run:
            print("  ⏭️  dry-run: 리라이트 스킵")
            results.append({"id": post_id, "title": title, "status": "skipped"})
            continue

        try:
            # 2. Claude로 리라이트
            print("  ✍️  리라이트 중...")
            new_content = rewrite_with_gemini(title, content)
            print(f"  리라이트 길이: {len(new_content)}자")

            # 3. WP에 업데이트
            print("  📤 업데이트 중...")
            update_post(post_id, new_content)
            print("  ✅ 완료")
            results.append({"id": post_id, "title": title, "status": "updated"})

        except Exception as e:
            print(f"  ❌ 실패: {e}")
            results.append({"id": post_id, "title": title, "status": f"error: {e}"})

        # 딜레이
        if not args.no_delay and i < len(posts):
            print(f"  ⏳ {DELAY_SECONDS}초 대기...")
            time.sleep(DELAY_SECONDS)

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 결과 요약")
    print("=" * 60)
    for r in results:
        status_icon = "✅" if r["status"] == "updated" else "⏭️" if r["status"] == "skipped" else "❌"
        print(f"  {status_icon} [{r['id']}] {r['title']} - {r['status']}")

    updated = sum(1 for r in results if r["status"] == "updated")
    print(f"\n총 {updated}/{len(results)}개 업데이트 완료")


if __name__ == "__main__":
    main()
