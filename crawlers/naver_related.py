"""
네이버 연관검색어 / 자동완성 크롤러
키워드를 입력하면 네이버에서 연관검색어와 자동완성 추천어를 수집합니다.
"""
import requests
import logging
import re
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

AUTOCOMPLETE_URL = "https://ac.search.naver.com/nx/ac"
SEARCH_URL = "https://search.naver.com/search.naver"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def get_autocomplete(keyword: str, display: int = 10) -> List[str]:
    """
    네이버 자동완성 추천어 수집

    Args:
        keyword: 검색 키워드
        display: 최대 결과 수

    Returns:
        자동완성 키워드 리스트
    """
    params = {
        "q": keyword,
        "con": "1",
        "frm": "nv",
        "ans": "2",
        "r_format": "json",
        "r_enc": "UTF-8",
        "r_unicode": "0",
        "t_koreng": "1",
        "run": "2",
        "rev": "4",
        "q_enc": "UTF-8",
    }

    try:
        resp = requests.get(AUTOCOMPLETE_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [[]])[0] if data.get("items") else []
        results = [item[0] for item in items if item][:display]

        logger.info(f"[autocomplete] '{keyword}' → {len(results)}개")
        return results

    except Exception as e:
        logger.error(f"[autocomplete] '{keyword}' 실패: {e}")
        return []


def get_related_keywords(keyword: str) -> List[str]:
    """
    네이버 검색 결과 페이지에서 연관검색어 수집

    Args:
        keyword: 검색 키워드

    Returns:
        연관검색어 리스트
    """
    params = {"where": "nexearch", "query": keyword}

    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        html = resp.text

        # 연관검색어 추출 (여러 패턴 시도)
        results = []

        # 패턴 1: data-area="related" 영역
        related_block = re.search(
            r'<div[^>]*class="[^"]*related_srch[^"]*"[^>]*>(.*?)</div>',
            html, re.DOTALL
        )
        if related_block:
            links = re.findall(r'<a[^>]*>(.*?)</a>', related_block.group(1))
            results.extend([re.sub(r'<[^>]+>', '', link).strip() for link in links])

        # 패턴 2: 연관 검색어 리스트
        related_items = re.findall(
            r'class="[^"]*keyword[^"]*"[^>]*>\s*([^<]+)\s*<',
            html
        )
        results.extend([item.strip() for item in related_items if item.strip()])

        # 중복 제거 및 빈 문자열 제거
        seen = set()
        unique = []
        for r in results:
            if r and r not in seen and r != keyword:
                seen.add(r)
                unique.append(r)

        logger.info(f"[related] '{keyword}' → {len(unique)}개")
        return unique

    except Exception as e:
        logger.error(f"[related] '{keyword}' 실패: {e}")
        return []


def expand_keywords(seed_keyword: str) -> Dict[str, List[str]]:
    """
    시드 키워드에서 자동완성 + 연관검색어를 모두 수집

    Args:
        seed_keyword: 시드 키워드

    Returns:
        {"autocomplete": [...], "related": [...]}
    """
    autocomplete = get_autocomplete(seed_keyword)
    related = get_related_keywords(seed_keyword)

    return {
        "autocomplete": autocomplete,
        "related": related,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    keyword = sys.argv[1] if len(sys.argv) > 1 else "연말정산"
    result = expand_keywords(keyword)

    print(f"\n=== '{keyword}' 키워드 확장 ===\n")
    print("자동완성:")
    for i, kw in enumerate(result["autocomplete"], 1):
        print(f"  {i}. {kw}")
    print("\n연관검색어:")
    for i, kw in enumerate(result["related"], 1):
        print(f"  {i}. {kw}")
