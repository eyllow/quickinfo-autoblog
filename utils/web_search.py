"""Google Custom Search API를 사용한 웹검색 모듈"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleSearcher:
    """Google Custom Search API를 사용한 웹검색 클래스"""

    def __init__(self):
        self.api_key = settings.google_search_api_key
        self.search_engine_id = settings.google_search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def is_configured(self) -> bool:
        """API가 설정되었는지 확인"""
        return bool(self.api_key and self.search_engine_id)

    def search(self, keyword: str, num_results: int = 5) -> List[Dict]:
        """
        구글 검색 실행

        Args:
            keyword: 검색 키워드
            num_results: 결과 개수 (최대 10)

        Returns:
            검색 결과 리스트
        """
        if not self.is_configured():
            logger.warning("Google Search API not configured")
            return []

        # 현재 연도를 쿼리에 추가하여 최신 정보 검색
        current_year = datetime.now().year
        enhanced_query = f"{keyword} {current_year}"
        logger.info(f"Enhanced search query: '{enhanced_query}'")

        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": enhanced_query,
            "num": min(num_results, 10),
            "lr": "lang_ko",  # 한국어 결과 우선
            "dateRestrict": "m1",  # 최근 1개월 (더 최신 콘텐츠)
            "sort": "date",  # 최신순 정렬
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })

            logger.info(f"Google search completed: '{keyword}' -> {len(results)} results")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Google search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def crawl_article(self, url: str, max_chars: int = 2000) -> str:
        """
        URL에서 본문 텍스트 추출

        Args:
            url: 크롤링할 URL
            max_chars: 최대 문자 수

        Returns:
            추출된 본문 텍스트
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # 불필요한 태그 제거
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                tag.decompose()

            # 본문 추출 시도 (일반적인 패턴들)
            content = ""

            # 뉴스 사이트 본문 선택자
            selectors = [
                "article",
                "#article-body",
                "#dic_area",  # 네이버 뉴스
                ".article_body",
                ".news_body",
                ".post-content",
                ".entry-content",
                "#articleBodyContents",  # 네이버 뉴스 구버전
                ".article-body",
                ".content-body",
                "main",
                "#content",
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=" ", strip=True)
                    if len(content) > 100:  # 충분한 내용이 있으면 사용
                        break

            # 선택자로 못 찾으면 body 전체
            if not content or len(content) < 100:
                if soup.body:
                    content = soup.body.get_text(separator=" ", strip=True)

            # 길이 제한 및 정리
            content = " ".join(content.split())  # 공백 정리
            content = content[:max_chars]

            return content

        except requests.exceptions.RequestException as e:
            logger.warning(f"Crawling failed ({url}): {e}")
            return ""
        except Exception as e:
            logger.warning(f"Error crawling ({url}): {e}")
            return ""

    def filter_old_content(self, content: str) -> str:
        """
        오래된 연도 정보를 필터링

        Args:
            content: 원본 콘텐츠

        Returns:
            필터링된 콘텐츠
        """
        current_year = datetime.now().year
        cutoff_year = current_year - 2  # 2년 전까지만 허용

        # 오래된 연도가 포함된 문장 제거 패턴
        old_year_patterns = []
        for old_year in range(2015, cutoff_year):
            # "2020년", "2021년" 등의 패턴
            old_year_patterns.append(rf'{old_year}년')
            old_year_patterns.append(rf'{old_year}\s*년')

        # 오래된 연도가 포함된 문장 제거
        lines = content.split('\n')
        filtered_lines = []

        for line in lines:
            has_old_year = False
            for pattern in old_year_patterns:
                if re.search(pattern, line):
                    has_old_year = True
                    break

            if not has_old_year:
                filtered_lines.append(line)
            else:
                logger.debug(f"Filtered old content: {line[:50]}...")

        filtered_content = '\n'.join(filtered_lines)

        # 필터링 통계 로깅
        if len(filtered_lines) < len(lines):
            removed = len(lines) - len(filtered_lines)
            logger.info(f"Filtered {removed} lines with old year references")

        return filtered_content

    def search_and_crawl(self, keyword: str, num_results: int = 5) -> Dict:
        """
        검색 + 크롤링 통합 함수

        Args:
            keyword: 검색 키워드
            num_results: 검색 결과 개수

        Returns:
            {
                "keyword": str,
                "sources": List[Dict],  # 출처 목록
                "content": str  # 통합된 콘텐츠
            }
        """
        logger.info(f"Starting web search for: {keyword}")

        # 1. 검색
        search_results = self.search(keyword, num_results)

        if not search_results:
            logger.warning(f"No search results for: {keyword}")
            return {"keyword": keyword, "sources": [], "content": ""}

        # 2. 각 URL 크롤링
        sources = []
        all_content = []

        for result in search_results:
            url = result["url"]
            title = result["title"]
            snippet = result["snippet"]

            # 크롤링
            body = self.crawl_article(url)

            if body and len(body) > 100:
                sources.append({
                    "title": title,
                    "url": url,
                })
                all_content.append(f"[출처: {title}]\n{body}")
                logger.info(f"  Crawled: {title[:40]}...")
            else:
                # 크롤링 실패 시 snippet 사용
                if snippet:
                    all_content.append(f"[출처: {title}]\n{snippet}")
                    sources.append({
                        "title": title,
                        "url": url,
                    })

        combined_content = "\n\n---\n\n".join(all_content)

        # 오래된 콘텐츠 필터링
        filtered_content = self.filter_old_content(combined_content)

        logger.info(f"Web search completed: {len(sources)} sources, {len(filtered_content)} chars (filtered)")

        return {
            "keyword": keyword,
            "sources": sources,
            "content": filtered_content
        }


# 모듈 레벨 함수
def search_web(keyword: str, num_results: int = 5) -> Dict:
    """
    웹검색 실행 (편의 함수)

    Args:
        keyword: 검색 키워드
        num_results: 결과 개수

    Returns:
        검색 결과
    """
    searcher = GoogleSearcher()
    return searcher.search_and_crawl(keyword, num_results)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    searcher = GoogleSearcher()

    if not searcher.is_configured():
        print("Google Search API not configured. Check .env file.")
    else:
        # 테스트 검색
        result = searcher.search_and_crawl("비트코인 전망", num_results=3)

        print(f"\n=== 검색 결과 ===")
        print(f"키워드: {result['keyword']}")
        print(f"출처 수: {len(result['sources'])}")

        for src in result['sources']:
            print(f"  - {src['title']}")
            print(f"    {src['url']}")

        print(f"\n콘텐츠 미리보기 (처음 500자):")
        print(result['content'][:500])
