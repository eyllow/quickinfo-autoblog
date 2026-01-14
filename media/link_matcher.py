"""
관련 사이트 링크 매칭 모듈
키워드에 맞는 공식 사이트 URL을 찾아 링크 버튼 HTML을 생성합니다.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "site_links.json"


class LinkMatcher:
    """키워드에 맞는 관련 사이트 링크 매칭"""

    def __init__(self):
        self.site_data = self._load_site_data()

    def _load_site_data(self) -> Dict:
        """사이트 링크 데이터 로드"""
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"사이트 링크 설정 파일 없음: {CONFIG_PATH}")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"사이트 링크 JSON 파싱 에러: {e}")
            return {}
        except Exception as e:
            logger.error(f"사이트 링크 로드 에러: {e}")
            return {}

    def find_matching_sites(self, keyword: str, content: str = "") -> List[Dict]:
        """
        키워드와 콘텐츠에서 관련 사이트 찾기

        Args:
            keyword: 검색 키워드
            content: 콘텐츠 본문 (선택)

        Returns:
            매칭된 사이트 정보 리스트
        """
        matches = []
        search_text = f"{keyword} {content}".lower()

        for site_key, site_info in self.site_data.items():
            for kw in site_info.get("keywords", []):
                if kw.lower() in search_text:
                    matches.append({
                        "url": site_info["url"],
                        "name": site_info["name"],
                        "description": site_info.get("description", ""),
                        "matched_keyword": kw
                    })
                    break  # 한 사이트당 하나만

        logger.info(f"링크 매칭 결과: '{keyword}' -> {len(matches)}개 사이트")
        return matches

    def get_primary_site(self, keyword: str) -> Optional[Dict]:
        """
        주요 관련 사이트 1개 반환

        Args:
            keyword: 검색 키워드

        Returns:
            사이트 정보 또는 None
        """
        matches = self.find_matching_sites(keyword)
        if matches:
            logger.info(f"주요 사이트: {matches[0]['name']} ({matches[0]['url']})")
            return matches[0]
        return None

    def generate_link_button_html(self, site: Dict) -> str:
        """
        클릭 유도 버튼 HTML 생성

        Args:
            site: 사이트 정보 딕셔너리

        Returns:
            버튼 HTML 문자열
        """
        return f'''
<div style="text-align: center; margin: 30px 0;">
    <a href="{site['url']}" target="_blank" rel="noopener noreferrer"
       style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; padding: 15px 30px; text-decoration: none;
              border-radius: 8px; font-weight: bold; font-size: 16px;
              box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
        {site['name']} 바로가기
    </a>
    <p style="margin-top: 10px; color: #666; font-size: 14px;">{site.get('description', '')}</p>
</div>
'''

    def generate_link_text(self, site: Dict) -> str:
        """
        텍스트 링크 생성

        Args:
            site: 사이트 정보 딕셔너리

        Returns:
            HTML 링크 문자열
        """
        return f'<a href="{site["url"]}" target="_blank" rel="noopener noreferrer">{site["name"]}</a>'

    def insert_link_into_content(self, content: str, keyword: str) -> str:
        """
        콘텐츠에 관련 사이트 링크 버튼 자동 삽입

        Args:
            content: HTML 콘텐츠
            keyword: 키워드

        Returns:
            링크가 삽입된 콘텐츠
        """
        import re

        site = self.get_primary_site(keyword)
        if not site:
            logger.info(f"관련 사이트 없음: {keyword}")
            return content

        # 버튼 HTML 생성
        button_html = self.generate_link_button_html(site)

        # 삽입 위치 결정: 두 번째 또는 첫 번째 섹션 헤더 뒤
        headers = list(re.finditer(r'</h[23]>', content))

        if len(headers) >= 2:
            # 두 번째 헤더 뒤에 삽입
            insert_pos = headers[1].end()
            content = content[:insert_pos] + button_html + content[insert_pos:]
            logger.info(f"링크 버튼 삽입 완료 (위치: 두 번째 헤더 뒤)")
        elif len(headers) >= 1:
            # 첫 번째 헤더 뒤에 삽입
            insert_pos = headers[0].end()
            content = content[:insert_pos] + button_html + content[insert_pos:]
            logger.info(f"링크 버튼 삽입 완료 (위치: 첫 번째 헤더 뒤)")
        else:
            # 헤더 없으면 첫 번째 </p> 태그 뒤에 삽입
            p_match = re.search(r'</p>', content)
            if p_match:
                insert_pos = p_match.end()
                content = content[:insert_pos] + button_html + content[insert_pos:]
                logger.info(f"링크 버튼 삽입 완료 (위치: 첫 번째 문단 뒤)")
            else:
                # 그래도 없으면 맨 앞에 삽입
                content = button_html + content
                logger.info(f"링크 버튼 삽입 완료 (위치: 맨 앞)")

        return content


# 편의 함수
def get_link_matcher() -> LinkMatcher:
    """LinkMatcher 인스턴스 반환"""
    return LinkMatcher()


def insert_related_links(content: str, keyword: str) -> str:
    """
    콘텐츠에 관련 링크 삽입 편의 함수

    Args:
        content: HTML 콘텐츠
        keyword: 키워드

    Returns:
        링크가 삽입된 콘텐츠
    """
    matcher = LinkMatcher()
    return matcher.insert_link_into_content(content, keyword)


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 링크 매칭 테스트 ===\n")

    matcher = LinkMatcher()

    test_keywords = ["정부24 등본", "연말정산 방법", "청년도약계좌", "비트코인 시세", "실업급여 신청"]

    for kw in test_keywords:
        site = matcher.get_primary_site(kw)
        if site:
            print(f"'{kw}'")
            print(f"  -> {site['name']} ({site['url']})")
            print()
        else:
            print(f"'{kw}' -> 매칭 없음\n")

    # HTML 삽입 테스트
    print("\n=== HTML 삽입 테스트 ===\n")
    test_html = """
<h2>연말정산 준비하기</h2>
<p>연말정산은 매년 1월~2월에 진행됩니다.</p>
<h2>필요 서류</h2>
<p>다음 서류가 필요합니다.</p>
"""
    result = matcher.insert_link_into_content(test_html, "연말정산")
    print(result)
