"""
카테고리 매핑 및 설정
4개 카테고리 체계: 재테크, 정책/지원금, 생활정보, 트렌드
"""

# 워드프레스 카테고리 ID 매핑 (실제 WordPress ID)
CATEGORY_IDS = {
    "finance": 13,       # 재테크
    "policy": 222,       # 정책/지원금
    "life": 39,          # 생활정보
    "trend": 3,          # 트렌드
    "uncategorized": 1   # 기본값
}

# 카테고리 한글명 매핑
CATEGORY_NAMES = {
    "finance": "재테크",
    "policy": "정책/지원금",
    "life": "생활정보",
    "trend": "트렌드"
}

# 쿠팡 파트너스 허용 카테고리
COUPANG_ALLOWED = ["finance", "life"]
COUPANG_BLOCKED = ["trend", "policy"]

# 키워드 → 카테고리 매핑 규칙
CATEGORY_KEYWORDS = {
    "finance": [
        # 세금/절세
        "연말정산", "세액공제", "소득공제", "절세", "세금",
        # 투자/재테크
        "주가", "주식", "투자", "코인", "비트코인", "이더리움", "암호화폐",
        "엔비디아", "삼성전자", "테슬라", "애플",
        # 금융상품
        "연금", "연금저축", "IRP", "ISA", "예금", "적금", "펀드",
        "금리", "대출", "청약", "주담대", "ETF", "채권",
        "부동산", "전세", "월세", "퇴직금", "환율", "재테크"
    ],
    "policy": [
        # 장려금/지원금
        "근로장려금", "자녀장려금", "장려금",
        "지원금", "보조금", "수당",
        # 청년정책
        "청년", "청년도약", "청년내일", "청년정책",
        # 복지정책
        "복지", "국민연금", "기초연금", "육아휴직",
        "출산", "양육", "보육", "실업급여", "고용보험"
    ],
    "life": [
        # 세금신고
        "종합소득세", "부가가치세", "사업자",
        # 생활
        "자취", "이사", "청소", "인테리어", "요리",
        "쇼핑", "할인", "택배", "여행", "맛집",
        "교통", "교통공사", "지하철", "버스",
        "전기세", "가스비", "관리비",
        # IT/가전
        "아이폰", "갤럭시", "노트북", "컴퓨터",
        # 건강
        "다이어트", "운동", "건강검진", "병원"
    ],
    "trend": [
        # 연예
        "배우", "가수", "아이돌", "드라마", "영화", "예능",
        "뉴진스", "BTS", "블랙핑크",
        # 스포츠
        "축구", "야구", "농구", "테니스", "UFC",
        "레알마드리드", "손흥민", "오타니",
        # 시사
        "대통령", "선거", "정치", "국회"
    ]
}


def get_category_for_keyword(keyword: str) -> tuple:
    """
    키워드를 분석하여 적절한 카테고리 반환

    Args:
        keyword: 검색/트렌드 키워드

    Returns:
        (카테고리명, 카테고리ID) 튜플
    """
    keyword_lower = keyword.lower()

    # 각 카테고리의 키워드와 매칭 확인
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                return (CATEGORY_NAMES[category], CATEGORY_IDS[category])

    # 에버그린 키워드 특성 분석
    finance_indicators = ["공제", "환급", "절세", "투자", "수익"]
    policy_indicators = ["신청", "지원", "혜택", "자격", "조건"]
    life_indicators = ["방법", "신고", "등록", "서비스"]

    for indicator in finance_indicators:
        if indicator in keyword:
            return (CATEGORY_NAMES["finance"], CATEGORY_IDS["finance"])

    for indicator in policy_indicators:
        if indicator in keyword:
            return (CATEGORY_NAMES["policy"], CATEGORY_IDS["policy"])

    for indicator in life_indicators:
        if indicator in keyword:
            return (CATEGORY_NAMES["life"], CATEGORY_IDS["life"])

    # 기본값: 트렌드
    return (CATEGORY_NAMES["trend"], CATEGORY_IDS["trend"])


def get_category_id(category_name: str) -> int:
    """카테고리명으로 ID 조회"""
    # 한글명으로 조회
    for key, name in CATEGORY_NAMES.items():
        if name == category_name:
            return CATEGORY_IDS[key]
    # 영문키로 조회
    return CATEGORY_IDS.get(category_name, CATEGORY_IDS["uncategorized"])


def is_coupang_allowed(category_key: str) -> bool:
    """해당 카테고리에 쿠팡 배너 삽입이 허용되는지 확인"""
    if category_key in COUPANG_BLOCKED:
        return False
    return category_key in COUPANG_ALLOWED


if __name__ == "__main__":
    # 테스트
    print("=== 카테고리 자동 배정 테스트 ===\n")

    test_keywords = [
        "2026 연말정산 환급",
        "근로장려금 신청 방법",
        "종합소득세 신고",
        "손흥민 토트넘",
        "엔비디아 주가 전망",
        "청년도약계좌 조건",
    ]

    for kw in test_keywords:
        cat_name, cat_id = get_category_for_keyword(kw)
        print(f"{kw} → {cat_name} (ID: {cat_id})")
