"""네이버 블로그 참조/벤치마킹 크롤러"""
import logging
import re
from typing import List, Dict
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class BlogReferenceCrawler:
    """네이버 블로그 상위 글 구조를 분석하여 참고 자료 제공"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search_naver_blogs(self, keyword: str, count: int = 3) -> List[str]:
        """
        네이버 블로그 검색 결과에서 상위 블로그 URL 추출

        Args:
            keyword: 검색 키워드
            count: 가져올 블로그 수

        Returns:
            블로그 URL 리스트
        """
        try:
            url = (
                f"https://search.naver.com/search.naver?"
                f"where=blog&query={quote(keyword)}&sm=tab_opt&sort=sim"
            )
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            urls = []
            # 블로그 링크 추출 (다양한 셀렉터 시도)
            for a_tag in soup.select("a.api_txt_lines.total_tit"):
                href = a_tag.get("href", "")
                if href and ("blog.naver.com" in href or "m.blog.naver.com" in href):
                    urls.append(href)
                    if len(urls) >= count:
                        break

            # 폴백 셀렉터
            if not urls:
                for a_tag in soup.select("a[href*='blog.naver.com']"):
                    href = a_tag.get("href", "")
                    if href and href not in urls:
                        urls.append(href)
                        if len(urls) >= count:
                            break

            logger.info(f"Blog search for '{keyword}': {len(urls)} URLs found")
            return urls[:count]

        except Exception as e:
            logger.warning(f"Blog search failed for '{keyword}': {e}")
            return []

    def analyze_blog(self, url: str) -> Dict:
        """
        블로그 글의 구조 분석 (소제목, 길이, 주요 토픽)

        Args:
            url: 블로그 URL

        Returns:
            분석 결과 딕셔너리
        """
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # iframe 내부 콘텐츠 (네이버 블로그 구조)
            iframe = soup.select_one("iframe#mainFrame")
            if iframe:
                iframe_src = iframe.get("src", "")
                if iframe_src:
                    if iframe_src.startswith("/"):
                        iframe_src = "https://blog.naver.com" + iframe_src
                    resp2 = self.session.get(iframe_src, timeout=10)
                    resp2.raise_for_status()
                    soup = BeautifulSoup(resp2.text, "html.parser")

            # 본문 영역 찾기
            content_area = (
                soup.select_one(".se-main-container") or
                soup.select_one("#postViewArea") or
                soup.select_one(".post-view") or
                soup.select_one("div.se_component_wrap")
            )

            if not content_area:
                return {"url": url, "headings": [], "length": 0, "subtopics": []}

            # 소제목 추출
            headings = []
            for tag in content_area.select("h2, h3, strong, .se-text-paragraph-align-center"):
                text = tag.get_text(strip=True)
                if text and 5 <= len(text) <= 80:
                    headings.append(text)

            # 본문 길이
            full_text = content_area.get_text(strip=True)
            length = len(full_text)

            # 핵심 키워드/토픽 추출 (빈도 기반)
            words = re.findall(r'[가-힣]{2,}', full_text)
            word_freq = {}
            for w in words:
                if len(w) >= 2:
                    word_freq[w] = word_freq.get(w, 0) + 1
            subtopics = sorted(word_freq, key=word_freq.get, reverse=True)[:10]

            return {
                "url": url,
                "headings": headings[:10],
                "length": length,
                "subtopics": subtopics,
            }

        except Exception as e:
            logger.warning(f"Blog analysis failed for {url}: {e}")
            return {"url": url, "headings": [], "length": 0, "subtopics": []}

    def get_blog_analysis(self, keyword: str, count: int = 3) -> str:
        """
        키워드에 대한 상위 블로그 구조 분석 요약 문자열 반환

        Args:
            keyword: 검색 키워드
            count: 분석할 블로그 수

        Returns:
            프롬프트에 삽입할 분석 요약 문자열
        """
        urls = self.search_naver_blogs(keyword, count)
        if not urls:
            return ""

        analyses = []
        for url in urls:
            analysis = self.analyze_blog(url)
            if analysis.get("headings") or analysis.get("length", 0) > 0:
                analyses.append(analysis)

        if not analyses:
            return ""

        # 요약 문자열 구성
        lines = []
        for i, a in enumerate(analyses, 1):
            lines.append(f"[블로그 {i}] 길이: 약 {a['length']}자")
            if a["headings"]:
                lines.append(f"  소제목: {' / '.join(a['headings'][:5])}")
            if a["subtopics"]:
                lines.append(f"  핵심 키워드: {', '.join(a['subtopics'][:5])}")

        result = "\n".join(lines)
        logger.info(f"Blog analysis for '{keyword}': {len(analyses)} blogs analyzed")
        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler = BlogReferenceCrawler()
    result = crawler.get_blog_analysis("연말정산")
    print(result)
