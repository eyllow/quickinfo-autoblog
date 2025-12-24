"""상품 매칭 모듈 - 블로그 키워드와 관련 상품 매칭"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 키워드 확장 매핑 (특정 키워드 -> 관련 카테고리 키워드들)
KEYWORD_EXPANSION = {
    # IT/테크
    "아이폰": ["스마트폰", "휴대폰", "아이폰", "애플"],
    "갤럭시": ["스마트폰", "휴대폰", "갤럭시", "삼성"],
    "맥북": ["노트북", "맥북", "애플"],
    "노트북": ["노트북", "컴퓨터"],
    "아이패드": ["태블릿", "아이패드", "애플"],
    "에어팟": ["이어폰", "에어팟", "애플", "음향"],

    # 건강
    "다이어트": ["다이어트", "건강", "운동", "헬스"],
    "영양제": ["영양제", "비타민", "건강"],
    "운동": ["운동", "헬스", "피트니스", "건강"],

    # 생활
    "캠핑": ["캠핑", "아웃도어", "등산"],
    "등산": ["등산", "아웃도어", "캠핑", "트레킹"],
}


def match_products_for_content(
    keyword: str,
    content_summary: str = "",
    products: list[dict] = None,
    max_products: int = 2
) -> list[dict]:
    """
    블로그 키워드와 내용을 분석하여 관련 상품 매칭

    매칭 로직:
    1. 상품명에 키워드 포함 여부 (가중치: 10)
    2. 상품 키워드 목록과 매칭 (가중치: 5)
    3. 카테고리 관련성 (가중치: 3)
    4. 내용에 상품 키워드 언급 (가중치: 2)

    Args:
        keyword: 블로그 키워드
        content_summary: 블로그 내용 요약 (선택)
        products: 상품 목록
        max_products: 반환할 최대 상품 수

    Returns:
        매칭된 상품 리스트 (관련 상품 없으면 빈 리스트)
    """
    if not products:
        logger.warning("No products provided for matching")
        return []

    if not keyword:
        logger.warning("No keyword provided for matching")
        return []

    keyword_lower = keyword.lower()

    # 키워드 확장: 관련 카테고리 키워드 추가
    expanded_keywords = set([keyword_lower])
    for key, expansions in KEYWORD_EXPANSION.items():
        if key in keyword:
            for exp in expansions:
                expanded_keywords.add(exp.lower())
            logger.debug(f"Expanded keywords for '{keyword}': {expanded_keywords}")
            break

    matched = []

    for product in products:
        score = 0
        match_reasons = []

        product_name = product.get('name', '').lower()
        product_keywords = product.get('keywords', [])
        product_category = product.get('category', '').lower()

        # 1. 상품명에 키워드 포함 (가장 높은 점수)
        if keyword_lower in product_name:
            score += 10
            match_reasons.append(f"상품명 매칭")

        # 키워드의 각 단어로도 체크
        keyword_words = keyword_lower.split()
        for word in keyword_words:
            if len(word) >= 2 and word in product_name:
                score += 5
                match_reasons.append(f"상품명 부분 매칭: {word}")
                break

        # 2. 상품 키워드와 매칭 (확장 키워드 포함)
        for pk in product_keywords:
            pk_lower = pk.strip().lower()
            if not pk_lower:
                continue

            # 상품 키워드가 블로그 키워드에 포함
            if pk_lower in keyword_lower:
                score += 5
                match_reasons.append(f"키워드 매칭: {pk}")

            # 블로그 키워드가 상품 키워드에 포함
            elif keyword_lower in pk_lower:
                score += 4
                match_reasons.append(f"키워드 역매칭: {pk}")

            # 확장 키워드와 매칭 (예: 아이폰 -> 스마트폰)
            elif pk_lower in expanded_keywords:
                score += 4
                match_reasons.append(f"확장 키워드 매칭: {pk}")

            # 확장 키워드가 상품 키워드에 포함
            else:
                for exp_kw in expanded_keywords:
                    if exp_kw in pk_lower or pk_lower in exp_kw:
                        score += 3
                        match_reasons.append(f"확장 키워드 부분 매칭: {exp_kw}")
                        break

            # 부분 매칭 (2글자 이상)
            if score == 0:
                for word in keyword_words:
                    if len(word) >= 2 and word in pk_lower:
                        score += 2
                        match_reasons.append(f"키워드 부분 매칭: {word} in {pk}")
                        break

        # 3. 카테고리 관련성
        if product_category:
            for word in keyword_words:
                if len(word) >= 2 and word in product_category:
                    score += 3
                    match_reasons.append(f"카테고리 매칭: {product_category}")
                    break

        # 4. 내용에 상품명 또는 키워드 언급
        if content_summary:
            content_lower = content_summary.lower()

            if product_name in content_lower:
                score += 3
                match_reasons.append("내용에 상품명 언급")

            for pk in product_keywords:
                pk_lower = pk.strip().lower()
                if pk_lower and pk_lower in content_lower:
                    score += 2
                    match_reasons.append(f"내용에 키워드 언급: {pk}")
                    break

        # 점수가 있는 상품만 추가
        if score > 0:
            matched.append({
                'product': product,
                'score': score,
                'reasons': match_reasons
            })
            logger.debug(f"Matched: {product['name']} (score: {score}, reasons: {match_reasons})")

    # 점수순 정렬 후 상위 N개 반환
    matched.sort(key=lambda x: x['score'], reverse=True)

    result = [m['product'] for m in matched[:max_products]]

    if result:
        logger.info(f"Matched {len(result)} products for keyword '{keyword}':")
        for i, m in enumerate(matched[:max_products], 1):
            logger.info(f"  {i}. {m['product']['name']} (score: {m['score']})")
    else:
        logger.info(f"No products matched for keyword '{keyword}'")

    return result


def generate_product_html(products: list[dict]) -> str:
    """
    매칭된 상품들의 HTML 생성

    Args:
        products: 매칭된 상품 리스트

    Returns:
        상품 추천 섹션 HTML
    """
    if not products:
        return ""

    # 각 상품의 HTML 합치기
    products_html = "\n".join([p.get('html', '') for p in products if p.get('html')])

    if not products_html:
        return ""

    html = f'''
<div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
    <h4 style="margin-bottom: 15px; color: #333; font-size: 18px;">📦 관련 상품 추천</h4>
    {products_html}
    <p style="font-size: 12px; color: #888; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
        이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
    </p>
</div>
'''
    return html


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.DEBUG)

    # 테스트 상품 데이터
    test_products = [
        {
            'name': '트루웰 메이트 등산화',
            'category': '아웃도어',
            'keywords': ['등산화', '트레킹화', '등산', '산행'],
            'price': '50,000원대',
            'url': 'https://link.coupang.com/xxx',
            'html': '<div>등산화 HTML</div>'
        },
        {
            'name': '나이키 런닝화',
            'category': '스포츠',
            'keywords': ['런닝', '조깅', '운동화'],
            'price': '100,000원대',
            'url': 'https://link.coupang.com/yyy',
            'html': '<div>런닝화 HTML</div>'
        },
        {
            'name': '삼성 갤럭시 S24',
            'category': '전자기기',
            'keywords': ['스마트폰', '갤럭시', '삼성'],
            'price': '1,000,000원대',
            'url': 'https://link.coupang.com/zzz',
            'html': '<div>갤럭시 HTML</div>'
        }
    ]

    # 테스트 1: 등산화 키워드
    print("=== 테스트 1: 등산화 추천 ===")
    matched = match_products_for_content("등산화 추천", "", test_products)
    for p in matched:
        print(f"  - {p['name']}")

    print()

    # 테스트 2: 스마트폰 키워드
    print("=== 테스트 2: 갤럭시 스마트폰 ===")
    matched = match_products_for_content("갤럭시 스마트폰", "", test_products)
    for p in matched:
        print(f"  - {p['name']}")

    print()

    # 테스트 3: 관련 없는 키워드
    print("=== 테스트 3: 연말정산 (관련 없음) ===")
    matched = match_products_for_content("연말정산 환급", "", test_products)
    print(f"  매칭 결과: {len(matched)}개")
