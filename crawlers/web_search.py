"""
Google Custom Search 웹검색 모듈
키워드 관련 최신 정보를 수집합니다.
"""
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings

logger = logging.getLogger(__name__)


class WebSearcher:
    """Google Custom Search API를 사용한 웹검색"""

    def __init__(self):
        self.api_key = settings.google_api_key
        self.cse_id = settings.google_cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def is_configured(self) -> bool:
        """API 설정 여부 확인"""
        return bool(self.api_key and self.cse_id)

    def search(self, keyword: str, num_results: int = 5) -> List[Dict]:
        """
        키워드로 웹검색 수행

        Args:
            keyword: 검색 키워드
            num_results: 결과 개수 (최대 10)

        Returns:
            검색 결과 리스트
            [{"title": "제목", "snippet": "설명", "link": "URL"}]
        """
        if not self.is_configured():
            logger.warning("Google Search API가 설정되지 않았습니다.")
            return []

        try:
            # 현재 연도 추가하여 최신 정보 검색
            current_year = datetime.now().year
            enhanced_query = f"{keyword} {current_year}"

            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": enhanced_query,
                "num": min(num_results, 10),
                "lr": "lang_ko",  # 한국어 결과 우선
            }

            logger.info(f"웹검색 시작: '{keyword}'")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            results = []
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                })

            logger.info(f"웹검색 완료: {len(results)}개 결과")
            return results

        except requests.RequestException as e:
            logger.error(f"웹검색 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"웹검색 오류: {e}")
            return []

    def get_search_context(self, keyword: str) -> str:
        """
        키워드 관련 컨텍스트 텍스트 생성
        AI 글쓰기에 참고할 수 있는 형태로 가공

        Args:
            keyword: 검색 키워드

        Returns:
            컨텍스트 텍스트
        """
        results = self.search(keyword, num_results=5)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            title = result["title"]
            snippet = result["snippet"]
            context_parts.append(f"[출처 {i}] {title}\n{snippet}")

        context = "\n\n".join(context_parts)
        logger.info(f"검색 컨텍스트 생성 완료: {len(context)}자")

        return context


def search_and_get_context(keyword: str) -> str:
    """
    웹검색 후 컨텍스트 텍스트 반환 (편의 함수)

    Args:
        keyword: 검색 키워드

    Returns:
        컨텍스트 텍스트
    """
    searcher = WebSearcher()
    return searcher.get_search_context(keyword)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 웹검색 테스트 ===\n")

    searcher = WebSearcher()

    if not searcher.is_configured():
        print("❌ Google Search API가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요.")
    else:
        keyword = "연말정산"
        print(f"검색 키워드: {keyword}\n")

        results = searcher.search(keyword)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['snippet'][:100]}...")
            print(f"   {result['link']}")
            print()
