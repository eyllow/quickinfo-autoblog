"""템플릿 다양화 설정 - 저품질 방지 시스템"""
import random

# =============================================================================
# 글 구조 템플릿 5종
# =============================================================================

STRUCTURE_TEMPLATES = {
    "problem_solution": {
        "name": "문제-해결형",
        "description": "문제 제기 → 원인 분석 → 해결책 제시",
        "sections": [
            {"type": "intro", "style": "problem", "min_words": 200, "max_words": 350},
            {"type": "heading", "title": "왜 이런 문제가 생길까요?"},
            {"type": "content", "min_words": 400, "max_words": 600},
            {"type": "heading", "title": "해결 방법 {count}가지"},
            {"type": "list_content", "items": [4, 6], "min_words_per_item": 150},
            {"type": "heading", "title": "실전 꿀팁"},
            {"type": "content", "min_words": 350, "max_words": 500},
            {"type": "heading", "title": "마무리"},
            {"type": "outro", "min_words": 150, "max_words": 300},
        ],
        "image_count": [4, 5],
        "total_words": [2800, 4000],
    },

    "storytelling": {
        "name": "스토리텔링형",
        "description": "경험담 → 깨달음 → 정보 공유",
        "sections": [
            {"type": "intro", "style": "story", "min_words": 250, "max_words": 400},
            {"type": "heading", "title": "저도 처음엔 몰랐어요"},
            {"type": "content", "min_words": 350, "max_words": 550},
            {"type": "heading", "title": "알고 보니 이랬더라고요"},
            {"type": "content", "min_words": 500, "max_words": 750},
            {"type": "heading", "title": "이렇게 하면 됩니다"},
            {"type": "list_content", "items": [5, 7], "min_words_per_item": 120},
            {"type": "heading", "title": "여러분께 드리는 조언"},
            {"type": "outro", "min_words": 200, "max_words": 350},
        ],
        "image_count": [4, 5],
        "total_words": [2900, 4200],
    },

    "listicle": {
        "name": "리스트형",
        "description": "핵심 포인트 나열 중심",
        "sections": [
            {"type": "intro", "style": "hook", "min_words": 150, "max_words": 300},
            {"type": "heading", "title": "{keyword} 핵심 포인트"},
            {"type": "numbered_list", "items": [5, 8], "min_words_per_item": 180},
            {"type": "heading", "title": "보너스 팁"},
            {"type": "content", "min_words": 300, "max_words": 500},
            {"type": "heading", "title": "한눈에 정리"},
            {"type": "table", "rows": [4, 6]},
            {"type": "outro", "min_words": 150, "max_words": 280},
        ],
        "image_count": [4, 5],
        "total_words": [2600, 3800],
    },

    "comparison": {
        "name": "비교분석형",
        "description": "A vs B 또는 장단점 비교",
        "sections": [
            {"type": "intro", "style": "question", "min_words": 200, "max_words": 350},
            {"type": "heading", "title": "먼저 알아야 할 기본 정보"},
            {"type": "content", "min_words": 350, "max_words": 550},
            {"type": "heading", "title": "장점"},
            {"type": "list_content", "items": [4, 6], "min_words_per_item": 120},
            {"type": "heading", "title": "단점"},
            {"type": "list_content", "items": [3, 5], "min_words_per_item": 120},
            {"type": "heading", "title": "비교 정리"},
            {"type": "table", "rows": [5, 7]},
            {"type": "heading", "title": "결론"},
            {"type": "outro", "min_words": 200, "max_words": 350},
        ],
        "image_count": [4, 5],
        "total_words": [3000, 4300],
    },

    "qa_format": {
        "name": "Q&A형",
        "description": "질문-답변 형식",
        "sections": [
            {"type": "intro", "style": "empathy", "min_words": 200, "max_words": 350},
            {"type": "heading", "title": "가장 많이 묻는 질문들"},
            {"type": "qa_list", "items": [6, 8], "min_words_per_item": 150},
            {"type": "heading", "title": "추가로 알아두면 좋은 것"},
            {"type": "content", "min_words": 350, "max_words": 550},
            {"type": "heading", "title": "정리하자면"},
            {"type": "outro", "min_words": 180, "max_words": 300},
        ],
        "image_count": [4, 5],
        "total_words": [2700, 3900],
    },
}

# =============================================================================
# 서론 패턴 (스타일별)
# =============================================================================

