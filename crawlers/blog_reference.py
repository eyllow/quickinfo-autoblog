"""네이버 블로그 + 구글 검색 참조/벤치마킹 크롤러 (강화 버전)

상위 5개 고품질 블로그를 정밀 분석하여 AI 콘텐츠 생성의 참고 자료 제공:
- 네이버 + 구글 검색 결과 통합
- 블로그 품질 평가 (댓글 수, 공감 수, 글 길이)
- 본문 전체 텍스트 추출 및 AI 요약
- 공통 구조 패턴 분석 (도입-본론-결론)
- 핵심 문장/논점/수치/비교 데이터 추출
- 글 톤 분석 (설명형/리스트형/비교형/스토리텔링)
"""
import logging
import re
from typing import List, Dict, Optional
from urllib.parse import quote, urlparse
from dataclasses import dataclass, field
import json

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import anthropic
    from config.settings import settings
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://www.naver.com/",
    "Connection": "keep-alive",
}


@dataclass
class BlogAnalysis:
    """블로그 분석 결과"""
    url: str
    title: str = ""
    headings: List[str] = field(default_factory=list)
    length: int = 0
    subtopics: List[str] = field(default_factory=list)
    full_text: str = ""
    quality_score: float = 0.0
    likes: int = 0
    comments: int = 0
    tone: str = ""  # 설명형, 리스트형, 비교형, 스토리텔링
    key_sentences: List[str] = field(default_factory=list)
    numbers_data: List[str] = field(default_factory=list)  # 수치/데이터
    structure_pattern: str = ""  # 도입-본론-결론 등


