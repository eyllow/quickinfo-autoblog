"""
AI 탐지 우회 인간화 처리 모듈
AI가 생성한 콘텐츠를 더 자연스럽게 변환합니다.
"""
import re
import random
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 인간화 변환 규칙
# =============================================================================

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

# 삽입할 감탄사/추임새
INTERJECTIONS = [
    "와, ",
    "대박! ",
    "솔직히 ",
    "진짜 ",
    "사실 ",
    "근데요, ",
    "아, 그리고 ",
    "참고로 ",
]

# 독자에게 말 걸기 표현
READER_ENGAGEMENT = [
    "여러분도 그렇지 않으세요?",
    "혹시 이런 경험 있으신가요?",
    "공감되시나요? ㅎㅎ",
    "이거 진짜 꿀팁이에요!",
    "저만 그런 거 아니었네요 ㅋㅋ",
]

# 개인 경험담 표현
PERSONAL_TOUCHES = [
    "제가 직접 해보니까 ",
    "저도 처음엔 몰랐는데 ",
    "솔직히 저도 고민했거든요. ",
    "제 경험상으로는 ",
    "친구한테 들었는데 ",
]


def apply_casual_tone(content: str) -> str:
    """
    딱딱한 표현을 구어체로 변환

    Args:
        content: 원본 콘텐츠

    Returns:
        변환된 콘텐츠
    """
    for formal, casual in FORMAL_TO_CASUAL:
        content = re.sub(formal, casual, content)
    return content


def add_interjections(content: str, probability: float = 0.15) -> str:
    """
    감탄사/추임새 삽입

    Args:
        content: 원본 콘텐츠
        probability: 삽입 확률 (0~1)

    Returns:
        변환된 콘텐츠
    """
    # <p> 태그 시작 부분에 랜덤하게 감탄사 삽입
    def insert_interjection(match):
        if random.random() < probability:
            interjection = random.choice(INTERJECTIONS)
            return match.group(0) + interjection
        return match.group(0)

    content = re.sub(r'<p[^>]*>', insert_interjection, content)
    return content


def add_reader_question(content: str) -> str:
    """
    독자에게 말 걸기 표현 추가 (1~2개)

    Args:
        content: 원본 콘텐츠

    Returns:
        변환된 콘텐츠
    """
    # </p> 태그 앞에 랜덤하게 독자 참여 문구 추가
    paragraphs = re.findall(r'<p[^>]*>.*?</p>', content, re.DOTALL)

    if len(paragraphs) < 3:
        return content

    # 중간 부분에서 1~2개 문단 선택
    mid_start = len(paragraphs) // 3
    mid_end = len(paragraphs) * 2 // 3
    candidates = paragraphs[mid_start:mid_end]

    if candidates:
        selected = random.choice(candidates)
        engagement = random.choice(READER_ENGAGEMENT)
        new_para = selected.replace("</p>", f" {engagement}</p>")
        content = content.replace(selected, new_para, 1)
        logger.info("Added reader question")

    return content


def add_personal_touch(content: str) -> str:
    """
    개인 경험담 표현 추가

    Args:
        content: 원본 콘텐츠

    Returns:
        변환된 콘텐츠
    """
    # 첫 번째 h3 태그 다음 문단에 개인 경험담 추가
    h3_match = re.search(r'</h3>\s*<p[^>]*>', content)

    if h3_match:
        personal = random.choice(PERSONAL_TOUCHES)
        insert_pos = h3_match.end()
        content = content[:insert_pos] + personal + content[insert_pos:]
        logger.info("Added personal touch after first heading")

    return content


def vary_sentence_length(content: str) -> str:
    """
    문장 길이 불규칙화
    너무 긴 문장은 분리, 짧은 문장은 유지

    Args:
        content: 원본 콘텐츠

    Returns:
        변환된 콘텐츠
    """
    # "그리고", "또한", "하지만" 등으로 연결된 긴 문장 분리
    content = re.sub(r'([.?!])\s*(그리고|또한|하지만|그래서|따라서)', r'\1</p>\n<p>\2', content)

    return content


def humanize_content(content: str, keyword: str = "") -> str:
    """
    콘텐츠 전체 인간화 처리

    Args:
        content: 원본 콘텐츠
        keyword: 키워드 (사용하지 않음, 호환성 유지)

    Returns:
        인간화 처리된 콘텐츠
    """
    original_length = len(content)

    # 1. 구어체 변환
    content = apply_casual_tone(content)

    # 2. 감탄사 삽입 (15% 확률)
    content = add_interjections(content, probability=0.15)

    # 3. 독자 참여 문구 추가
    content = add_reader_question(content)

    # 4. 개인 경험담 추가
    content = add_personal_touch(content)

    # 5. 문장 길이 불규칙화
    content = vary_sentence_length(content)

    logger.info(f"Humanized content: {original_length} -> {len(content)} chars")

    return content


if __name__ == "__main__":
    # 테스트
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
