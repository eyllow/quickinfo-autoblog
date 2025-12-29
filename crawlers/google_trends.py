"""Google Trends RSS 크롤러 - 트렌드 맥락 파악 기능 포함"""
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

import feedparser
import requests
from bs4 import BeautifulSoup

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
    news_items: list = None
    trend_context: str = ""

    def __post_init__(self):
        if self.news_items is None:
            self.news_items = []


class GoogleTrendsCrawler:
    """Google Trends RSS 크롤러 - 트렌드 맥락 파악 기능 포함"""

    def __init__(self, rss_url: str = None):
        self.rss_url = rss_url or settings.google_trends_rss_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

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

                # 관련 뉴스 추출 (RSS에 포함된 경우)
                news_items = []
                if hasattr(entry, 'ht_news_item'):
                    items = entry.ht_news_item if isinstance(entry.ht_news_item, list) else [entry.ht_news_item]
                    for news in items[:3]:
                        if hasattr(news, 'ht_news_item_title'):
                            news_items.append({
                                "title": news.ht_news_item_title,
                                "url": getattr(news, 'ht_news_item_url', ''),
                                "source": getattr(news, 'ht_news_item_source', '')
                            })

                # 뉴스 제목들로 트렌드 맥락 생성
                trend_context = ""
                if news_items:
                    news_titles = [n["title"] for n in news_items]
                    trend_context = " | ".join(news_titles)

                trend = TrendItem(
                    title=entry.title,
                    link=entry.get('link', ''),
                    pub_date=pub_date,
                    traffic=traffic,
                    news_items=news_items,
                    trend_context=trend_context
                )
                trends.append(trend)

            logger.info(f"Fetched {len(trends)} trends")
            return trends

        except Exception as e:
            logger.error(f"Error fetching trends: {e}")
            return []

    def get_trend_context(self, keyword: str) -> dict:
        """
        특정 키워드에 대한 최신 뉴스 맥락 수집 (네이버 뉴스)

        Args:
            keyword: 검색 키워드

        Returns:
            트렌드 맥락 정보 딕셔너리
        """
        try:
            # 네이버 뉴스 검색 (최신순)
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sort=1"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            news_items = []

            # 뉴스 아이템 추출
            articles = soup.select("div.news_wrap, li.bx")[:5]  # 최신 5개

            for article in articles:
                title_elem = article.select_one("a.news_tit, a.title")
                if title_elem:
                    news_items.append({
                        "title": title_elem.get_text(strip=True),
                        "url": title_elem.get("href", "")
                    })

            # 뉴스 제목들을 요약하여 트렌드 맥락 생성
            context = {
                "keyword": keyword,
                "news_titles": [n["title"] for n in news_items],
                "trend_summary": " | ".join([n["title"] for n in news_items[:3]]),
                "news_count": len(news_items)
            }

            logger.info(f"Trend context for '{keyword}': {context['news_count']} news items found")
            return context

        except Exception as e:
            logger.warning(f"트렌드 맥락 수집 오류 ({keyword}): {e}")
            return {
                "keyword": keyword,
                "news_titles": [],
                "trend_summary": "",
                "news_count": 0
            }

    def get_trending_keywords(self, limit: int = 20) -> list[dict]:
        """
        트렌드 키워드와 맥락 정보를 딕셔너리 리스트로 반환

        Args:
            limit: 반환할 최대 키워드 수

        Returns:
            키워드 정보 딕셔너리 리스트
        """
        trends = self.fetch_trends(limit)
        result = []

        for trend in trends:
            keyword_data = {
                "keyword": trend.title,
                "category": "트렌드",
                "traffic": trend.traffic or "",
                "news_items": trend.news_items,
                "trend_context": trend.trend_context
            }
            result.append(keyword_data)

        return result

    def get_trending_keywords_simple(self, limit: int = 20) -> list[str]:
        """
        트렌드 키워드 문자열 리스트 반환 (기존 호환용)

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

    print("\n=== 트렌드 키워드 ===")
    keywords = crawler.get_trending_keywords()
    for i, kw in enumerate(keywords[:5], 1):
        print(f"\n{i}. {kw['keyword']}")
        print(f"   트래픽: {kw['traffic']}")
        print(f"   맥락: {kw['trend_context'][:100]}..." if kw['trend_context'] else "   맥락: 없음")

    print("\n\n=== 특정 키워드 맥락 테스트 ===")
    context = crawler.get_trend_context("날씨")
    print(f"키워드: {context['keyword']}")
    print(f"뉴스 수: {context['news_count']}")
    for title in context['news_titles'][:3]:
        print(f"  - {title}")
