"""
네이버 지식iN 답변 텍스트 생성

블로그 글 기반으로 네이버 지식iN에 올릴 답변 텍스트를 생성합니다.
실제 API 연동 없이 텍스트만 생성합니다.
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 답변 템플릿
ANSWER_TEMPLATE = """안녕하세요, {keyword} 관련해서 답변 드릴게요.

{summary}

{key_points}

더 자세한 내용은 아래 링크에서 확인하실 수 있어요.
👉 {blog_url}

도움이 되셨으면 좋겠어요!"""


def generate_kin_answer(
    keyword: str,
    summary: str,
    key_points: list,
    blog_url: str,
) -> str:
    """
    네이버 지식iN용 답변 텍스트 생성

    Args:
        keyword: 질문 키워드
        summary: 블로그 글 요약 (2~3문장)
        key_points: 핵심 포인트 리스트
        blog_url: 블로그 글 URL

    Returns:
        답변 텍스트
    """
    points_text = "\n".join(f"✅ {point}" for point in key_points[:5])

    answer = ANSWER_TEMPLATE.format(
        keyword=keyword,
        summary=summary,
        key_points=points_text,
        blog_url=blog_url,
    )

    logger.info(f"[지식iN] '{keyword}' 답변 생성 ({len(answer)}자)")
    return answer


def generate_kin_answers_batch(posts: list) -> list:
    """
    여러 글에 대한 답변 일괄 생성

    Args:
        posts: [{"keyword": str, "summary": str, "key_points": list, "blog_url": str}, ...]

    Returns:
        [{"keyword": str, "answer": str}, ...]
    """
    results = []
    for post in posts:
        answer = generate_kin_answer(
            keyword=post["keyword"],
            summary=post["summary"],
            key_points=post.get("key_points", []),
            blog_url=post["blog_url"],
        )
        results.append({"keyword": post["keyword"], "answer": answer})

    logger.info(f"[지식iN] 총 {len(results)}개 답변 생성")
    return results


if __name__ == "__main__":
    test = generate_kin_answer(
        keyword="연말정산 환급",
        summary="연말정산은 매년 1~2월에 진행되며, 소득공제와 세액공제를 통해 세금을 돌려받을 수 있어요.",
        key_points=[
            "신용카드 소득공제: 총급여 25% 초과분에 대해 공제",
            "의료비 세액공제: 총급여 3% 초과분에 대해 15% 공제",
            "교육비 세액공제: 본인 전액, 자녀 1인당 연 300만원 한도",
        ],
        blog_url="https://quickinfo.kr/연말정산-환급-방법/",
    )
    print(test)
