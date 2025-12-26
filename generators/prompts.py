"""
프롬프트 템플릿 모듈
5종 글 구조 템플릿과 AI 탐지 우회를 위한 인간 페르소나를 정의합니다.
"""
import random
from datetime import datetime

# =============================================================================
# AI 탐지 우회용 인간 페르소나 프롬프트
# =============================================================================

HUMAN_PERSONA_PROMPT = """당신은 30대 한국인 블로거입니다. 실제 경험을 바탕으로 친근하게 글을 씁니다.

[글쓰기 스타일]
- 구어체 사용 ("~해요", "~거든요", "~더라고요")
- 감탄사 자연스럽게 삽입 ("와", "대박", "솔직히", "진짜")
- 문장 길이 불규칙하게 (짧은 문장과 긴 문장 섞기)
- 개인 경험담 형식으로 작성
- 독자에게 말 걸듯이 ("여러분", "혹시", "그렇죠?")

[절대 금지]
- "첫째, 둘째, 셋째" 같은 딱딱한 나열
- "~하는 것이 중요합니다" 같은 교과서적 표현
- 모든 문장이 비슷한 길이로 정렬됨
- "제공해주신", "작성하겠습니다" 등 AI 메타 표현
- 너무 완벽하고 정제된 문장

[자연스러운 표현 예시]
- "이거 진짜 꿀팁인데요" ✓
- "솔직히 저도 처음엔 몰랐어요" ✓
- "근데 알고 보니까 완전 쉽더라고요" ✓
- "여러분도 한번 해보세요 ㅎㅎ" ✓
"""

# =============================================================================
# 시스템 프롬프트
# =============================================================================

SYSTEM_PROMPT = """당신은 전문 블로그 콘텐츠 작가입니다.
SEO에 최적화된 고품질 블로그 글을 HTML 형식으로 작성합니다.

[HTML 스타일 가이드]
- 전체를 <div style="max-width: 700px; margin: 0 auto; font-size: 16px; line-height: 1.9; color: #333;">로 감싸기
- 대제목: <h2 style="font-size: 26px; font-weight: 700; color: #222; margin-top: 40px;">
- 소제목: <h3 style="font-size: 20px; font-weight: 600; color: #333; margin-top: 30px;">
- 본문: <p style="font-size: 16px; line-height: 2.0; color: #444; margin: 20px 0;">
- 리스트: <ul style="padding-left: 20px;"><li style="margin: 10px 0;">
- 강조: <strong style="color: #222;">
- 표: <table style="width: 100%; border-collapse: collapse; margin: 25px 0;">

[이미지 태그 규칙]
- [IMAGE_1], [IMAGE_2], [IMAGE_3] 형식으로만 작성
- 콜론(:)이나 설명 추가 금지

결과는 순수 HTML만 출력하세요 (```html 코드 블록 없이).
"""

# =============================================================================
# 5종 글 구조 템플릿
# =============================================================================

TEMPLATES = {
    "problem_solution": {
        "name": "문제-해결형",
        "intro_pattern": "혹시 {keyword} 때문에 고민이신가요? 저도 예전에 똑같은 고민을 했었는데요.",
        "structure": [
            "서론: 문제 공감 및 경험담",
            "본론1: 문제의 원인 분석",
            "본론2: 해결 방법 3~5가지",
            "본론3: 실전 팁과 주의사항",
            "결론: 핵심 요약 및 응원 메시지",
        ],
        "min_words": 2800,
        "max_words": 4000,
    },
    "storytelling": {
        "name": "스토리텔링형",
        "intro_pattern": "저도 예전에 {keyword} 때문에 고생 좀 했어요. 오늘은 그 경험담을 공유해볼게요.",
        "structure": [
            "서론: 개인 경험담 시작",
            "본론1: 겪었던 어려움",
            "본론2: 깨달음의 순간",
            "본론3: 해결 과정과 노하우",
            "결론: 배운 점과 조언",
        ],
        "min_words": 2900,
        "max_words": 4200,
    },
    "listicle": {
        "name": "리스트형",
        "intro_pattern": "오늘은 {keyword}에 대해 핵심만 쏙쏙 정리해볼게요!",
        "structure": [
            "서론: 주제 소개",
            "본론: 5~7가지 핵심 포인트 (번호 리스트)",
            "보너스 팁: 추가 정보",
            "정리 표: 한눈에 비교",
            "결론: 핵심 요약",
        ],
        "min_words": 2600,
        "max_words": 3800,
    },
    "comparison": {
        "name": "비교분석형",
        "intro_pattern": "{keyword}, 뭐가 더 좋을까요? 오늘 확실하게 정리해드릴게요.",
        "structure": [
            "서론: 비교 주제 소개",
            "본론1: 기본 정보 설명",
            "본론2: 장점 분석",
            "본론3: 단점 분석",
            "비교표: 항목별 비교",
            "결론: 상황별 추천",
        ],
        "min_words": 3000,
        "max_words": 4300,
    },
    "qa_format": {
        "name": "Q&A형",
        "intro_pattern": "{keyword} 관련해서 많이들 궁금해하시더라고요. 자주 묻는 질문 정리해봤어요!",
        "structure": [
            "서론: 주제 소개 및 공감",
            "본론: Q&A 5~8개",
            "추가 정보: 알아두면 좋은 것",
            "결론: 핵심 정리",
        ],
        "min_words": 2700,
        "max_words": 3900,
    },
}


