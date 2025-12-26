"""
Google Trends 키워드 수집 모듈
한국 실시간 급상승 키워드를 수집합니다.
"""
import logging
import feedparser
from typing import List, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.categories import get_category_for_keyword

logger = logging.getLogger(__name__)

# Google Trends RSS 피드 URL (한국)
TRENDS_RSS_URL = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR"


class GoogleTrendsCrawler:
    """Google Trends 키워드 수집기"""

    def __init__(self):
        self.rss_url = TRENDS_RSS_URL

    def fetch_trending_keywords(self, limit: int = 20) -> List[dict]:
        """
        실시간 급상승 키워드 수집

        Args:
            limit: 수집할 키워드 최대 개수

        Returns:
            키워드 정보 리스트
            [{"keyword": "키워드", "category": "카테고리", "traffic": "검색량"}]
        """
        try:
            logger.info(f"Google Trends RSS 피드 요청: {self.rss_url}")
            feed = feedparser.parse(self.rss_url)

            if not feed.entries:
                logger.warning("트렌드 키워드를 찾을 수 없습니다.")
                return []

            keywords = []
            for entry in feed.entries[:limit]:
                keyword = entry.get("title", "").strip()
                if not keyword:
                    continue

                # 카테고리 자동 분류
                category = get_category_for_keyword(keyword)

                # 검색량 추출 (approx_traffic)
                traffic = entry.get("ht_approx_traffic", "N/A")

                keywords.append({
                    "keyword": keyword,
                    "category": category,
                    "traffic": traffic,
                    "published": entry.get("published", ""),
                })

            logger.info(f"총 {len(keywords)}개 트렌드 키워드 수집 완료")
            return keywords

        except Exception as e:
            logger.error(f"트렌드 키워드 수집 실패: {e}")
            return []

    def get_best_keyword(self, exclude_keywords: List[str] = None) -> Optional[dict]:
        """
        발행에 가장 적합한 키워드 1개 선택

        Args:
            exclude_keywords: 제외할 키워드 목록 (이미 발행된 키워드)

        Returns:
            선택된 키워드 정보 또는 None
        """
        if exclude_keywords is None:
            exclude_keywords = []

        keywords = self.fetch_trending_keywords(limit=20)

        for kw_info in keywords:
            keyword = kw_info["keyword"]

            # 이미 발행된 키워드 제외
            if keyword in exclude_keywords:
                logger.debug(f"이미 발행된 키워드 제외: {keyword}")
                continue

            # 너무 짧은 키워드 제외
            if len(keyword) < 2:
                continue

            # 특수문자만 있는 키워드 제외
            if not any(c.isalnum() for c in keyword):
                continue

            logger.info(f"선택된 트렌드 키워드: {keyword} (카테고리: {kw_info['category']})")
            return kw_info

        logger.warning("적합한 트렌드 키워드를 찾을 수 없습니다.")
        return None


def get_trending_keyword(exclude_keywords: List[str] = None) -> Optional[dict]:
    """
    트렌드 키워드 1개 가져오기 (편의 함수)

    Args:
        exclude_keywords: 제외할 키워드 목록

    Returns:
        키워드 정보 또는 None
    """
    crawler = GoogleTrendsCrawler()
    return crawler.get_best_keyword(exclude_keywords)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== Google Trends 키워드 수집 테스트 ===\n")

    crawler = GoogleTrendsCrawler()
    keywords = crawler.fetch_trending_keywords(limit=10)

    print(f"수집된 키워드 ({len(keywords)}개):\n")
    for i, kw in enumerate(keywords, 1):
        print(f"{i}. {kw['keyword']}")
        print(f"   카테고리: {kw['category']}")
        print(f"   검색량: {kw['traffic']}")
        print()
