"""네이버 뉴스 + Google News RSS 크롤러"""
import logging
import time
import re
import xml.etree.ElementTree as ET
from typing import Optional, List
from dataclasses import dataclass
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)

# 봇 차단 방지 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    link: str
    summary: str
    source: Optional[str] = None
    date: Optional[str] = None


class NaverNewsCrawler:
    """네이버 뉴스 크롤러"""

    def __init__(self):
        self.search_url = settings.naver_search_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search_news(self, keyword: str, max_articles: int = 3) -> list[NewsArticle]:
        """
        키워드로 네이버 뉴스 검색

        Args:
            keyword: 검색 키워드
            max_articles: 최대 기사 수

        Returns:
            NewsArticle 리스트
        """
        try:
            # 뉴스 탭 검색 URL
            search_url = f"{self.search_url}?where=news&query={quote(keyword)}&sm=tab_jum"
            logger.info(f"Searching news for: {keyword}")

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []

            # 뉴스 검색 결과에서 네이버 뉴스 링크만 추출
            news_items = soup.select('div.news_area')

            for item in news_items[:max_articles * 2]:  # 여유있게 검색
                if len(articles) >= max_articles:
                    break

                # 제목과 링크 추출
                title_elem = item.select_one('a.news_tit')
                if not title_elem:
                    continue

                title = title_elem.get('title', title_elem.get_text(strip=True))
                link = title_elem.get('href', '')

                # news.naver.com 링크만 필터링
                naver_news_link = None

                # 네이버 뉴스 링크 찾기
                naver_links = item.select('a[href*="news.naver.com"]')
                for nl in naver_links:
                    href = nl.get('href', '')
                    if 'news.naver.com/article' in href or 'news.naver.com/main' in href:
                        naver_news_link = href
                        break

                if not naver_news_link:
                    # 다른 방식으로 네이버 뉴스 링크 찾기
                    info_group = item.select_one('div.info_group')
                    if info_group:
                        for a_tag in info_group.find_all('a'):
                            href = a_tag.get('href', '')
                            if 'news.naver.com' in href:
                                naver_news_link = href
                                break

                if not naver_news_link:
                    continue

                # 기사 본문 추출
                time.sleep(0.5)  # 딜레이
                article_content = self._fetch_article_content(naver_news_link)

                if article_content:
                    # 출처 추출
                    source = None
                    source_elem = item.select_one('a.info.press')
                    if source_elem:
                        source = source_elem.get_text(strip=True)

                    # 날짜 추출
                    date = None
                    date_elem = item.select_one('span.info')
                    if date_elem:
                        date = date_elem.get_text(strip=True)

                    article = NewsArticle(
                        title=title,
                        link=naver_news_link,
                        summary=article_content,
                        source=source,
                        date=date
                    )
                    articles.append(article)

                time.sleep(0.5)  # 차단 방지 딜레이

            logger.info(f"Found {len(articles)} articles for: {keyword}")
            return articles

        except Exception as e:
            logger.error(f"Error searching news for {keyword}: {e}")
            return []

    def _fetch_article_content(self, url: str) -> Optional[str]:
        """
        네이버 뉴스 기사 본문 추출 및 3줄 요약

        Args:
            url: 기사 URL

        Returns:
            3줄 요약 문자열
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 본문 추출 (여러 선택자 시도)
            content = None

            # 스포츠/연예 뉴스
            article_body = soup.select_one('#articeBody, #articleBodyContents, #newsct_article')
            if article_body:
                content = article_body.get_text(strip=True)

            # 일반 뉴스
            if not content:
                article_body = soup.select_one('article#dic_area')
                if article_body:
                    content = article_body.get_text(strip=True)

            # 다른 형식
            if not content:
                article_body = soup.select_one('div._article_body_contents, div.newsct_article')
                if article_body:
                    content = article_body.get_text(strip=True)

            if not content:
                return None

            # 불필요한 텍스트 제거
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'[\n\r\t]', ' ', content)

            # 3줄 요약 생성 (문장 단위로 분리)
            sentences = re.split(r'[.!?]\s+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

            if len(sentences) >= 3:
                summary = '. '.join(sentences[:3]) + '.'
            elif sentences:
                summary = '. '.join(sentences) + '.'
            else:
                summary = content[:300] + '...' if len(content) > 300 else content

            return summary

        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None

    def get_news_summary(self, keyword: str, max_articles: int = 3) -> str:
        """
        키워드 관련 뉴스 요약 반환

        Args:
            keyword: 검색 키워드
            max_articles: 최대 기사 수

        Returns:
            통합 뉴스 요약 문자열
        """
        articles = self.search_news(keyword, max_articles)

        if not articles:
            return f"'{keyword}'에 대한 최신 뉴스를 찾을 수 없습니다."

        summaries = []
        for i, article in enumerate(articles, 1):
            summary = f"[기사 {i}] {article.title}\n{article.summary}"
            if article.source:
                summary += f"\n출처: {article.source}"
            summaries.append(summary)

        return "\n\n".join(summaries)


class GoogleNewsCrawler:
    """Google News RSS 한국어 크롤러"""

    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search_news(self, keyword: str, max_articles: int = 5) -> List[NewsArticle]:
        """Google News RSS에서 뉴스 검색"""
        try:
            url = self.GOOGLE_NEWS_RSS.format(query=quote(keyword))
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            articles = []

            for item in root.findall('.//item'):
                if len(articles) >= max_articles:
                    break

                title = item.findtext('title', '')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                source = item.findtext('source', '')
                description = item.findtext('description', '')

                # HTML 태그 제거
                if description:
                    description = re.sub(r'<[^>]+>', '', description).strip()

                articles.append(NewsArticle(
                    title=title,
                    link=link,
                    summary=description or title,
                    source=source,
                    date=pub_date,
                ))

            logger.info(f"Google News: {len(articles)} articles for '{keyword}'")
            return articles

        except Exception as e:
            logger.error(f"Google News RSS error for '{keyword}': {e}")
            return []

    def get_news_summary(self, keyword: str, max_articles: int = 5) -> str:
        """키워드 관련 Google News 요약"""
        articles = self.search_news(keyword, max_articles)
        if not articles:
            return ""

        summaries = []
        for i, article in enumerate(articles, 1):
            s = f"[Google뉴스 {i}] {article.title}"
            if article.summary and article.summary != article.title:
                s += f"\n{article.summary}"
            if article.source:
                s += f"\n출처: {article.source}"
            summaries.append(s)

        return "\n\n".join(summaries)


def extract_key_facts(text: str) -> dict:
    """
    뉴스 본문에서 핵심 팩트 추출 (날짜, 수치, 인물, 기관)
    """
    facts = {
        "dates": [],
        "numbers": [],
        "people": [],
        "organizations": [],
    }

    # 날짜 패턴
    date_patterns = [
        r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',
        r'\d{4}\.\d{1,2}\.\d{1,2}',
        r'\d{1,2}월\s*\d{1,2}일',
    ]
    for p in date_patterns:
        facts["dates"].extend(re.findall(p, text))

    # 수치 패턴 (금액, 퍼센트 등)
    number_patterns = [
        r'\d+(?:,\d{3})*(?:\.\d+)?(?:원|만원|억원|조원)',
        r'\d+(?:\.\d+)?%',
        r'\d+(?:,\d{3})*명',
        r'\d+(?:,\d{3})*건',
    ]
    for p in number_patterns:
        facts["numbers"].extend(re.findall(p, text))

    # 기관 패턴
    org_patterns = [
        r'[가-힣]+(?:부|처|청|원|위원회|은행|공사|공단|협회|연합회)',
        r'[가-힣]+(?:대학교|대학|연구원|연구소)',
    ]
    for p in org_patterns:
        found = re.findall(p, text)
        facts["organizations"].extend([o for o in found if len(o) >= 3])

    # 중복 제거
    for key in facts:
        facts[key] = list(set(facts[key]))[:10]

    return facts


class CombinedNewsCrawler:
    """네이버 + Google News 통합 크롤러"""

    def __init__(self):
        self.naver = NaverNewsCrawler()
        self.google = GoogleNewsCrawler()

    def get_combined_summary(self, keyword: str, max_per_source: int = 3) -> str:
        """두 소스에서 뉴스 수집 후 통합 요약"""
        naver_summary = self.naver.get_news_summary(keyword, max_per_source)
        google_summary = self.google.get_news_summary(keyword, max_per_source)

        parts = []
        if naver_summary:
            parts.append(f"[네이버 뉴스]\n{naver_summary}")
        if google_summary:
            parts.append(f"[Google 뉴스]\n{google_summary}")

        combined = "\n\n".join(parts) if parts else f"'{keyword}'에 대한 최신 뉴스를 찾을 수 없습니다."

        # 핵심 팩트 추출
        facts = extract_key_facts(combined)
        if any(facts.values()):
            fact_lines = []
            if facts["dates"]:
                fact_lines.append(f"주요 날짜: {', '.join(facts['dates'][:5])}")
            if facts["numbers"]:
                fact_lines.append(f"주요 수치: {', '.join(facts['numbers'][:5])}")
            if facts["organizations"]:
                fact_lines.append(f"관련 기관: {', '.join(facts['organizations'][:5])}")
            if fact_lines:
                combined += "\n\n[핵심 팩트 요약]\n" + "\n".join(fact_lines)

        return combined


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    combined = CombinedNewsCrawler()
    summary = combined.get_combined_summary("인공지능")
    print("Combined News Summary:")
    print(summary)
