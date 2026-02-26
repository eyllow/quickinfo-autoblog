"""템플릿 다양화 설정 - AdSense 최적화 버전"""
import random

# =============================================================================
# 글 구조 템플릿 5종 (AdSense 최적화)
# =============================================================================

STRUCTURE_TEMPLATES = {
    "problem_solution": {
        "name": "문제-해결형",
        "description": "문제 제기 → 원인 분석 → 해결책 제시",
        "sections": [
            {"type": "intro", "style": "problem", "min_words": 200, "max_words": 350},
            {"type": "heading", "title": "왜 이런 문제가 생길까요?"},
            {"type": "content", "min_words": 400, "max_words": 600},
            {"type": "heading", "title": "효과적인 해결 방법 {count}가지"},
            {"type": "list_content", "items": [4, 6], "min_words_per_item": 150},
            {"type": "heading", "title": "실용적인 조언"},
            {"type": "content", "min_words": 350, "max_words": 500},
            {"type": "heading", "title": "마무리"},
            {"type": "outro", "min_words": 150, "max_words": 300},
        ],
        "image_count": [2, 2],
        "total_words": [2800, 4000],
    },

    "storytelling": {
        "name": "스토리텔링형",
        "description": "경험담 → 깨달음 → 정보 공유",
        "sections": [
            {"type": "intro", "style": "story", "min_words": 250, "max_words": 400},
            {"type": "heading", "title": "처음 접했을 때의 어려움"},
            {"type": "content", "min_words": 350, "max_words": 550},
            {"type": "heading", "title": "알아두면 좋은 핵심 정보"},
            {"type": "content", "min_words": 500, "max_words": 750},
            {"type": "heading", "title": "단계별 실천 방법"},
            {"type": "list_content", "items": [5, 7], "min_words_per_item": 120},
            {"type": "heading", "title": "마무리"},
            {"type": "outro", "min_words": 200, "max_words": 350},
        ],
        "image_count": [2, 2],
        "total_words": [2900, 4200],
    },

    "listicle": {
        "name": "리스트형",
        "description": "핵심 포인트 나열 중심",
        "sections": [
            {"type": "intro", "style": "hook", "min_words": 150, "max_words": 300},
            {"type": "heading", "title": "{keyword} 핵심 포인트"},
            {"type": "numbered_list", "items": [5, 8], "min_words_per_item": 180},
            {"type": "heading", "title": "추가 정보"},
            {"type": "content", "min_words": 300, "max_words": 500},
            {"type": "heading", "title": "한눈에 정리"},
            {"type": "table", "rows": [4, 6]},
            {"type": "outro", "min_words": 150, "max_words": 280},
        ],
        "image_count": [2, 2],
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
        "image_count": [2, 2],
        "total_words": [3000, 4300],
    },

    "qa_format": {
        "name": "Q&A형",
        "description": "질문-답변 형식",
        "sections": [
            {"type": "intro", "style": "empathy", "min_words": 200, "max_words": 350},
            {"type": "heading", "title": "자주 묻는 질문"},
            {"type": "qa_list", "items": [6, 8], "min_words_per_item": 150},
            {"type": "heading", "title": "추가로 알아두면 좋은 정보"},
            {"type": "content", "min_words": 350, "max_words": 550},
            {"type": "heading", "title": "정리"},
            {"type": "outro", "min_words": 180, "max_words": 300},
        ],
        "image_count": [2, 2],
        "total_words": [2700, 3900],
    },
}

# =============================================================================
# 서론 패턴 (AdSense 최적화 - 전문적 톤)
# =============================================================================

INTRO_PATTERNS = {
    "problem": [
        "{keyword}에 대해 고민하시는 분들이 많습니다. 오늘 그 해결책을 알려드릴게요.",
        "{keyword} 관련해서 어디서부터 시작해야 할지 막막하시죠? 차근차근 정리해드릴게요.",
        "{keyword} 때문에 고민이신 분들을 위해 핵심 정보를 정리해봤어요.",
        "{keyword}를 검색하시다가 이 글을 찾으셨다면, 제대로 찾아오셨어요.",
        "{keyword}에 대해 명확하게 정리해드릴게요. 처음이시더라도 쉽게 이해하실 수 있어요.",
    ],
    "story": [
        "{keyword}에 대해 처음 알아볼 때 정말 막막했어요. 그 경험을 바탕으로 정리해봤습니다.",
        "{keyword} 관련 정보를 찾다가 어려움을 겪으신 분들께 도움이 되고 싶어요.",
        "{keyword}를 처음 접했을 때 알았으면 좋았을 것들을 정리해봤어요.",
        "오늘은 {keyword}에 대한 실제 경험을 바탕으로 정보를 공유해드릴게요.",
        "{keyword} 관련해서 많은 분들이 궁금해하시는 내용을 담았어요.",
    ],
    "hook": [
        "{keyword}에 대해 알아두시면 정말 유용해요. 핵심만 정리해드릴게요.",
        "오늘 {keyword}에 대해 상세히 알려드릴게요. 필요한 정보를 모두 담았어요.",
        "{keyword} 관련 정보를 찾고 계시다면, 이 글에서 필요한 내용을 확인하실 수 있어요.",
        "이 글에서는 {keyword}에 대해 핵심 정보를 정리해드립니다.",
        "{keyword} 완벽 가이드! 필요한 정보를 한곳에 모았어요.",
    ],
    "question": [
        "{keyword}, 어떻게 해야 할까요? 오늘 명확하게 정리해드릴게요.",
        "{keyword}에 대해 고민되시는 부분이 있으시죠? 오늘 확실히 정리해드립니다.",
        "'{keyword}는 어떻게 하는 건가요?' 이 질문에 대해 상세히 답해드릴게요.",
        "{keyword}의 장단점이 궁금하시죠? 객관적으로 분석해드릴게요.",
        "{keyword} 관련 고민, 오늘 해결해드릴게요.",
    ],
    "empathy": [
        "{keyword} 관련 정보를 찾고 계시는군요. 필요한 정보를 정리해드릴게요.",
        "많은 분들이 {keyword}에 대해 비슷한 고민을 하고 계세요. 함께 알아볼까요?",
        "{keyword}에 대해 처음 알아보실 때 어려우실 수 있어요. 쉽게 설명해드릴게요.",
        "{keyword} 관련해서 도움이 필요하시다면, 이 글이 도움이 될 거예요.",
        "{keyword}에 대한 궁금증을 해결해드릴게요.",
    ],
}

# =============================================================================
# 마무리 패턴 (AdSense 최적화 - 전문적 톤)
# =============================================================================

OUTRO_PATTERNS = [
    "오늘 {keyword}에 대해 정리해봤어요. 도움이 되셨으면 좋겠습니다. 추가 질문은 댓글로 남겨주세요.",
    "여기까지 {keyword} 관련 내용이었어요. 이해가 되셨다면 다행이에요.",
    "{keyword}, 이제 좀 감이 오시나요? 처음엔 어려워 보여도 익숙해지면 괜찮아요.",
    "정리하자면 {keyword}은(는) 핵심만 알면 어렵지 않아요. 이 글이 도움이 됐다면 공유해주세요.",
    "오늘 내용이 {keyword} 관련해서 도움이 됐으면 해요. 다음에 또 유용한 정보로 찾아올게요.",
    "{keyword} 정리 완료! 필요한 분들께 도움이 되길 바랍니다.",
    "오늘도 긴 글 읽어주셔서 감사해요. {keyword} 관련 추가 질문은 댓글로 남겨주세요.",
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
