"""
중복 발행 방지 모듈 (1단계)
- 키워드 토큰 매칭 (2/3 이상 겹치면 중복)
- WP REST API + 로컬 DB 이중 체크
- manual_publish.py, main.py 공통 사용
"""
import re
import logging
import requests
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# 불용어 (체크에서 제외)
STOPWORDS = {
    "2024", "2025", "2026", "2027", "년", "월", "일",
    "방법", "총정리", "정리", "완벽", "가이드", "추천",
    "핵심", "실전", "활용법", "알아보기", "확인", "비교",
    "best", "top", "how", "what", "the", "가성비",
}


def extract_tokens(text: str) -> set:
    """키워드에서 의미 있는 토큰 추출"""
    # 특수문자 제거, 공백 분리
    clean = re.sub(r'[^\w\s가-힣]', ' ', text.lower())
    tokens = set(clean.split())
    # 불용어 제거
    tokens = tokens - STOPWORDS
    # 1글자 제거
    tokens = {t for t in tokens if len(t) > 1}
    return tokens


def calc_similarity(tokens_a: set, tokens_b: set) -> float:
    """두 토큰 집합의 유사도 (Jaccard-like, 작은 쪽 기준)"""
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    min_size = min(len(tokens_a), len(tokens_b))
    return len(overlap) / min_size if min_size > 0 else 0.0


def check_wp_duplicates(
    keyword: str,
    wp_url: str,
    wp_user: str,
    wp_pass: str,
    threshold: float = 0.6,
    days: int = 30
) -> Optional[dict]:
    """
    WP REST API로 중복 글 검색
    
    Returns:
        중복 글 정보 dict or None
        {"id": int, "title": str, "url": str, "similarity": float}
    """
    auth = (wp_user, wp_pass)
    new_tokens = extract_tokens(keyword)
    
    if not new_tokens:
        return None
    
    # 핵심 토큰으로 검색 (가장 긴 토큰 사용)
    search_terms = sorted(new_tokens, key=len, reverse=True)[:2]
    
    found_duplicates = []
    
    for term in search_terms:
        try:
            r = requests.get(
                f"{wp_url}/wp-json/wp/v2/posts",
                params={"search": term, "per_page": 20, "status": "publish"},
                auth=auth,
                timeout=10
            )
            if r.status_code != 200:
                continue
                
            for post in r.json():
                title = post.get("title", {}).get("rendered", "")
                title_tokens = extract_tokens(title)
                sim = calc_similarity(new_tokens, title_tokens)
                
                if sim >= threshold:
                    found_duplicates.append({
                        "id": post["id"],
                        "title": title,
                        "url": post.get("link", ""),
                        "date": post.get("date", "")[:10],
                        "similarity": round(sim, 2),
                    })
        except Exception as e:
            logger.warning(f"WP search failed for '{term}': {e}")
    
    # 중복 제거 (같은 ID)
    seen = set()
    unique = []
    for d in found_duplicates:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)
    
    if unique:
        # 유사도 높은 순 정렬
        unique.sort(key=lambda x: x["similarity"], reverse=True)
        return unique[0]
    
    return None


def check_db_duplicates(keyword: str, db, days: int = 30, threshold: float = 0.6) -> Optional[dict]:
    """
    로컬 DB에서 중복 체크
    
    Returns:
        중복 글 정보 dict or None
    """
    try:
        new_tokens = extract_tokens(keyword)
        if not new_tokens:
            return None
            
        # DB에서 최근 발행 목록
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT keyword, title, url, created_at FROM published_posts WHERE created_at >= datetime('now', ?)",
                (f'-{days} days',)
            )
            for row in cursor.fetchall():
                pub_kw, pub_title, pub_url, pub_date = row
                pub_tokens = extract_tokens(pub_kw) | extract_tokens(pub_title)
                sim = calc_similarity(new_tokens, pub_tokens)
                
                if sim >= threshold:
                    return {
                        "keyword": pub_kw,
                        "title": pub_title,
                        "url": pub_url or "",
                        "date": str(pub_date)[:10],
                        "similarity": round(sim, 2),
                    }
    except Exception as e:
        logger.warning(f"DB dedup check failed: {e}")
    
    return None


def check_duplicate(
    keyword: str,
    wp_url: str,
    wp_user: str,
    wp_pass: str,
    db=None,
    threshold: float = 0.6,
    days: int = 30
) -> Tuple[bool, Optional[dict]]:
    """
    통합 중복 체크 (WP + DB)
    
    Returns:
        (is_duplicate: bool, duplicate_info: dict or None)
    """
    # 1. WP REST API 체크
    wp_dup = check_wp_duplicates(keyword, wp_url, wp_user, wp_pass, threshold, days)
    if wp_dup:
        logger.warning(f"WP 중복 발견: [{wp_dup['id']}] {wp_dup['title'][:50]} (유사도: {wp_dup['similarity']})")
        return True, wp_dup
    
    # 2. 로컬 DB 체크
    if db:
        db_dup = check_db_duplicates(keyword, db, days, threshold)
        if db_dup:
            logger.warning(f"DB 중복 발견: {db_dup['keyword']} (유사도: {db_dup['similarity']})")
            return True, db_dup
    
    return False, None
