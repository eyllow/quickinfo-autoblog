"""주제 선정 알고리즘 - 다중 소스 키워드 스코어링"""
import logging
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crawlers.google_trends import GoogleTrendsCrawler
from crawlers.naver_related import get_autocomplete
from database.models import db

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class TopicSelector:
    """다중 소스 키워드 수집 + 스코어링으로 최적 주제 선정"""

    def __init__(self):
        self.trends_crawler = GoogleTrendsCrawler()

    def get_google_trends_keywords(self, limit: int = 20) -> List[str]:
        """Google Trends RSS에서 키워드 수집"""
        try:
            return self.trends_crawler.get_trending_keywords_simple(limit=limit)
        except Exception as e:
            logger.warning(f"Google Trends fetch failed: {e}")
            return []

    def get_naver_datalab_keywords(self) -> List[str]:
        """네이버 DataLab 실시간 검색어 수집"""
        try:
            url = "https://datalab.naver.com/keyword/realtimeList.naver"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            keywords = []
            for item in soup.select(".ranking_item .item_title, .keyword_rank .title"):
                text = item.get_text(strip=True)
                if text and len(text) >= 2:
                    keywords.append(text)

            # 폴백: JSON API 시도
            if not keywords:
                try:
                    api_url = "https://datalab.naver.com/keyword/realtimeList.naver?age=20s"
                    resp2 = requests.get(api_url, headers=HEADERS, timeout=10)
                    if resp2.status_code == 200:
                        # HTML에서 키워드 추출 시도
                        soup2 = BeautifulSoup(resp2.text, "html.parser")
                        for span in soup2.select("span.title"):
                            text = span.get_text(strip=True)
                            if text and len(text) >= 2:
                                keywords.append(text)
                except Exception:
                    pass

            logger.info(f"Naver DataLab keywords: {len(keywords)}")
            return keywords[:20]

        except Exception as e:
            logger.warning(f"Naver DataLab fetch failed: {e}")
            return []

    def get_naver_autocomplete_count(self, keyword: str) -> int:
        """네이버 자동완성 제안 수 반환"""
        try:
            suggestions = get_autocomplete(keyword, display=10)
            return len(suggestions)
        except Exception:
            return 0

    def score_keywords(self, keywords_sources: dict) -> List[Tuple[str, float]]:
        """
        키워드별 점수 계산

        Args:
            keywords_sources: {keyword: set(sources)} 매핑

        Returns:
            (keyword, score) 리스트, 점수 내림차순
        """
        scored = []
        published_keywords = set(db.get_published_keywords())

        for keyword, sources in keywords_sources.items():
            # 이미 발행된 키워드 스킵
            if keyword in published_keywords:
                continue
            # DB 유사 키워드 체크
            if db.is_similar_keyword_published(keyword, days=7):
                continue

            score = 0.0

            # 소스별 점수
            if "google_trends" in sources:
                score += 3
            if "naver_datalab" in sources:
                score += 4

            # 네이버 자동완성 점수
            ac_count = self.get_naver_autocomplete_count(keyword)
            score += min(ac_count, 5)  # 최대 +5

            # 멀티소스 보너스
            if len(sources) >= 2:
                score *= 1.5

            scored.append((keyword, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def get_best_keywords(self, limit: int = 5) -> List[str]:
        """
        최적 키워드 리스트 반환

        Args:
            limit: 반환할 키워드 수

        Returns:
            스코어링된 상위 키워드 리스트
        """
        keywords_sources = {}  # {keyword: set(sources)}

        # 1. Google Trends
        gt_keywords = self.get_google_trends_keywords(limit=20)
        for kw in gt_keywords:
            keywords_sources.setdefault(kw, set()).add("google_trends")

        # 2. Naver DataLab
        nd_keywords = self.get_naver_datalab_keywords()
        for kw in nd_keywords:
            keywords_sources.setdefault(kw, set()).add("naver_datalab")

        logger.info(f"Total unique keywords from all sources: {len(keywords_sources)}")

        # 3. 스코어링
        scored = self.score_keywords(keywords_sources)

        result = [kw for kw, _ in scored[:limit]]
        if scored[:limit]:
            for kw, sc in scored[:limit]:
                logger.info(f"  Selected: '{kw}' (score: {sc:.1f})")

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    selector = TopicSelector()
    best = selector.get_best_keywords(limit=5)
    print(f"Best keywords: {best}")
