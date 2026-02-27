"""주제 선정 알고리즘 - 다중 소스 키워드 스코어링 (v2: 소스 확장 + 스코어링 개선)"""
import logging
import re
import json
import time
from typing import List, Tuple, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crawlers.google_trends import GoogleTrendsCrawler
from crawlers.naver_related import get_autocomplete, get_related_keywords
from database.models import db

logger = logging.getLogger(__name__)

import random as _random

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

def _get_headers():
    return {
        "User-Agent": _random.choice(_USER_AGENTS),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.naver.com/",
        "Connection": "keep-alive",
    }

HEADERS = _get_headers()

# 상업적 키워드 패턴 (광고 수익 가능성 높은 키워드)
COMMERCIAL_PATTERNS = [
    r"추천$", r"비교$", r"가격", r"할인", r"쿠폰", r"최저가",
    r"구매", r"리뷰", r"후기", r"순위", r"TOP", r"베스트",
    r"보험", r"대출", r"카드", r"적금", r"투자", r"재테크",
    r"다이어트", r"영양제", r"건강식품", r"화장품", r"가전",
    r"노트북", r"스마트폰", r"태블릿", r"이어폰", r"모니터",
]


class TopicSelector:
    """다중 소스 키워드 수집 + 스코어링으로 최적 주제 선정 (v2)"""

    def __init__(self):
        self.trends_crawler = GoogleTrendsCrawler()
        # 트래픽 수치 캐시: {keyword: approx_traffic_int}
        self._traffic_cache: Dict[str, int] = {}

    # =========================================================================
    # 소스 1: Google Trends RSS (기존 + 트래픽 수치 캐싱)
    # =========================================================================

    def get_google_trends_keywords(self, limit: int = 20) -> List[str]:
        """Google Trends RSS에서 키워드 수집 + 트래픽 수치 캐싱"""
        try:
            trends = self.trends_crawler.fetch_trends(limit=limit)
            keywords = []
            for t in trends:
                keywords.append(t.title)
                # 트래픽 수치 파싱 (예: "200,000+", "50K+")
                if t.traffic:
                    self._traffic_cache[t.title] = self._parse_traffic(t.traffic)
            logger.info(f"Google Trends keywords: {len(keywords)}")
            return keywords
        except Exception as e:
            logger.warning(f"Google Trends fetch failed: {e}")
            return []

    @staticmethod
    def _parse_traffic(traffic_str: str) -> int:
        """트래픽 문자열을 정수로 변환 ('200,000+' → 200000, '50K+' → 50000)"""
        try:
            s = traffic_str.replace(",", "").replace("+", "").strip()
            if s.upper().endswith("K"):
                return int(float(s[:-1]) * 1000)
            elif s.upper().endswith("M"):
                return int(float(s[:-1]) * 1_000_000)
            return int(s)
        except (ValueError, AttributeError):
            return 0

    # =========================================================================
    # 소스 2: 네이버 DataLab (기존)
    # =========================================================================

    def get_naver_datalab_keywords(self) -> List[str]:
        """네이버 DataLab 실시간 검색어 수집 (v2: 다중 폴백)"""
        keywords = []

        # 방법 1: 네이버 DataLab 쇼핑인사이트 (더 안정적)
        try:
            url = "https://datalab.naver.com/keyword/realtimeList.naver"
            resp = requests.get(url, headers=_get_headers(), timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select(".ranking_item .item_title, .keyword_rank .title, span.title"):
                    text = item.get_text(strip=True)
                    if text and len(text) >= 2 and text not in keywords:
                        keywords.append(text)
        except Exception as e:
            logger.debug(f"Naver DataLab primary failed: {e}")

        # 방법 2: 네이버 실시간 급상승 검색어 (모바일 API)
        if not keywords:
            try:
                url = "https://m.search.naver.com/p/csearch/content/qapirender.nhn?key=RealTimeSearchRank&where=nexearch&_callback=cb"
                resp = requests.get(url, headers=_get_headers(), timeout=10)
                if resp.status_code == 200:
                    # JSONP 파싱
                    import re as _re
                    json_match = _re.search(r'cb\((.*)\)', resp.text, _re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        items = data.get("data", [])
                        for item in items:
                            kw = item.get("keyword", "")
                            if kw and len(kw) >= 2:
                                keywords.append(kw)
            except Exception as e:
                logger.debug(f"Naver mobile realtime failed: {e}")

        # 방법 3: 네이버 뉴스 인기 검색어 추출 (폴백)
        if not keywords:
            try:
                url = "https://news.naver.com/"
                resp = requests.get(url, headers=_get_headers(), timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.select("a.cjs_t, .rankingnews_head a, .ofhd_lst a"):
                        text = a.get_text(strip=True)
                        if text and 2 <= len(text) <= 30 and text not in keywords:
                            keywords.append(text)
            except Exception as e:
                logger.debug(f"Naver news fallback failed: {e}")

        logger.info(f"Naver DataLab keywords: {len(keywords)}")
        return keywords[:20]

    # =========================================================================
    # 소스 3: Signal.bz 실시간 급상승 검색어 (NEW)
    # =========================================================================

    def get_signal_keywords(self) -> List[str]:
        """signal.bz 또는 대안 소스에서 실시간 급상승 검색어 수집"""
        keywords = []

        # 방법 1: signal.bz (기존)
        for url in ["https://signal.bz/news", "https://m.signal.bz/naver", "https://signal.bz/"]:
            try:
                resp = requests.get(url, headers=_get_headers(), timeout=8)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")

                for selector in [
                    "a.signal-keyword", "li.list-item a", ".rank-text",
                    "a[href*='search.naver']", ".keyword-list a", "span.keyword",
                    ".list_area a", "td a",
                ]:
                    for el in soup.select(selector):
                        text = el.get_text(strip=True)
                        if text and 2 <= len(text) <= 30 and text not in keywords:
                            keywords.append(text)
                    if keywords:
                        break

                # 폴백: 네이버 검색 URL 파싱
                if not keywords:
                    for a in soup.find_all("a", href=True):
                        href = a.get("href", "")
                        if "search.naver.com" in href and "query=" in href:
                            m = re.search(r"query=([^&]+)", href)
                            if m:
                                from urllib.parse import unquote
                                kw = unquote(m.group(1))
                                if kw and 2 <= len(kw) <= 30 and kw not in keywords:
                                    keywords.append(kw)

                if keywords:
                    break
            except Exception as e:
                logger.debug(f"Signal.bz ({url}) failed: {e}")
                continue

        # 방법 2: 네이버 실검 대안 — 다음 실시간 이슈
        if not keywords:
            try:
                resp = requests.get("https://www.daum.net/", headers=_get_headers(), timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.select(".rank_cont a, .hot_issue a, .realtime_issue a, a.link_issue"):
                        text = a.get_text(strip=True)
                        if text and 2 <= len(text) <= 30 and text not in keywords:
                            keywords.append(text)
            except Exception as e:
                logger.debug(f"Daum fallback failed: {e}")

        logger.info(f"Signal.bz keywords: {len(keywords)}")
        return keywords[:20]

    # =========================================================================
    # 소스 4: Zum 실시간 검색어 (NEW)
    # =========================================================================

    def get_zum_keywords(self) -> List[str]:
        """Zum 실시간 급상승 검색어 수집 (v2: 다중 엔드포인트)"""
        keywords = []

        # 방법 1: Zum API
        for api_url in [
            "https://search.zum.com/search/issue/realtimeKeyword",
            "https://issue.zum.com/api/v2/issue/realtime",
        ]:
            try:
                resp = requests.get(api_url, headers=_get_headers(), timeout=8)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        items = data if isinstance(data, list) else data.get("items", data.get("keywords", data.get("data", [])))
                        for item in items:
                            if isinstance(item, str):
                                keywords.append(item)
                            elif isinstance(item, dict):
                                kw = item.get("keyword", item.get("name", item.get("title", "")))
                                if kw and kw not in keywords:
                                    keywords.append(kw)
                    except (json.JSONDecodeError, ValueError):
                        pass
                if keywords:
                    break
            except Exception:
                continue

        # 방법 2: Zum 메인 페이지 스크래핑
        if not keywords:
            try:
                resp = requests.get("https://zum.com/", headers=_get_headers(), timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for selector in [".realtime_keyword", ".issue_keyword", ".hot-keyword", "a.keyword", ".rank_list a", "a[href*='search.zum.com']"]:
                        for el in soup.select(selector):
                            text = el.get_text(strip=True)
                            if text and 2 <= len(text) <= 30 and text not in keywords:
                                keywords.append(text)
                        if keywords:
                            break
            except Exception as e:
                logger.debug(f"Zum page scrape failed: {e}")

        logger.info(f"Zum keywords: {len(keywords)}")
        return keywords[:20]

    # =========================================================================
    # 소스 5: Google Trends Daily Trends (실시간 보강) (NEW)
    # =========================================================================

    def get_google_daily_trends(self) -> List[str]:
        """Google Trends Daily Trends API에서 추가 키워드 수집"""
        try:
            url = "https://trends.google.com/trends/api/dailytrends"
            params = {"hl": "ko", "tz": "-540", "geo": "KR", "ed": datetime.now().strftime("%Y%m%d"), "ns": "15"}
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)

            keywords = []
            if resp.status_code == 200:
                # Google Trends API는 ")]}'" 접두사 포함
                text = resp.text
                if text.startswith(")]}'"):
                    text = text[5:]
                try:
                    data = json.loads(text)
                    days = data.get("default", {}).get("trendingSearchesDays", [])
                    for day in days[:2]:  # 최근 2일
                        for search in day.get("trendingSearches", []):
                            title = search.get("title", {}).get("query", "")
                            if title:
                                keywords.append(title)
                                # 트래픽 수치 캐싱
                                traffic = search.get("formattedTraffic", "")
                                if traffic:
                                    self._traffic_cache[title] = self._parse_traffic(traffic)
                except (json.JSONDecodeError, KeyError):
                    pass

            logger.info(f"Google Daily Trends keywords: {len(keywords)}")
            return keywords[:20]

        except Exception as e:
            logger.warning(f"Google Daily Trends fetch failed: {e}")
            return []

    # =========================================================================
    # 스코어링 헬퍼
    # =========================================================================

    def get_naver_autocomplete_count(self, keyword: str) -> int:
        """네이버 자동완성 제안 수 반환"""
        try:
            suggestions = get_autocomplete(keyword, display=10)
            return len(suggestions)
        except Exception:
            return 0

    def _get_blog_competition(self, keyword: str) -> int:
        """네이버 블로그 검색 결과 수 추정 (낮을수록 기회)"""
        try:
            url = f"https://search.naver.com/search.naver?where=blog&query={keyword}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                # "약 N개" 패턴 매칭
                m = re.search(r'약\s*([\d,]+)\s*개', resp.text)
                if m:
                    return int(m.group(1).replace(",", ""))
                # "1-10 / N건" 패턴
                m2 = re.search(r'/([\d,]+)건', resp.text)
                if m2:
                    return int(m2.group(1).replace(",", ""))
        except Exception:
            pass
        return -1  # 측정 실패

    def _is_commercial_keyword(self, keyword: str) -> bool:
        """상업적 키워드인지 판별 (광고 수익 가능성)"""
        for pattern in COMMERCIAL_PATTERNS:
            if re.search(pattern, keyword):
                return True
        return False

    def _get_performance_bonus(self, keyword: str) -> float:
        """과거 성과 데이터 기반 보너스 (performance_learner 활용)"""
        try:
            from utils.performance_learner import PerformanceLearner
            learner = PerformanceLearner()
            insights = learner.get_keyword_insights()
            if not insights:
                return 0.0

            # 과거 고성과 키워드와 유사한 패턴이면 보너스
            high_perf_keywords = insights.get("high_performance_keywords", [])
            for hp_kw in high_perf_keywords:
                if isinstance(hp_kw, dict):
                    hp_kw = hp_kw.get("keyword", "")
                # 부분 매칭
                if hp_kw and (hp_kw in keyword or keyword in hp_kw):
                    return 2.0

            # 고성과 카테고리 보너스
            high_perf_categories = insights.get("high_performance_categories", [])
            if high_perf_categories:
                return 0.5  # 데이터 있으면 약간의 기본 보너스

        except Exception as e:
            logger.debug(f"Performance learner not available: {e}")
        return 0.0

    # =========================================================================
    # 메인 스코어링
    # =========================================================================

    def score_keywords(self, keywords_sources: dict) -> List[Tuple[str, float]]:
        """
        키워드별 점수 계산 (v2: 트래픽/경쟁도/상업성/과거성과 반영)

        Args:
            keywords_sources: {keyword: set(sources)} 매핑

        Returns:
            (keyword, score) 리스트, 점수 내림차순
        """
        scored = []
        published_keywords = set(db.get_published_keywords())

        # 스포츠/연예 차단 패턴 로드
        try:
            _eg_config = json.load(open(str(Path(__file__).resolve().parent.parent / "config" / "evergreen_keywords.json"), encoding="utf-8"))
            _blocked_patterns = _eg_config.get("blocked_patterns", [])
        except Exception:
            _blocked_patterns = [
                "경기 결과", "경기 하이라이트", "골 장면", "승리", "패배", "이적",
                "우승", "결승", "16강", "8강", "챔피언스리그", "프리미어리그",
                "KBO", "NBA", "UFC", "올림픽", "아이돌", "컴백", "팬미팅", "콘서트",
            ]

        for keyword, sources in keywords_sources.items():
            if keyword in published_keywords:
                continue
            if db.is_similar_keyword_published(keyword, days=7):
                continue

            # 스포츠/연예 키워드 차단
            _is_blocked = False
            for bp in _blocked_patterns:
                if bp in keyword:
                    _is_blocked = True
                    logger.info(f"Blocked keyword '{keyword}' (pattern: {bp})")
                    break
            if _is_blocked:
                continue

            score = 0.0

            # === 소스별 기본 점수 ===
            if "google_trends" in sources:
                score += 3.0
            if "naver_datalab" in sources:
                score += 4.0
            if "signal_bz" in sources:
                score += 3.5  # 실시간 급상승
            if "zum" in sources:
                score += 2.0
            if "google_daily" in sources:
                score += 2.5

            # === 트래픽 수치 보너스 (Google Trends approx_traffic) ===
            traffic = self._traffic_cache.get(keyword, 0)
            if traffic >= 500_000:
                score += 5.0
            elif traffic >= 200_000:
                score += 3.0
            elif traffic >= 50_000:
                score += 1.5
            elif traffic >= 10_000:
                score += 0.5

            # === 네이버 자동완성 점수 ===
            ac_count = self.get_naver_autocomplete_count(keyword)
            score += min(ac_count, 5)  # 최대 +5

            # === 연관 검색어 수 보너스 ===
            try:
                related = get_related_keywords(keyword)
                score += min(len(related), 3)  # 최대 +3
            except Exception:
                pass

            # === 상업적 키워드 보너스 (광고 수익) ===
            if self._is_commercial_keyword(keyword):
                score += 2.0

            # === 멀티소스 보너스 ===
            if len(sources) >= 3:
                score *= 1.8
            elif len(sources) >= 2:
                score *= 1.5

            # === 블로그 경쟁도 보너스 (경쟁 낮으면 유리) ===
            blog_count = self._get_blog_competition(keyword)
            if blog_count >= 0:
                if blog_count < 1000:
                    score += 3.0  # 블루오션
                elif blog_count < 10000:
                    score += 1.5
                elif blog_count > 500000:
                    score -= 1.0  # 레드오션 페널티

            # === 과거 성과 보너스 ===
            score += self._get_performance_bonus(keyword)

            scored.append((keyword, round(score, 1)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # =========================================================================
    # 메인 엔트리포인트
    # =========================================================================

    def get_best_keywords(self, limit: int = 5) -> List[str]:
        """
        최적 키워드 리스트 반환

        Args:
            limit: 반환할 키워드 수

        Returns:
            스코어링된 상위 키워드 리스트
        """
        keywords_sources = {}  # {keyword: set(sources)}

        # 1. Google Trends RSS
        gt_keywords = self.get_google_trends_keywords(limit=20)
        for kw in gt_keywords:
            keywords_sources.setdefault(kw, set()).add("google_trends")

        # 2. Naver DataLab
        nd_keywords = self.get_naver_datalab_keywords()
        for kw in nd_keywords:
            keywords_sources.setdefault(kw, set()).add("naver_datalab")

        # 3. Signal.bz 실시간 급상승
        sig_keywords = self.get_signal_keywords()
        for kw in sig_keywords:
            keywords_sources.setdefault(kw, set()).add("signal_bz")

        # 4. Zum 실시간 검색어
        zum_keywords = self.get_zum_keywords()
        for kw in zum_keywords:
            # 순번 접두사 제거 (예: "1설영우 16강 탈락" → "설영우 16강 탈락")
            cleaned = re.sub(r'^\d+', '', kw).strip()
            if cleaned:
                keywords_sources.setdefault(cleaned, set()).add("zum")

        # 5. Google Daily Trends
        gd_keywords = self.get_google_daily_trends()
        for kw in gd_keywords:
            keywords_sources.setdefault(kw, set()).add("google_daily")

        logger.info(f"Total unique keywords from all sources: {len(keywords_sources)}")
        source_counts = {}
        for kw, srcs in keywords_sources.items():
            for s in srcs:
                source_counts[s] = source_counts.get(s, 0) + 1
        logger.info(f"Keywords per source: {source_counts}")

        # 스코어링
        scored = self.score_keywords(keywords_sources)

        result = [kw for kw, _ in scored[:limit]]
        if scored[:limit]:
            for kw, sc in scored[:limit]:
                logger.info(f"  Selected: '{kw}' (score: {sc})")

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    selector = TopicSelector()
    best = selector.get_best_keywords(limit=5)
    print(f"\nBest keywords: {best}")
