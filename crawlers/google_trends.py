"""Google Trends RSS 크롤러"""
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

import feedparser

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class TrendItem:
    """트렌드 키워드 아이템"""
    title: str
    link: str
    pub_date: Optional[datetime]
    traffic: Optional[str] = None


class GoogleTrendsCrawler:
    """Google Trends RSS 크롤러"""

    def __init__(self, rss_url: str = None):
        self.rss_url = rss_url or settings.google_trends_rss_url

    def fetch_trends(self, limit: int = 20) -> list[TrendItem]:
        """
        Google Trends RSS에서 트렌드 키워드 수집

        Args:
            limit: 반환할 최대 키워드 수

        Returns:
            TrendItem 리스트
        """
        try:
            logger.info(f"Fetching trends from {self.rss_url}")
            feed = feedparser.parse(self.rss_url)

            if feed.bozo:
                logger.warning(f"Feed parsing warning: {feed.bozo_exception}")

            trends = []
            for entry in feed.entries[:limit]:
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])

                # 트래픽 정보 추출 (ht:approx_traffic)
                traffic = None
                if hasattr(entry, 'ht_approx_traffic'):
                    traffic = entry.ht_approx_traffic

                trend = TrendItem(
                    title=entry.title,
                    link=entry.get('link', ''),
                    pub_date=pub_date,
                    traffic=traffic
                )
                trends.append(trend)

            logger.info(f"Fetched {len(trends)} trends")
            return trends

        except Exception as e:
            logger.error(f"Error fetching trends: {e}")
            return []

    def get_trending_keywords(self, limit: int = 20) -> list[str]:
        """
        트렌드 키워드 문자열 리스트 반환

        Args:
            limit: 반환할 최대 키워드 수

        Returns:
            키워드 문자열 리스트
        """
        trends = self.fetch_trends(limit)
        return [trend.title for trend in trends]


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)
    crawler = GoogleTrendsCrawler()
    keywords = crawler.get_trending_keywords()
    print("Trending Keywords:")
    for i, keyword in enumerate(keywords, 1):
        print(f"  {i}. {keyword}")
