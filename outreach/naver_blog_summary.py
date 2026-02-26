"""
네이버 블로그 요약 포스트 텍스트 생성

블로그 글을 네이버 블로그용 짧은 요약 포스트로 변환합니다.
실제 API 연동 없이 텍스트만 생성합니다.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BLOG_SUMMARY_TEMPLATE = """{title}

{intro}

📌 핵심 정리

{key_points}

{official_link_section}

💡 더 자세한 내용이 궁금하시다면?
👉 {blog_url}

#생활정보 #{hashtag1} #{hashtag2}"""


def generate_blog_summary(
    title: str,
    intro: str,
    key_points: list,
    blog_url: str,
    hashtags: list = None,
    official_url: str = None,
    official_name: str = None,
) -> str:
    """
    네이버 블로그용 요약 포스트 생성

    Args:
        title: 글 제목
        intro: 도입부 (1~2문장)
        key_points: 핵심 포인트 리스트
        blog_url: 원본 블로그 URL
        hashtags: 해시태그 리스트 (최소 2개)
        official_url: 공식 사이트 URL
        official_name: 공식 사이트 이름

    Returns:
        네이버 블로그 요약 포스트 텍스트
    """
    points_text = "\n".join(f"✔️ {point}" for point in key_points[:7])

    if official_url and official_name:
        official_link_section = f"🔗 공식 사이트: {official_name}\n{official_url}"
    else:
        official_link_section = ""

    tags = hashtags or ["생활꿀정보", "정보공유"]
    hashtag1 = tags[0].replace("#", "")
    hashtag2 = tags[1].replace("#", "") if len(tags) > 1 else "정보공유"

    post = BLOG_SUMMARY_TEMPLATE.format(
        title=title,
        intro=intro,
        key_points=points_text,
        official_link_section=official_link_section,
        blog_url=blog_url,
        hashtag1=hashtag1,
        hashtag2=hashtag2,
    )

    logger.info(f"[블로그요약] '{title}' 생성 ({len(post)}자)")
    return post


if __name__ == "__main__":
    test = generate_blog_summary(
        title="2025 연말정산 환급 꼭 알아야 할 3가지",
        intro="연말정산 시즌이 돌아왔어요. 올해 달라진 점과 환급 받는 방법을 정리했어요.",
        key_points=[
            "신용카드 공제 한도 확대 (최대 300만원)",
            "월세 세액공제율 상향 (15→17%)",
            "자녀 세액공제 금액 인상",
        ],
        blog_url="https://quickinfo.kr/연말정산-환급-방법/",
        hashtags=["연말정산", "세금환급"],
        official_url="https://www.hometax.go.kr",
        official_name="국세청 홈택스",
    )
    print(test)
