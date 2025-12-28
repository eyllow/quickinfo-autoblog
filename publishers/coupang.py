"""
쿠팡 파트너스 배너 삽입 모듈
조건에 맞는 글에 쿠팡 배너를 삽입합니다.
"""
import re
import logging
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.categories import is_coupang_allowed

logger = logging.getLogger(__name__)

# 쿠팡 배너 HTML 템플릿
COUPANG_BANNER_TEMPLATE = '''
<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; text-align: center;">
    <p style="margin: 0 0 15px 0; font-size: 15px; color: #666;">
        💰 이 상품 어때요?
    </p>
    <a href="{url}" target="_blank" rel="noopener noreferrer"
       style="display: inline-block; padding: 12px 24px; background: #ff6b35; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
        {button_text}
    </a>
</div>
'''

# 파트너스 고지 문구
AFFILIATE_NOTICE = '''
<p style="margin-top: 40px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 13px; color: #666; text-align: center;">
    이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
</p>
'''

# 키워드별 CTA 버튼 텍스트
KEYWORD_CTA_MAPPING = {
    "아이폰": "아이폰 최저가 확인하기",
    "갤럭시": "갤럭시 최저가 확인하기",
    "노트북": "노트북 추천 보기",
    "에어컨": "에어컨 최저가 보기",
    "냉장고": "냉장고 추천 보기",
    "세탁기": "세탁기 추천 보기",
    "청소기": "청소기 추천 보기",
    "건강": "건강식품 추천 보기",
    "영양제": "영양제 추천 보기",
    "비타민": "비타민 추천 보기",
    "다이어트": "다이어트 보조제 보기",
    "운동": "운동용품 추천 보기",
    "자동차": "자동차 용품 보기",
}


def get_cta_text(keyword: str) -> str:
    """
    키워드에 맞는 CTA 버튼 텍스트 반환

    Args:
        keyword: 키워드

    Returns:
        CTA 버튼 텍스트
    """
    for key, text in KEYWORD_CTA_MAPPING.items():
        if key in keyword:
            return text
    return "쿠팡에서 확인하기"


def generate_coupang_url(keyword: str) -> str:
    """
    쿠팡 검색 URL 생성

    Args:
        keyword: 검색 키워드

    Returns:
        쿠팡 검색 URL
    """
    partner_id = settings.coupang_partner_id
    base_url = "https://www.coupang.com/np/search"

    # 키워드 인코딩
    import urllib.parse
    encoded_keyword = urllib.parse.quote(keyword)

    url = f"{base_url}?q={encoded_keyword}"

    # 파트너스 ID 추가
    if partner_id:
        url += f"&lptag={partner_id}"

    return url


def insert_coupang_banner(
    content: str,
    keyword: str,
    category: str,
    position: str = "bottom"
) -> tuple:
    """
    쿠팡 배너 삽입

    Args:
        content: HTML 본문
        keyword: 키워드
        category: 카테고리
        position: 삽입 위치 (middle, bottom, both)

    Returns:
        (수정된 본문, 삽입 여부) 튜플
    """
    # 쿠팡 허용 카테고리 확인
    if not is_coupang_allowed(category):
        logger.info(f"쿠팡 비허용 카테고리: {category}")
        # [COUPANG] 태그 제거
        content = content.replace("[COUPANG]", "")
        return content, False

    # 파트너스 ID 확인
    if not settings.coupang_partner_id:
        logger.warning("쿠팡 파트너스 ID가 설정되지 않았습니다.")
        content = content.replace("[COUPANG]", "")
        return content, False

    # 배너 생성
    coupang_url = generate_coupang_url(keyword)
    cta_text = get_cta_text(keyword)

    banner_html = COUPANG_BANNER_TEMPLATE.format(
        url=coupang_url,
        button_text=cta_text
    )

    # [COUPANG] 태그가 있으면 교체
    if "[COUPANG]" in content:
        content = content.replace("[COUPANG]", banner_html)
        logger.info("쿠팡 배너 삽입 완료 (태그 위치)")
    else:
        # 태그가 없으면 위치에 따라 삽입
        if position in ["bottom", "both"]:
            # 마지막 </div> 앞에 삽입
            last_div = content.rfind("</div>")
            if last_div != -1:
                content = content[:last_div] + banner_html + content[last_div:]
            else:
                content += banner_html
            logger.info("쿠팡 배너 삽입 완료 (하단)")

        if position in ["middle", "both"]:
            # 중간에 삽입 (3번째 </p> 뒤)
            p_matches = list(re.finditer(r'</p>', content))
            if len(p_matches) >= 3:
                insert_pos = p_matches[2].end()
                content = content[:insert_pos] + banner_html + content[insert_pos:]
                logger.info("쿠팡 배너 삽입 완료 (중간)")

    # 파트너스 고지 추가
    if AFFILIATE_NOTICE not in content:
        content += AFFILIATE_NOTICE
        logger.info("파트너스 고지 추가 완료")

    return content, True


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 쿠팡 배너 테스트 ===\n")

    # 허용 카테고리 테스트
    test_cases = [
        ("아이폰16", "IT/가전"),
        ("비트코인", "재테크"),
        ("BTS 콘서트", "연예"),
        ("다이어트", "건강"),
    ]

    for keyword, category in test_cases:
        allowed = is_coupang_allowed(category)
        cta = get_cta_text(keyword)
        print(f"{keyword} ({category})")
        print(f"  쿠팡 허용: {'✅' if allowed else '❌'}")
        print(f"  CTA 텍스트: {cta}")
        print()
