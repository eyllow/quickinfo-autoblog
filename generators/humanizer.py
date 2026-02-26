"""
AI 탐지 우회 인간화 처리 모듈
AI가 생성한 콘텐츠를 더 자연스럽게 변환합니다.
"""
import re
import logging

logger = logging.getLogger(__name__)

# 딱딱한 표현 → 구어체 변환
FORMAL_TO_CASUAL = [
    (r"것이 중요합니다", "게 진짜 중요해요"),
    (r"것이 좋습니다", "게 좋아요"),
    (r"할 수 있습니다", "할 수 있어요"),
    (r"됩니다", "돼요"),
    (r"합니다", "해요"),
    (r"입니다", "이에요"),
    (r"습니다", "어요"),
    (r"있습니다", "있어요"),
    (r"없습니다", "없어요"),
    (r"하였습니다", "했어요"),
    (r"되었습니다", "됐어요"),
    (r"첫째,", "일단,"),
    (r"둘째,", "그리고,"),
    (r"셋째,", "또,"),
    (r"넷째,", "그리고 또,"),
    (r"다섯째,", "마지막으로,"),
    (r"따라서", "그래서"),
    (r"그러나", "근데"),
    (r"하지만", "근데"),
    (r"그러므로", "그래서"),
    (r"매우 중요한", "진짜 중요한"),
    (r"반드시", "꼭"),
    (r"특히", "특히나"),
]


def apply_casual_tone(content: str) -> str:
    """
    딱딱한 표현을 구어체로 변환
    """
    for formal, casual in FORMAL_TO_CASUAL:
        content = re.sub(formal, casual, content)
    return content


def vary_sentence_length(content: str) -> str:
    """
    문장 길이 불규칙화
    너무 긴 문장은 분리, 짧은 문장은 유지
    """
    content = re.sub(r'([.?!])\s*(그리고|또한|하지만|그래서|따라서)', r'\1</p>\n<p>\2', content)
    return content


def humanize_content(content: str, keyword: str = "") -> str:
    """
    콘텐츠 전체 인간화 처리

    Args:
        content: 원본 콘텐츠
        keyword: 키워드 (호환성 유지)

    Returns:
        인간화 처리된 콘텐츠
    """
    original_length = len(content)

    content = apply_casual_tone(content)
    content = vary_sentence_length(content)

    logger.info(f"Humanized content: {original_length} -> {len(content)} chars")
    return content


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_content = """
<div>
<h2>연말정산 환급 받는 방법</h2>
<p>연말정산은 매우 중요합니다. 첫째, 소득공제 항목을 확인해야 합니다.</p>
<h3>소득공제 항목</h3>
<p>둘째, 세액공제 항목도 중요합니다. 따라서 미리 준비하는 것이 좋습니다.</p>
<p>셋째, 증빙서류를 잘 챙겨야 합니다. 그러므로 영수증을 모아두세요.</p>
</div>
"""

    print("=== 인간화 처리 테스트 ===\n")
    print("원본:")
    print(test_content)
    print("\n변환 후:")
    result = humanize_content(test_content)
    print(result)
