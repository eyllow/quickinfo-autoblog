"""
QuickInfo 카테고리 자동 배정 설정
키워드 기반으로 적절한 카테고리를 자동 선택

4개 카테고리 체계:
- 재테크: 세금/절세, 투자/재테크, 금융상품
- 정책/지원금: 장려금, 청년정책, 복지정책
- 생활정보: 세금신고, 취업/실업, 공공서비스, 생활
- 트렌드: 연예, 스포츠, 시사
"""

# WordPress 카테고리 ID 매핑
# WordPress에서 카테고리 생성 후 실제 ID로 업데이트 필요
# curl -s "https://quickinfo.kr/wp-json/wp/v2/categories" | python3 -m json.tool
CATEGORY_IDS = {
    "finance": 2,      # 재테크
    "policy": 3,       # 정책/지원금
    "life": 4,         # 생활정보
    "trend": 5,        # 트렌드
    "uncategorized": 1 # 기본값
}

# 카테고리명 매핑 (영문 키 → 한글 카테고리명)
CATEGORY_NAMES = {
    "finance": "재테크",
    "policy": "정책/지원금",
    "life": "생활정보",
    "trend": "트렌드",
    "uncategorized": "미분류"
}

# 카테고리별 키워드 매핑
CATEGORY_KEYWORDS = {
    "finance": [
        # 세금/절세
        "연말정산", "세액공제", "소득공제", "절세", "세금",
        # 투자/재테크
        "주가", "주식", "투자", "코인", "비트코인", "이더리움", "암호화폐",
        "엔비디아", "삼성전자", "테슬라", "애플", "증시", "코스피", "코스닥",
        # 금융상품
        "연금", "연금저축", "IRP", "ISA", "예금", "적금", "펀드",
        "금리", "대출", "청약", "주담대", "전세대출", "신용대출",
        # 부동산
        "부동산", "전세", "월세", "아파트", "분양",
    ],

    "policy": [
        # 장려금/지원금
        "근로장려금", "자녀장려금", "장려금",
        "지원금", "보조금", "수당", "급여",
        # 청년정책
        "청년", "청년도약", "청년내일", "청년정책", "청년통장",
        # 복지정책
        "복지", "국민연금", "기초연금", "육아휴직",
        "출산", "양육", "보육", "주거급여", "생계급여",
        # 정부 서비스
        "정부", "신청", "혜택",
    ],

    "life": [
        # 세금신고
        "종합소득세", "부가가치세", "사업자",
        # 취업/실업
        "실업급여", "고용보험", "퇴직금", "퇴직", "취업", "이직",
        # 공공서비스
        "교통공사", "지하철", "버스", "공공기관",
        # 보험/생활
        "보험", "건강보험", "자동차보험", "자동차",
        "이사", "전입신고", "주민등록", "운전면허",
        # IT/가전
        "아이폰", "갤럭시", "노트북", "스마트폰",
        # 건강
        "다이어트", "운동", "건강", "영양제",
        # 생활일반
        "여행", "맛집", "레시피", "인테리어",
    ],

    "trend": [
        # 연예
        "배우", "가수", "아이돌", "드라마", "영화", "예능",
        "뉴진스", "BTS", "블랙핑크", "에스파", "아이브",
        "넷플릭스", "디즈니", "웨이브",
        # 스포츠
        "축구", "야구", "농구", "테니스", "UFC",
        "레알마드리드", "손흥민", "오타니", "이강인", "김민재",
        # 시사
        "대통령", "선거", "정치", "국회", "검찰",
    ]
}

# 쿠팡 파트너스 허용 카테고리
COUPANG_ALLOWED = ["life"]

# 쿠팡 파트너스 비허용 카테고리
COUPANG_BLOCKED = ["finance", "policy", "trend"]


def get_category_for_keyword(keyword: str) -> tuple[str, int]:
    """
    키워드를 분석하여 적절한 카테고리 반환

    Args:
        keyword: 검색/트렌드 키워드

    Returns:
        (카테고리 영문키, 카테고리ID) 튜플
    """
    keyword_lower = keyword.lower()

    # 각 카테고리의 키워드와 매칭 확인
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                return (category, CATEGORY_IDS[category])

    # 에버그린 키워드 특성 분석 (정책/금융 관련 단어 포함 여부)
    finance_indicators = ["공제", "환급", "절세", "투자", "수익", "금리", "배당"]
    policy_indicators = ["신청", "지원", "혜택", "자격", "조건", "수급"]
    life_indicators = ["방법", "신고", "등록", "서비스", "절차", "준비"]

    for indicator in finance_indicators:
        if indicator in keyword:
            return ("finance", CATEGORY_IDS["finance"])

    for indicator in policy_indicators:
        if indicator in keyword:
            return ("policy", CATEGORY_IDS["policy"])

    for indicator in life_indicators:
        if indicator in keyword:
            return ("life", CATEGORY_IDS["life"])

    # 기본값: 트렌드
    return ("trend", CATEGORY_IDS["trend"])


def get_category_id(category_key: str) -> int:
    """
    카테고리 키(영문)로 ID 조회

    Args:
        category_key: 카테고리 영문 키 (finance, policy, life, trend)

    Returns:
        카테고리 ID (기본값: 1)
    """
    return CATEGORY_IDS.get(category_key, CATEGORY_IDS["uncategorized"])


def get_category_name(category_key: str) -> str:
    """
    카테고리 키(영문)로 한글 이름 조회

    Args:
        category_key: 카테고리 영문 키

    Returns:
        카테고리 한글 이름
    """
    return CATEGORY_NAMES.get(category_key, "트렌드")


def is_coupang_allowed(category_key: str) -> bool:
    """
    해당 카테고리에 쿠팡 배너 삽입이 허용되는지 확인

    Args:
        category_key: 카테고리 영문 키

    Returns:
        True면 허용, False면 비허용
    """
    if category_key in COUPANG_BLOCKED:
        return False
    return category_key in COUPANG_ALLOWED


# 레거시 호환용 (기존 코드에서 사용하는 경우)
CATEGORIES = {
    "재테크": CATEGORY_IDS["finance"],
    "정책/지원금": CATEGORY_IDS["policy"],
    "생활정보": CATEGORY_IDS["life"],
    "트렌드": CATEGORY_IDS["trend"],
}

KEYWORD_CATEGORY_RULES = {
    "재테크": CATEGORY_KEYWORDS["finance"],
    "정책/지원금": CATEGORY_KEYWORDS["policy"],
    "생활정보": CATEGORY_KEYWORDS["life"],
    "트렌드": CATEGORY_KEYWORDS["trend"],
}


if __name__ == "__main__":
    # 테스트
    print("=== 카테고리 자동 배정 테스트 ===\n")

    test_keywords = [
        "2026 연말정산 환급",
        "근로장려금 신청 방법",
        "종합소득세 신고",
        "손흥민 토트넘",
        "엔비디아 주가 전망",
        "청년도약계좌 가입",
        "실업급여 신청",
        "아이폰16 스펙",
    ]

    for kw in test_keywords:
        cat_key, cat_id = get_category_for_keyword(kw)
        cat_name = get_category_name(cat_key)
        print(f"{kw} → {cat_name} ({cat_key}, ID: {cat_id})")
