"""포스트 703: 중복 링크카드 제거 + 링크 연결 수정"""
import requests, sys, re
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts/703", auth=auth, timeout=10)
content = r.json()["content"]["rendered"]

# 모든 📌 관련 사이트 바로가기 섹션 제거 (중복 포함)
# 다양한 패턴으로 제거
content = re.sub(r'<div[^>]*>\s*<h3[^>]*>📌[^<]*</h3>[\s\S]*?(?:</a>\s*</div>)', '', content, count=0)
# 혹시 남은 h3만 있는 경우
content = re.sub(r'<h3[^>]*>\s*📌[^<]*</h3>', '', content)
# 링크 없는 카드들도 제거 (왼손개발자님이 수정한 a태그 없는 버전)
content = re.sub(r'<div[^>]*>\s*K-Startup \(창업넷\)[\s\S]*?k-startup\.go\.kr →\s*</div>\s*</div>\s*</div>', '', content)

# 빈 태그 정리
content = re.sub(r'<p>\s*</p>', '', content)
content = re.sub(r'<div[^>]*>\s*</div>', '', content)
content = re.sub(r'\n{3,}', '\n\n', content)

# 새 링크카드 HTML (a 태그로 클릭 가능)
link_cards = """
<div style="margin: 0 0 30px 0;">
<h3 style="margin-bottom: 15px;">📌 관련 사이트 바로가기</h3>

<a href="https://www.k-startup.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 12px;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 100%);">
<div style="min-width: 50px; height: 50px; background: #1a73e8; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 24px; font-weight: bold;">K</span>
</div>
<div>
<div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">K-Startup (창업넷)</div>
<div style="font-size: 13px; color: #666; margin-top: 3px;">예비창업패키지 온라인 신청·접수 사이트</div>
<div style="font-size: 12px; color: #1a73e8; margin-top: 3px;">k-startup.go.kr →</div>
</div>
</div>
</a>

<a href="https://www.mss.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 12px;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #f0e8f8 100%);">
<div style="min-width: 50px; height: 50px; background: #6c3483; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 20px; font-weight: bold;">중기</span>
</div>
<div>
<div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">중소벤처기업부</div>
<div style="font-size: 13px; color: #666; margin-top: 3px;">공고문 원본·첨부파일 다운로드</div>
<div style="font-size: 12px; color: #6c3483; margin-top: 3px;">mss.go.kr →</div>
</div>
</div>
</a>

<a href="https://www.bizinfo.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f8e8 100%);">
<div style="min-width: 50px; height: 50px; background: #27ae60; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 18px; font-weight: bold;">기업</span>
</div>
<div>
<div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">기업마당</div>
<div style="font-size: 13px; color: #666; margin-top: 3px;">정부 지원사업 통합 검색·맞춤형 추천</div>
<div style="font-size: 12px; color: #27ae60; margin-top: 3px;">bizinfo.go.kr →</div>
</div>
</div>
</a>
</div>
"""

# 정보카드(📋) 닫는 div 뒤에 삽입
info_match = re.search(r'</table>\s*</div>', content)
if info_match:
    insert_at = info_match.end()
    content = content[:insert_at] + "\n" + link_cards + "\n" + content[insert_at:]
    print("✅ 링크카드 삽입 (정보카드 뒤)")
else:
    # 본문 시작에 삽입
    content = link_cards + content
    print("✅ 링크카드 삽입 (본문 시작)")

resp = requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/703",
                     auth=auth, json={"content": content}, timeout=15)
print(f"Update: {resp.status_code}")