class BlogReferenceCrawler:
    """네이버 블로그 + 구글 검색 고품질 블로그 분석기 (강화 버전)"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # Claude 클라이언트 초기화
        if HAS_CLAUDE:
            try:
                self.claude_client = anthropic.Anthropic(api_key=settings.claude_api_key)
            except Exception as e:
                logger.warning(f"Claude client initialization failed: {e}")
                self.claude_client = None
        else:
            self.claude_client = None

    def search_naver_blogs(self, keyword: str, count: int = 5) -> List[str]:
        """
        네이버 블로그 검색 결과에서 상위 블로그 URL 추출

        Args:
            keyword: 검색 키워드
            count: 가져올 블로그 수 (기본 5개로 증가)

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

            logger.info(f"Naver blog search for '{keyword}': {len(urls)} URLs found")
            return urls[:count]

        except Exception as e:
            logger.warning(f"Naver blog search failed for '{keyword}': {e}")
            return []

    def search_google_blogs(self, keyword: str, count: int = 5) -> List[str]:
        """
        구글 검색에서 블로그 URL 추출

        Args:
            keyword: 검색 키워드
            count: 가져올 블로그 수

        Returns:
            블로그 URL 리스트
        """
        try:
            # 구글 검색 (블로그 필터링)
            search_query = f"{keyword} 블로그 site:blog.naver.com OR site:tistory.com OR site:brunch.co.kr"
            url = f"https://www.google.com/search?q={quote(search_query)}&num={count + 5}&hl=ko"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html",
                "Accept-Language": "ko-KR,ko;q=0.9",
            }

            resp = self.session.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            urls = []
            for a_tag in soup.select("a[href*='blog.naver.com'], a[href*='tistory.com'], a[href*='brunch.co.kr']"):
                href = a_tag.get("href", "")
                # 구글 리다이렉트 URL 처리
                if "/url?q=" in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if "q" in parsed:
                        href = parsed["q"][0]

                if href and href.startswith("http") and href not in urls:
                    urls.append(href)
                    if len(urls) >= count:
                        break

            logger.info(f"Google blog search for '{keyword}': {len(urls)} URLs found")
            return urls[:count]

        except Exception as e:
            logger.warning(f"Google blog search failed for '{keyword}': {e}")
            return []

    def analyze_blog(self, url: str) -> BlogAnalysis:
        """
        블로그 글의 심층 구조 분석

        Args:
            url: 블로그 URL

        Returns:
            BlogAnalysis 객체
        """
        analysis = BlogAnalysis(url=url)

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # iframe 내부 콘텐츠 (네이버 블로그 구조)
            iframe = soup.select_one("iframe#mainFrame")
            if iframe:
                iframe_src = iframe.get("src", "")
                if iframe_src:
                    if iframe_src.startswith("/"):
                        iframe_src = "https://blog.naver.com" + iframe_src
                    resp2 = self.session.get(iframe_src, timeout=15)
                    resp2.raise_for_status()
                    soup = BeautifulSoup(resp2.text, "html.parser")

            # 제목 추출
            title_tag = (
                soup.select_one(".se-title-text") or
                soup.select_one(".pcol1") or
                soup.select_one("h3.tit_h3") or
                soup.select_one("title")
            )
            if title_tag:
                analysis.title = title_tag.get_text(strip=True)[:100]

            # 본문 영역 찾기
            content_area = (
                soup.select_one(".se-main-container") or
                soup.select_one("#postViewArea") or
                soup.select_one(".post-view") or
                soup.select_one("div.se_component_wrap") or
                soup.select_one(".article_view") or  # 티스토리
                soup.select_one(".wrap_body")  # 브런치
            )

            if not content_area:
                return analysis

            # 소제목 추출
            headings = []
            for tag in content_area.select("h2, h3, h4, strong, .se-text-paragraph-align-center"):
                text = tag.get_text(strip=True)
                if text and 5 <= len(text) <= 80:
                    # 중복 제거
                    if text not in headings:
                        headings.append(text)
            analysis.headings = headings[:15]

            # 본문 전체 텍스트
            full_text = content_area.get_text(separator="\n", strip=True)
            analysis.full_text = full_text[:10000]  # 최대 10000자
            analysis.length = len(full_text)

            # 핵심 키워드/토픽 추출 (빈도 기반)
            words = re.findall(r'[가-힣]{2,}', full_text)
            word_freq = {}
            for w in words:
                if len(w) >= 2:
                    word_freq[w] = word_freq.get(w, 0) + 1
            analysis.subtopics = sorted(word_freq, key=word_freq.get, reverse=True)[:15]

            # 수치/데이터 추출 (금액, 퍼센트, 날짜 등)
            numbers = re.findall(
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:원|만원|억원|%|퍼센트|개월|년|일|명|건|회))',
                full_text
            )
            analysis.numbers_data = list(set(numbers))[:10]

            # 핵심 문장 추출 (결론/핵심 포인트)
            key_patterns = [
                r'결론[은적]?\s*[:：]?\s*(.{20,100})',
                r'핵심[은적]?\s*[:：]?\s*(.{20,100})',
                r'중요한\s*것은\s*(.{20,100})',
                r'정리하[면자]\s*(.{20,100})',
                r'요약하[면자]\s*(.{20,100})',
                r'TIP[:：]?\s*(.{20,100})',
                r'꿀팁[:：]?\s*(.{20,100})',
            ]
            key_sentences = []
            for pattern in key_patterns:
                matches = re.findall(pattern, full_text)
                key_sentences.extend(matches)
            analysis.key_sentences = list(set(key_sentences))[:5]

            # 글 톤 분석
            analysis.tone = self._analyze_tone(full_text, headings)

            # 구조 패턴 분석
            analysis.structure_pattern = self._analyze_structure(headings, full_text)

            # 품질 점수 계산 (공감/댓글 추출 시도)
            try:
                likes = soup.select_one(".u_likeit_list_count, .sympathy_cnt, .like_cnt")
                if likes:
                    analysis.likes = int(re.sub(r'\D', '', likes.get_text()) or 0)

                comments = soup.select_one(".comment_count, .cmt_cnt, .commentCount")
                if comments:
                    analysis.comments = int(re.sub(r'\D', '', comments.get_text()) or 0)
            except Exception:
                pass

            # 품질 점수 계산
            analysis.quality_score = self._calculate_quality_score(analysis)

            return analysis

        except Exception as e:
            logger.warning(f"Blog analysis failed for {url}: {e}")
            return analysis

    def _analyze_tone(self, full_text: str, headings: List[str]) -> str:
        """글 톤 분석"""
        # 리스트형 지표
        list_markers = len(re.findall(r'^\s*[-•▶▷◆◇★☆✓✔]\s*', full_text, re.MULTILINE))
        numbered_markers = len(re.findall(r'^\s*\d+[.)\]]\s*', full_text, re.MULTILINE))

        # 비교형 지표
        comparison_words = len(re.findall(r'비교|차이|vs|VS|장단점|장점|단점|뭐가 더|어떤 것이', full_text))

        # 스토리텔링 지표
        story_words = len(re.findall(r'저는|제가|나는|내가|했어요|했습니다|경험|후기', full_text))

        # 설명형 지표 (기본)
        explanation_words = len(re.findall(r'입니다|있습니다|됩니다|것입니다|방법|알아보', full_text))

        # 가장 높은 지표 선택
        scores = {
            "리스트형": list_markers + numbered_markers,
            "비교형": comparison_words * 3,
            "스토리텔링": story_words,
            "설명형": explanation_words // 5,
        }

        return max(scores, key=scores.get)

    def _analyze_structure(self, headings: List[str], full_text: str) -> str:
        """구조 패턴 분석"""
        if not headings:
            return "단순형"

        num_headings = len(headings)

        # 도입-본론-결론 패턴 체크
        has_intro = any(h for h in headings[:2] if re.search(r'소개|개요|시작|먼저', h))
        has_conclusion = any(h for h in headings[-2:] if re.search(r'마무리|결론|정리|총정리|요약', h))

        if has_intro and has_conclusion and num_headings >= 5:
            return f"도입-본론({num_headings-2}개)-결론"
        elif num_headings >= 5:
            return f"상세형({num_headings}개 섹션)"
        elif num_headings >= 3:
            return f"표준형({num_headings}개 섹션)"
        else:
            return f"간결형({num_headings}개 섹션)"

    def _calculate_quality_score(self, analysis: BlogAnalysis) -> float:
        """품질 점수 계산 (0-100)"""
        score = 0.0

        # 글 길이 (최대 30점)
        if analysis.length >= 3000:
            score += min(30, analysis.length / 200)

        # 소제목 수 (최대 20점)
        score += min(20, len(analysis.headings) * 3)

        # 핵심 키워드 다양성 (최대 15점)
        score += min(15, len(analysis.subtopics))

        # 수치 데이터 포함 (최대 15점)
        score += min(15, len(analysis.numbers_data) * 3)

        # 공감/댓글 (최대 20점)
        score += min(10, analysis.likes // 5)
        score += min(10, analysis.comments * 2)

        return min(100, score)

    def summarize_with_ai(self, text: str, keyword: str) -> str:
        """
        AI를 사용하여 블로그 본문 요약

        Args:
            text: 블로그 본문
            keyword: 키워드

        Returns:
            AI 요약 결과
        """
        if not self.claude_client or not text:
            return ""

        try:
            prompt = f"""다음은 '{keyword}'에 대한 블로그 글입니다. 핵심 내용을 200자 이내로 요약해주세요.

요약 시 포함할 내용:
1. 주요 논점/핵심 정보
2. 중요한 수치/데이터
3. 실용적인 팁/조언

블로그 본문:
{text[:3000]}

200자 이내 요약:"""

            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"AI summarization failed: {e}")
            return ""

    def get_blog_analysis(self, keyword: str, count: int = 5) -> str:
        """
        키워드에 대한 상위 블로그 심층 분석 요약 문자열 반환 (강화 버전)

        Args:
            keyword: 검색 키워드
            count: 분석할 블로그 수 (기본 5개로 증가)

        Returns:
            프롬프트에 삽입할 상세 분석 요약 문자열
        """
        # 네이버 + 구글 블로그 URL 수집 (중복 제거)
        naver_urls = self.search_naver_blogs(keyword, count)
        google_urls = self.search_google_blogs(keyword, count)

        all_urls = []
        seen = set()
        for url in naver_urls + google_urls:
            # URL 정규화 (m.blog -> blog)
            normalized = url.replace("m.blog.naver.com", "blog.naver.com")
            if normalized not in seen:
                seen.add(normalized)
                all_urls.append(url)

        all_urls = all_urls[:count]

        if not all_urls:
            return ""

        # 블로그 분석
        analyses: List[BlogAnalysis] = []
        for url in all_urls:
            analysis = self.analyze_blog(url)
            if analysis.headings or analysis.length > 500:
                analyses.append(analysis)

        if not analyses:
            return ""

        # 품질 점수 기준 정렬
        analyses.sort(key=lambda x: x.quality_score, reverse=True)
        analyses = analyses[:count]

        # 공통 패턴 분석
        common_analysis = self._analyze_common_patterns(analyses)

        # 요약 문자열 구성 (강화 버전)
        lines = []
        lines.append(f"=== 상위 {len(analyses)}개 블로그 심층 분석 ===\n")

        # 공통 패턴 정보
        if common_analysis:
            lines.append("[공통 패턴]")
            lines.append(f"  - 평균 글 길이: 약 {common_analysis['avg_length']}자")
            lines.append(f"  - 평균 소제목 수: {common_analysis['avg_headings']}개")
            lines.append(f"  - 주요 톤: {common_analysis['dominant_tone']}")
            lines.append(f"  - 공통 키워드: {', '.join(common_analysis['common_keywords'][:10])}")
            lines.append("")

        # 개별 블로그 분석
        for i, a in enumerate(analyses, 1):
            lines.append(f"[블로그 {i}] 품질점수: {a.quality_score:.0f}/100, 길이: 약 {a.length}자")
            lines.append(f"  제목: {a.title[:50]}..." if len(a.title) > 50 else f"  제목: {a.title}")

            if a.headings:
                lines.append(f"  소제목 흐름: {' → '.join(a.headings[:7])}")

            if a.subtopics:
                lines.append(f"  핵심 키워드: {', '.join(a.subtopics[:8])}")

            if a.numbers_data:
                lines.append(f"  포함 수치: {', '.join(a.numbers_data[:5])}")

            if a.tone:
                lines.append(f"  글 스타일: {a.tone} ({a.structure_pattern})")

            # AI 요약 (상위 2개만)
            if i <= 2 and a.full_text and self.claude_client:
                summary = self.summarize_with_ai(a.full_text, keyword)
                if summary:
                    lines.append(f"  핵심 요약: {summary}")

            lines.append("")

        result = "\n".join(lines)
        logger.info(f"Enhanced blog analysis for '{keyword}': {len(analyses)} blogs analyzed")
        return result

    def _analyze_common_patterns(self, analyses: List[BlogAnalysis]) -> Dict:
        """분석 결과에서 공통 패턴 추출"""
        if not analyses:
            return {}

        # 평균 계산
        avg_length = sum(a.length for a in analyses) // len(analyses)
        avg_headings = sum(len(a.headings) for a in analyses) // len(analyses)

        # 톤 빈도
        tone_freq = {}
        for a in analyses:
            if a.tone:
                tone_freq[a.tone] = tone_freq.get(a.tone, 0) + 1
        dominant_tone = max(tone_freq, key=tone_freq.get) if tone_freq else "설명형"

        # 공통 키워드 (2개 이상 블로그에서 등장)
        keyword_freq = {}
        for a in analyses:
            for kw in a.subtopics:
                keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        common_keywords = [kw for kw, freq in sorted(keyword_freq.items(), key=lambda x: -x[1]) if freq >= 2]

        return {
            "avg_length": avg_length,
            "avg_headings": avg_headings,
            "dominant_tone": dominant_tone,
            "common_keywords": common_keywords,
        }

    def get_detailed_analysis(self, keyword: str, count: int = 5) -> Dict:
        """
        상세 분석 결과를 딕셔너리로 반환 (프로그래매틱 사용용)

        Args:
            keyword: 검색 키워드
            count: 분석할 블로그 수

        Returns:
            분석 결과 딕셔너리
        """
        # 네이버 + 구글 블로그 URL 수집
        naver_urls = self.search_naver_blogs(keyword, count)
        google_urls = self.search_google_blogs(keyword, count)

        all_urls = list(set(naver_urls + google_urls))[:count]

        if not all_urls:
            return {"keyword": keyword, "blogs": [], "common_patterns": {}}

        # 블로그 분석
        analyses = []
        for url in all_urls:
            analysis = self.analyze_blog(url)
            if analysis.headings or analysis.length > 500:
                analyses.append(analysis)

        # 품질 점수 기준 정렬
        analyses.sort(key=lambda x: x.quality_score, reverse=True)

        # 결과 구성
        blogs_data = []
        for a in analyses:
            blogs_data.append({
                "url": a.url,
                "title": a.title,
                "headings": a.headings,
                "length": a.length,
                "subtopics": a.subtopics,
                "numbers_data": a.numbers_data,
                "tone": a.tone,
                "structure_pattern": a.structure_pattern,
                "quality_score": a.quality_score,
                "likes": a.likes,
                "comments": a.comments,
            })

        return {
            "keyword": keyword,
            "blogs": blogs_data,
            "common_patterns": self._analyze_common_patterns(analyses),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler = BlogReferenceCrawler()

    # 테스트
    print("=== 강화된 블로그 분석 테스트 ===\n")
    result = crawler.get_blog_analysis("연말정산", count=5)
    print(result)

    print("\n=== 상세 분석 (딕셔너리) ===\n")
    detailed = crawler.get_detailed_analysis("연말정산", count=3)
    print(json.dumps(detailed, ensure_ascii=False, indent=2))
