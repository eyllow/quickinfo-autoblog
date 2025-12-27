"""
WordPress 필수 페이지 자동 생성 스크립트
About, Contact, Privacy Policy 페이지를 REST API로 생성합니다.
"""
import requests
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


class WordPressPageCreator:
    def __init__(self):
        self.base_url = f"{settings.wp_url}/wp-json/wp/v2"
        credentials = f"{settings.wp_user}:{settings.wp_app_password}"
        self.token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {self.token}',
            'Content-Type': 'application/json'
        }

    def page_exists(self, slug: str) -> bool:
        """페이지 존재 여부 확인"""
        response = requests.get(
            f"{self.base_url}/pages",
            headers=self.headers,
            params={'slug': slug}
        )
        if response.status_code == 200:
            pages = response.json()
            return len(pages) > 0
        return False

    def create_page(self, title: str, content: str, slug: str) -> dict:
        """페이지 생성"""
        # 이미 존재하면 건너뛰기
        if self.page_exists(slug):
            print(f"⏭️  페이지 이미 존재: {title} (/{slug}/)")
            return None

        data = {
            'title': title,
            'content': content,
            'slug': slug,
            'status': 'publish'
        }

        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=data
        )

        if response.status_code == 201:
            result = response.json()
            print(f"✅ 페이지 생성 성공: {title}")
            print(f"   URL: {result.get('link', '')}")
            return result
        else:
            print(f"❌ 페이지 생성 실패: {title}")
            print(f"   오류: {response.text}")
            return None

    def create_required_pages(self):
        """필수 페이지 일괄 생성"""
        print("\n" + "=" * 50)
        print("📄 WordPress 필수 페이지 생성")
        print("=" * 50 + "\n")

        pages = [
            {
                'title': '소개',
                'slug': 'about',
                'content': '''
<!-- wp:heading -->
<h2>QuickInfo 소개</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>QuickInfo는 빠르고 정확한 정보를 제공하는 블로그입니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>우리의 목표</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>최신 트렌드와 유용한 정보를 신속하게 전달</li>
<li>재테크, 생활정보, IT 등 다양한 분야의 실용적인 콘텐츠 제공</li>
<li>독자들의 일상에 도움이 되는 가치 있는 정보 공유</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>다루는 주제</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>재테크</strong>: 연말정산, 청년도약계좌, 국민연금 등</li>
<li><strong>생활정보</strong>: 건강보험, 자동차보험, 실업급여 등</li>
<li><strong>트렌드</strong>: 최신 이슈, 엔터테인먼트, 스포츠 등</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>QuickInfo와 함께 더 스마트한 일상을 만들어보세요!</p>
<!-- /wp:paragraph -->
'''
            },
            {
                'title': '문의하기',
                'slug': 'contact',
                'content': '''
<!-- wp:heading -->
<h2>문의하기</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>QuickInfo에 대한 문의사항이 있으시면 아래 이메일로 연락해주세요.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>이메일</strong>: contact@quickinfo.kr</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>광고 및 제휴 문의도 환영합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>빠른 시일 내에 답변 드리겠습니다. 감사합니다.</p>
<!-- /wp:paragraph -->
'''
            },
            {
                'title': '개인정보처리방침',
                'slug': 'privacy-policy',
                'content': '''
<!-- wp:heading -->
<h2>개인정보처리방침</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>QuickInfo(이하 "사이트")는 이용자의 개인정보를 중요시하며, 개인정보보호법 등 관련 법령을 준수합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>1. 수집하는 개인정보 항목</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>사이트는 서비스 제공을 위해 최소한의 개인정보만을 수집합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>웹사이트 방문 시: IP 주소, 쿠키, 방문 기록</li>
<li>문의 시: 이메일 주소</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>2. 개인정보의 수집 및 이용목적</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>서비스 제공 및 운영</li>
<li>이용자 문의 응대</li>
<li>사이트 이용 통계 분석</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>3. 개인정보의 보유 및 이용기간</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>수집된 개인정보는 수집 목적이 달성되면 즉시 파기합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>4. 쿠키(Cookie) 사용</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>사이트는 이용자에게 적합한 서비스를 제공하기 위해 쿠키를 사용합니다. 이용자는 브라우저 설정을 통해 쿠키를 거부할 수 있습니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>5. 광고</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>사이트는 Google AdSense를 통해 광고를 게재합니다. Google은 쿠키를 사용하여 이용자에게 적합한 광고를 표시합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>6. 문의</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>개인정보 관련 문의: contact@quickinfo.kr</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><em>시행일: 2025년 1월 1일</em></p>
<!-- /wp:paragraph -->
'''
            }
        ]

        success_count = 0
        for page in pages:
            result = self.create_page(page['title'], page['content'], page['slug'])
            if result:
                success_count += 1

        print("\n" + "=" * 50)
        print(f"📊 결과: {success_count}/{len(pages)} 페이지 생성 완료")
        print("=" * 50 + "\n")

        return success_count


if __name__ == "__main__":
    creator = WordPressPageCreator()
    creator.create_required_pages()
