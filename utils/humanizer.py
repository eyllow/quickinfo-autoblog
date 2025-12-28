"""AI 생성 텍스트를 인간적으로 변환하는 후처리 모듈"""
import random
import re
import logging

logger = logging.getLogger(__name__)


def humanize_content(content: str) -> str:
    """
    AI 생성 텍스트를 인간적으로 변환

    Args:
        content: AI가 생성한 HTML 콘텐츠

    Returns:
        인간화 처리된 콘텐츠
    """
    original_length = len(content)

    # 1단계: 딱딱한 표현 변환
    replacements = [
        # 순서 나열 표현
        ("첫째,", "일단"),
        ("둘째,", "그리고"),
        ("셋째,", "또"),
        ("넷째,", "그리고 또"),
        ("다섯째,", "마지막으로"),
        ("마지막으로,", "아 그리고"),
        ("첫 번째로,", "일단"),
        ("두 번째로,", "그다음에"),
        ("세 번째로,", "또"),

        # 딱딱한 존댓말 → 친근한 해요체
        ("하는 것이 중요합니다", "하는 게 진짜 중요해요"),
        ("에 대해 알아보겠습니다", "에 대해 얘기해볼게요"),
        ("라고 할 수 있습니다", "라고 볼 수 있어요"),
        ("해야 합니다", "해야 해요"),
        ("하시기 바랍니다", "하세요!"),
        ("되어 있습니다", "돼 있어요"),
        ("인 것 같습니다", "인 것 같아요"),
        ("확인해 보시기 바랍니다", "확인해 보세요"),
        ("참고하시기 바랍니다", "참고하세요!"),
        ("살펴보겠습니다", "살펴볼게요"),
        ("말씀드리겠습니다", "말씀드릴게요"),
        ("도움이 되셨으면 합니다", "도움이 됐으면 좋겠어요"),
        ("알려드리겠습니다", "알려드릴게요"),
        ("소개해 드리겠습니다", "소개해 드릴게요"),
        ("설명드리겠습니다", "설명해 드릴게요"),
        ("추천드립니다", "추천해요"),
        ("권장합니다", "권장해요"),
        ("필요합니다", "필요해요"),
        ("있습니다", "있어요"),
        ("됩니다", "돼요"),
        ("입니다", "이에요"),
        ("습니다", "어요"),

        # 결론/마무리 표현
        ("결론적으로 말씀드리자면", "정리하자면"),
        ("결론적으로", "정리하자면"),
        ("요약하자면", "정리해보면"),
        ("다양한 측면에서 살펴보면", "여러 가지로 보면"),
        ("종합적으로 판단하면", "전체적으로 보면"),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    # 2단계: 랜덤 추임새 삽입 (</p> 태그 뒤에)
    interjections = [
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">아 참, ",
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">근데요, ",
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">솔직히 ",
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">여기서 잠깐! ",
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">꿀팁인데요, ",
        "\n<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">이게 중요한데, ",
    ]

    # </p> 태그 위치 찾기
    p_positions = [m.end() for m in re.finditer(r'</p>', content)]

    if len(p_positions) > 8:
        # 2~3개 위치에 추임새 삽입 (처음과 끝 제외)
        insert_count = random.randint(2, 3)
        # 중간 위치에서만 선택 (처음 2개, 마지막 2개 제외)
        available_positions = p_positions[3:-3]

        if len(available_positions) >= insert_count:
            insert_positions = random.sample(available_positions, insert_count)

            # 역순으로 삽입 (위치가 밀리지 않게)
            for pos in sorted(insert_positions, reverse=True):
                interjection = random.choice(interjections)
                content = content[:pos] + interjection + content[pos:]

    # 3단계: 일부 문장에 구어체 변환 (30% 확률)
    casual_additions = [
        ("이에요.</p>", "이에요 ㅎㅎ</p>"),
        ("해요.</p>", "해요!</p>"),
        ("거든요.</p>", "거든요 ㅋㅋ</p>"),
        ("같아요.</p>", "같아요~</p>"),
    ]

    for old, new in casual_additions:
        if random.random() > 0.7:  # 30% 확률
            # 1~2개만 변환
            count = random.randint(1, 2)
            for _ in range(count):
                content = content.replace(old, new, 1)

    # 4단계: 강조 표현 추가
    emphasis_patterns = [
        (r'(진짜 중요)', r'진짜 진짜 중요'),
        (r'(꼭 확인)', r'꼭꼭 확인'),
        (r'(매우 중요)', r'엄청 중요'),
    ]

    for pattern, replacement in emphasis_patterns:
        if random.random() > 0.5:  # 50% 확률
            content = re.sub(pattern, replacement, content, count=1)

    logger.info(f"Humanized content: {original_length} -> {len(content)} chars")
    return content


def add_personal_touches(content: str, keyword: str) -> str:
    """
    개인적인 경험담 스타일 추가

    Args:
        content: HTML 콘텐츠
        keyword: 블로그 키워드

    Returns:
        개인적 터치가 추가된 콘텐츠
    """
    # 이미 개인 경험이 있으면 스킵
    personal_indicators = ["저도", "제가", "솔직히", "사실 저는"]
    first_500 = content[:500]

    if any(indicator in first_500 for indicator in personal_indicators):
        logger.info("Personal touch already exists - skipping")
        return content

    # 키워드 기반 개인 경험담
    personal_phrases = [
        f"<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">저도 {keyword} 처음 알아볼 때 진짜 막막했거든요. 그래서 제가 직접 경험한 걸 바탕으로 정리해봤어요.</p>",
        f"<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">솔직히 {keyword} 관련해서 저도 삽질 좀 했어요 ㅋㅋ 그래서 여러분은 저처럼 시행착오 없이 가시라고 이 글 정리했어요.</p>",
        f"<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">제 주변에도 {keyword} 때문에 고민하는 분들 많더라고요. 그래서 한번 정리해봤어요!</p>",
    ]

    # 첫 번째 </h2> 또는 첫 번째 </h4> 다음에 삽입
    heading_match = re.search(r'(</h[24]>)', content)

    if heading_match:
        insert_pos = heading_match.end()
        phrase = random.choice(personal_phrases)
        content = content[:insert_pos] + "\n" + phrase + "\n" + content[insert_pos:]
        logger.info("Added personal touch after first heading")

    return content


def add_reader_questions(content: str) -> str:
    """
    독자에게 질문하는 표현 추가

    Args:
        content: HTML 콘텐츠

    Returns:
        질문이 추가된 콘텐츠
    """
    questions = [
        "<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">혹시 이거 해보신 분 계세요?</p>",
        "<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">저만 그런가요? ㅋㅋ</p>",
        "<p style=\"font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;\">여러분은 어떠세요?</p>",
    ]

    # 50% 확률로 추가
    if random.random() > 0.5:
        # 중간 위치의 </p> 찾기
        p_positions = [m.end() for m in re.finditer(r'</p>', content)]

        if len(p_positions) > 6:
            # 중간 위치 선택
            mid_positions = p_positions[len(p_positions)//3 : 2*len(p_positions)//3]
            if mid_positions:
                insert_pos = random.choice(mid_positions)
                question = random.choice(questions)
                content = content[:insert_pos] + "\n" + question + content[insert_pos:]
                logger.info("Added reader question")

    return content


def humanize_full(content: str, keyword: str) -> str:
    """
    전체 인간화 처리 (모든 단계 적용)

    Args:
        content: AI가 생성한 HTML 콘텐츠
        keyword: 블로그 키워드

    Returns:
        완전히 인간화된 콘텐츠
    """
    print("  🧑 인간화 처리 시작...")

    # 1. 기본 인간화
    content = humanize_content(content)

    # 2. 개인 경험담 추가
    content = add_personal_touches(content, keyword)

    # 3. 독자 질문 추가
    content = add_reader_questions(content)

    print("  ✓ 인간화 처리 완료")

    return content


if __name__ == "__main__":
    # 테스트
    test_content = """
    <h2>테스트 제목</h2>
    <p>첫째, 이것이 중요합니다. 둘째, 저것도 중요합니다.</p>
    <p>이에 대해 알아보겠습니다. 확인해 보시기 바랍니다.</p>
    <p>결론적으로 말씀드리자면 이것이 핵심입니다.</p>
    """

    result = humanize_full(test_content, "테스트 키워드")
    print(result)
