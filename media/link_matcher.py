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
        깔끔한 레퍼런스 스타일 링크 카드 HTML 생성

        Args:
            site: 사이트 정보 딕셔너리

        Returns:
            카드 HTML 문자열
        """
        from urllib.parse import urlparse
        domain = urlparse(site['url']).netloc
        return f'''
<div style="margin: 24px 0; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
  <a href="{site['url']}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; padding: 20px 24px;">
    <table style="width: 100%; border: none; border-collapse: collapse;">
      <tr>
        <td style="width: 56px; vertical-align: middle; padding-right: 16px;">
          <div style="width: 48px; height: 48px; background: #f1f5f9; border-radius: 10px; text-align: center; line-height: 48px;">
            <img src="https://www.google.com/s2/favicons?domain={domain}&sz=32" alt="" style="width: 32px; height: 32px; vertical-align: middle;" onerror="this.style.display=\'none\'" />
          </div>
        </td>
        <td style="vertical-align: middle;">
          <p style="margin: 0 0 4px 0; font-size: 16px; font-weight: 700; color: #1a202c;">{site['name']}</p>
          <p style="margin: 0; font-size: 13px; color: #64748b;">{site.get('description', '')}</p>
          <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">{domain}</p>
        </td>
        <td style="width: 32px; vertical-align: middle; text-align: right; color: #94a3b8; font-size: 20px;">&#8594;</td>
      </tr>
    </table>
  </a>
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
        콘텐츠에 관련 사이트 링크 카드 자동 삽입 (최대 3개)

        Args:
            content: HTML 콘텐츠
            keyword: 키워드

        Returns:
            링크가 삽입된 콘텐츠
        """
        import re

        sites = self.find_matching_sites(keyword)
        if not sites:
            logger.info(f"관련 사이트 없음: {keyword}")
            return content

        # 최대 3개 사이트
        sites = sites[:3]

        # 모든 카드 HTML 합치기
        cards_html = "\n".join(self.generate_link_button_html(site) for site in sites)

        # 삽입 위치 결정: 두 번째 또는 첫 번째 섹션 헤더 뒤
        headers = list(re.finditer(r'</h[23]>', content))

        if len(headers) >= 2:
            insert_pos = headers[1].end()
            content = content[:insert_pos] + cards_html + content[insert_pos:]
            logger.info(f"링크 카드 {len(sites)}개 삽입 완료 (위치: 두 번째 헤더 뒤)")
        elif len(headers) >= 1:
            insert_pos = headers[0].end()
            content = content[:insert_pos] + cards_html + content[insert_pos:]
            logger.info(f"링크 카드 {len(sites)}개 삽입 완료 (위치: 첫 번째 헤더 뒤)")
        else:
            p_match = re.search(r'</p>', content)
            if p_match:
                insert_pos = p_match.end()
                content = content[:insert_pos] + cards_html + content[insert_pos:]
                logger.info(f"링크 카드 {len(sites)}개 삽입 완료 (위치: 첫 번째 문단 뒤)")
            else:
                content = cards_html + content
                logger.info(f"링크 카드 {len(sites)}개 삽입 완료 (위치: 맨 앞)")

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