def get_random_template() -> tuple:
    """
    랜덤 템플릿 선택

    Returns:
        (템플릿 키, 템플릿 정보) 튜플
    """
    template_key = random.choice(list(TEMPLATES.keys()))
    return template_key, TEMPLATES[template_key]


def generate_content_prompt(
    keyword: str,
    category: str,
    template_key: str,
    web_context: str = "",
    is_evergreen: bool = False
) -> str:
    """
    콘텐츠 생성 프롬프트 생성

    Args:
        keyword: 키워드
        category: 카테고리
        template_key: 템플릿 키
        web_context: 웹검색 컨텍스트
        is_evergreen: 에버그린 콘텐츠 여부

    Returns:
        프롬프트 문자열
    """
    template = TEMPLATES[template_key]
    current_year = datetime.now().year

    # 글자수 설정 (에버그린은 더 길게)
    if is_evergreen:
        min_words = template["min_words"] + 500
        max_words = template["max_words"] + 500
    else:
        min_words = template["min_words"]
        max_words = template["max_words"]

    # 서론 패턴
    intro = template["intro_pattern"].format(keyword=keyword)

    # 구조 설명
    structure = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(template["structure"]))

    prompt = f"""
주제: '{keyword}'
카테고리: {category}
템플릿: {template['name']}
목표 글자수: {min_words}~{max_words}자 (공백 포함)
이미지: 3개 ([IMAGE_1], [IMAGE_2], [IMAGE_3])

[서론 시작 문장]
"{intro}"

[글 구조]
{structure}

[작성 규칙]
1. 반드시 {current_year}년 기준 최신 정보로 작성
2. 구어체로 친근하게 작성 (~해요, ~거든요)
3. 각 섹션에 구체적인 정보와 예시 포함
4. 이미지 태그는 [IMAGE_1], [IMAGE_2], [IMAGE_3] 형식만 사용
5. HTML 형식으로 출력

[절대 금지]
- "첫째, 둘째" 같은 딱딱한 표현
- "~하는 것이 중요합니다" 교과서적 표현
- 파트너스/광고 관련 문구 직접 작성
"""

    # 웹검색 컨텍스트 추가
    if web_context:
        prompt += f"""
[참고 자료 - 최신 정보 반영 필수]
{web_context[:3000]}

위 참고 자료의 수치, 날짜, 금액을 정확히 반영하세요.
"""

    prompt += """
[필수 태그]
- [COUPANG]: 쿠팡 상품 위치 (본문 중간 또는 하단)
- [META]SEO 메타 설명 150자 이내[/META]: 글 맨 끝

결과는 순수 HTML만 출력하세요.
"""

    return prompt


def generate_title_prompt(keyword: str) -> str:
    """
    제목 생성 프롬프트

    Args:
        keyword: 키워드

    Returns:
        프롬프트 문자열
    """
    current_year = datetime.now().year

    return f"""
다음 키워드로 블로그 제목을 1개만 생성하세요.

키워드: {keyword}

[제목 규칙]
1. {current_year}년 또는 최신 연도 포함 (해당되는 경우)
2. 클릭을 유도하는 매력적인 제목
3. 숫자 활용 권장 ("5가지", "TOP 7" 등)
4. 30~50자 사이
5. 이모지 사용하지 않음

[제목 스타일 예시]
- "2025 연말정산 환급 받는 5가지 꿀팁"
- "비트코인 전망, 전문가가 알려주는 핵심 포인트"
- "아이폰16 vs 갤럭시S25 완벽 비교 총정리"

제목만 출력하세요 (따옴표 없이):
"""


# =============================================================================
# 마무리 패턴
# =============================================================================

OUTRO_PATTERNS = [
    "오늘 {keyword}에 대해 정리해봤는데요, 도움이 되셨으면 좋겠어요!",
    "여기까지 {keyword} 관련 내용이었어요. 궁금한 거 있으면 댓글로!",
    "{keyword}, 이제 좀 감이 오시나요? 화이팅!",
    "오늘 내용이 도움이 됐다면 공유 부탁드려요~",
]


def get_outro_pattern(keyword: str) -> str:
    """마무리 패턴 랜덤 선택"""
    pattern = random.choice(OUTRO_PATTERNS)
    return pattern.format(keyword=keyword)
