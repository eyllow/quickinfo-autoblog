"""
Threads(스레드) 요약 포스트 텍스트 생성

블로그 글을 Threads용 짧은 포스트로 변환합니다.
실제 API 연동 없이 텍스트만 생성합니다.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

MAX_LENGTH = 500  # Threads 글자 수 제한


def generate_threads_post(
    title: str,
    key_point: str,
    blog_url: str,
    emoji: str = "📢",
) -> str:
    """
    Threads용 짧은 포스트 생성

    Args:
        title: 글 제목
        key_point: 핵심 내용 1가지 (1~2문장)
        blog_url: 원본 블로그 URL
        emoji: 시작 이모지

    Returns:
        Threads 포스트 텍스트 (500자 이내)
    """
    post = f"{emoji} {title}\n\n{key_point}\n\n자세한 내용 👉 {blog_url}"

    if len(post) > MAX_LENGTH:
        # 초과 시 key_point 잘라내기
        available = MAX_LENGTH - len(f"{emoji} {title}\n\n\n\n자세한 내용 👉 {blog_url}") - 3
        key_point = key_point[:available] + "..."
        post = f"{emoji} {title}\n\n{key_point}\n\n자세한 내용 👉 {blog_url}"

    logger.info(f"[Threads] '{title}' 생성 ({len(post)}자)")
    return post


def generate_threads_series(
    title: str,
    points: List[str],
    blog_url: str,
) -> List[str]:
    """
    여러 포인트를 Threads 시리즈로 생성

    Args:
        title: 글 제목
        points: 핵심 포인트 리스트
        blog_url: 원본 블로그 URL

    Returns:
        Threads 포스트 리스트
    """
    emojis = ["📢", "💡", "✅", "🔍", "📌"]
    posts = []

    for i, point in enumerate(points[:5]):
        emoji = emojis[i % len(emojis)]
        if i == 0:
            post = generate_threads_post(title, point, blog_url, emoji)
        else:
            # 후속 글은 제목 없이
            post = f"{emoji} {point}\n\n👉 {blog_url}"
        posts.append(post)

    logger.info(f"[Threads] '{title}' 시리즈 {len(posts)}개 생성")
    return posts


if __name__ == "__main__":
    posts = generate_threads_series(
        title="2025 연말정산, 이것만 알면 끝!",
        points=[
            "올해부터 신용카드 공제 한도가 300만원으로 늘어났어요. 아직 안 챙기셨다면 지금 확인해보세요.",
            "월세 세액공제율이 15%에서 17%로 올랐어요. 무주택 세입자라면 꼭 신청하세요.",
            "자녀 세액공제도 인상됐어요. 첫째 15만원, 둘째 20만원, 셋째 이상 30만원이에요.",
        ],
        blog_url="https://quickinfo.kr/연말정산-환급-방법/",
    )
    for i, post in enumerate(posts, 1):
        print(f"\n--- 포스트 {i} ---")
        print(post)
