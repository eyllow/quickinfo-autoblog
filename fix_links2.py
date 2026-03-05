"""포스트 703: 링크카드 완전 교체 — WP 호환 구조"""
import requests, sys, re
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts/703", auth=auth, timeout=10)
content = r.json()["content"]["rendered"]
print(f"원본: {len(content)}자")

# 1. 모든 링크카드/관련사이트 섹션 완전 제거
# 패턴: 📌 관련 사이트 바로가기 ~ 그 섹션 끝
# 정보카드(📋) 이후 ~ 본문 시작(h2) 사이의 모든 것을 교체

# 정보카드 끝 위치
info_end = content.find('</table>')
if info_end > 0:
    info_div_end = content.find('</div>', info_end) + 6
else:
    info_div_end = 0

# 본문 시작 위치 (첫 번째 h2)
body_start = content.find('<h2', info_div_end)
if body_start < 0:
    body_start = content.find('<div style="max-width: 700px', info_div_end)

print(f"정보카드 끝: {info_div_end}, 본문 시작: {body_start}")

# 정보카드와 본문 사이를 깔끔하게 교체
# WP 호환 링크카드 — <a>를 블록으로 쓰되 내부는 <span>으로만 구성
link_cards_wp = """

<!-- wp:html -->
<div style="margin: 25px 0 30px 0;">
<h3 style="margin-bottom: 15px; font-size: 18px;">📌 관련 사이트 바로가기</h3>

<a href="https://www.k-startup.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 12px; border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 100%); color: inherit;">
<table style="border: none; border-collapse: collapse; width: 100%;"><tr>
<td style="width: 50px; vertical-align: middle; border: none; padding: 0;"><span style="display: inline-block; width: 50px; height: 50px; background: #1a73e8; border-radius: 10px; text-align: center; line-height: 50px; color: white; font-size: 24px; font-weight: bold;">K</span></td>
<td style="padding-left: 15px; border: none; vertical-align: middle;"><span style="font-size: 16px; font-weight: bold; color: #1a1a1a; display: block;">K-Startup (창업넷)</span><span style="font-size: 13px; color: #666; display: block; margin-top: 3px;">예비창업패키지 온라인 신청·접수 사이트</span><span style="font-size: 12px; color: #1a73e8; display: block; margin-top: 3px;">k-startup.go.kr →</span></td>
</tr></table>
</a>

<a href="https://www.mss.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 12px; border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; background: linear-gradient(135deg, #f8f9fa 0%, #f0e8f8 100%); color: inherit;">
<table style="border: none; border-collapse: collapse; width: 100%;"><tr>
<td style="width: 50px; vertical-align: middle; border: none; padding: 0;"><span style="display: inline-block; width: 50px; height: 50px; background: #6c3483; border-radius: 10px; text-align: center; line-height: 50px; color: white; font-size: 20px; font-weight: bold;">중기</span></td>
<td style="padding-left: 15px; border: none; vertical-align: middle;"><span style="font-size: 16px; font-weight: bold; color: #1a1a1a; display: block;">중소벤처기업부</span><span style="font-size: 13px; color: #666; display: block; margin-top: 3px;">공고문 원본·첨부파일 다운로드</span><span style="font-size: 12px; color: #6c3483; display: block; margin-top: 3px;">mss.go.kr →</span></td>
</tr></table>
</a>

<a href="https://www.bizinfo.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f8e8 100%); color: inherit;">
<table style="border: none; border-collapse: collapse; width: 100%;"><tr>
<td style="width: 50px; vertical-align: middle; border: none; padding: 0;"><span style="display: inline-block; width: 50px; height: 50px; background: #27ae60; border-radius: 10px; text-align: center; line-height: 50px; color: white; font-size: 18px; font-weight: bold;">기업</span></td>
<td style="padding-left: 15px; border: none; vertical-align: middle;"><span style="font-size: 16px; font-weight: bold; color: #1a1a1a; display: block;">기업마당</span><span style="font-size: 13px; color: #666; display: block; margin-top: 3px;">정부 지원사업 통합 검색·맞춤형 추천</span><span style="font-size: 12px; color: #27ae60; display: block; margin-top: 3px;">bizinfo.go.kr →</span></td>
</tr></table>
</a>

</div>
<!-- /wp:html -->

"""

if info_div_end > 0 and body_start > info_div_end:
    # 정보카드~본문 사이를 통째로 교체
    new_content = content[:info_div_end] + link_cards_wp + content[body_start:]
else:
    # 정보카드 못 찾으면 본문 앞에 삽입
    new_content = link_cards_wp + content

# 최종 정리
new_content = re.sub(r'<p>\s*</p>', '', new_content)
new_content = re.sub(r'<p>\s*&nbsp;\s*</p>', '', new_content)

print(f"결과: {len(new_content)}자")

resp = requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/703",
                     auth=auth, json={"content": new_content}, timeout=15)
print(f"✅ Update: {resp.status_code}")