INTRO_PATTERNS = {
    "problem": [
        "요즘 {keyword} 때문에 고민인 분들 정말 많죠? 저도 얼마 전까지 똑같았어요.",
        "{keyword}... 이거 진짜 머리 아프잖아요. 뭐부터 해야 할지 모르겠고.",
        "혹시 {keyword} 때문에 밤잠 설치신 적 있으세요? 저만 그런 거 아니었네요.",
        "{keyword} 검색하다가 여기까지 오셨죠? 저도 그 심정 백번 이해해요.",
        "솔직히 {keyword} 이거 왜 이렇게 복잡한 건지... 저도 처음엔 포기할 뻔했어요.",
    ],
    "story": [
        "솔직히 말할게요. 저 {keyword} 때문에 한 달 동안 검색만 했거든요...",
        "제가 {keyword} 처음 접했을 때 얘기 좀 할게요. 진짜 막막했어요.",
        "여러분 저 고백할 게 있어요. {keyword} 관련해서 저도 완전 초보였거든요.",
        "오늘은 제가 {keyword} 경험담을 솔직하게 풀어볼게요. 실패담 포함해서요 ㅋㅋ",
        "{keyword} 얘기하면 저 좀 할 말이 많아요. 직접 겪어봤거든요.",
    ],
    "hook": [
        "잠깐! {keyword} 아직도 모르시면 진짜 손해예요.",
        "오늘 {keyword}에 대해 제가 아는 거 다 풀어볼게요. 꿀정보만 담았어요!",
        "{keyword} 검색하다 여기 오셨죠? 잘 오셨어요. 핵심만 정리해드릴게요.",
        "이 글 보시는 분들 럭키예요. {keyword} 꿀팁 다 모았거든요!",
        "{keyword} 총정리! 이것만 보면 끝이에요. 진짜로요.",
    ],
    "question": [
        "{keyword}, 해야 할까요 말아야 할까요? 이거 진짜 고민되는 부분이죠.",
        "{keyword} vs 다른 방법, 뭐가 더 좋을까요? 오늘 확실히 정리해드릴게요.",
        "\"그래서 {keyword} 어떻게 하는 건데?\" 이 질문 정말 많이 받아요.",
        "{keyword} 장단점이 뭔지 궁금하시죠? 오늘 팩트로 정리해볼게요.",
        "A를 할까 B를 할까... {keyword} 고민, 오늘 끝내드릴게요!",
    ],
    "empathy": [
        "{keyword} 검색하시다가 오셨죠? 그 마음 너무 잘 알아요.",
        "이 글 보시는 분들 다 비슷한 고민이실 거예요. {keyword} 관련해서요.",
        "{keyword}... 저도 처음엔 뭐가 뭔지 하나도 몰랐어요. 지금은 좀 알 것 같아요.",
        "여러분 힘드시죠? {keyword} 때문에요. 제가 도움 좀 드려볼게요.",
        "{keyword} 고민하느라 스트레스받으셨죠? 이 글 보시면 좀 나아지실 거예요.",
    ],
}

# =============================================================================
# 마무리 패턴
# =============================================================================

OUTRO_PATTERNS = [
    "오늘 {keyword}에 대해 정리해봤는데요, 도움이 되셨으면 좋겠어요! 궁금한 거 있으면 댓글 남겨주세요~",
    "여기까지 {keyword} 관련 내용이었어요. 생각보다 어렵지 않죠? 화이팅!",
    "{keyword}, 이제 좀 감이 오시나요? 저도 처음엔 막막했는데 하다 보면 익숙해져요.",
    "정리하자면 {keyword}은(는) 생각보다 간단해요. 이 글이 도움이 됐다면 공유 부탁드려요!",
    "오늘 내용이 {keyword} 고민하시는 분들께 조금이나마 도움이 됐으면 해요. 다음에 또 유용한 정보로 올게요!",
    "{keyword} 완전 정복! 이제 여러분도 할 수 있어요. 응원할게요 ㅎㅎ",
    "오늘도 긴 글 읽어주셔서 감사해요. {keyword} 관련 추가 질문은 댓글로!",
]

# =============================================================================
# CTA 버튼 설정
# =============================================================================

CTA_CONFIG = {
    "positions": ["middle", "bottom", "both"],
    "texts": [
        "자세히 알아보기",
        "지금 확인하기",
        "바로가기",
        "더 알아보기",
        "확인하러 가기",
        "신청하러 가기",
    ],
    "colors": ["#ff6b35", "#3182f6", "#00c73c", "#6b5ce7"],
}


# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_random_template() -> tuple:
    """
    랜덤 템플릿 선택

    Returns:
        (템플릿 키, 템플릿 설정) 튜플
    """
    template_key = random.choice(list(STRUCTURE_TEMPLATES.keys()))
    template = STRUCTURE_TEMPLATES[template_key].copy()

    # 깊은 복사로 sections 처리
    template["sections"] = [s.copy() for s in template["sections"]]

    # 이미지 개수 랜덤 결정
    template["selected_image_count"] = random.randint(*template["image_count"])

    # 글 길이 랜덤 결정
    template["selected_word_count"] = random.randint(*template["total_words"])

    # 리스트 아이템 개수 랜덤 결정
    for section in template["sections"]:
        if "items" in section:
            section["selected_items"] = random.randint(*section["items"])
        if "rows" in section:
            section["selected_rows"] = random.randint(*section["rows"])

    return template_key, template


def get_intro_pattern(style: str, keyword: str) -> str:
    """
    서론 패턴 랜덤 선택

    Args:
        style: 서론 스타일
        keyword: 키워드

    Returns:
        서론 문장
    """
    patterns = INTRO_PATTERNS.get(style, INTRO_PATTERNS["hook"])
    pattern = random.choice(patterns)
    return pattern.format(keyword=keyword)


def get_outro_pattern(keyword: str) -> str:
    """
    마무리 패턴 랜덤 선택

    Args:
        keyword: 키워드

    Returns:
        마무리 문장
    """
    pattern = random.choice(OUTRO_PATTERNS)
    return pattern.format(keyword=keyword)


def get_cta_config() -> dict:
    """
    CTA 설정 랜덤 선택

    Returns:
        CTA 설정 딕셔너리
    """
    return {
        "position": random.choice(CTA_CONFIG["positions"]),
        "text": random.choice(CTA_CONFIG["texts"]),
        "color": random.choice(CTA_CONFIG["colors"]),
    }


if __name__ == "__main__":
    # 테스트
    print("=== 템플릿 다양화 테스트 ===\n")

    for i in range(5):
        key, template = get_random_template()
        intro = get_intro_pattern(template["sections"][0].get("style", "hook"), "테스트 키워드")
        outro = get_outro_pattern("테스트 키워드")
        cta = get_cta_config()

        print(f"테스트 {i+1}:")
        print(f"  템플릿: {template['name']}")
        print(f"  글자수: {template['selected_word_count']}자")
        print(f"  이미지: {template['selected_image_count']}개")
        print(f"  CTA: {cta['position']} / {cta['text']}")
        print(f"  서론: {intro[:50]}...")
        print()
