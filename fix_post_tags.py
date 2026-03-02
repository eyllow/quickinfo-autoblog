import requests, sys, re
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)

# 1. 최신 포스트 가져오기
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts?per_page=1&orderby=date&order=desc", auth=auth, timeout=10)
post = r.json()[0]
post_id = post["id"]
content = post["content"]["rendered"]
print(f"Post ID: {post_id}")
print(f"Title: {post['title']['rendered'][:50]}")

# 2. 문제 태그 제거
cleaned = content
cleaned = re.sub(r'\[OFFICIAL_LINK\]', '', cleaned)
cleaned = re.sub(r'\[COUPANG\]', '', cleaned)
cleaned = re.sub(r'\[AFFILIATE_NOTICE\]', '', cleaned)
cleaned = re.sub(r'\[META\].*?\[/META\]', '', cleaned, flags=re.DOTALL)
cleaned = re.sub(r'<p>\s*</p>', '', cleaned)

# 3. 핵심 정보 요약 카드
info_card = """
<div style="border: 2px solid #4a90d9; border-radius: 12px; padding: 25px; margin: 25px 0; background: linear-gradient(135deg, #eef5ff 0%, #f0f7ff 100%);">
<h3 style="margin: 0 0 15px 0; color: #2c5282;">📋 2026 예비창업패키지 핵심 요약</h3>
<table style="width: 100%; border-collapse: collapse; font-size: 15px;">
<tr style="border-bottom: 1px solid #c3d9f0;">
<td style="padding: 10px; font-weight: bold; color: #2c5282; width: 30%;">📅 신청 기간</td>
<td style="padding: 10px;">2026.03.06(금) ~ 03.24(화) 16:00</td>
</tr>
<tr style="border-bottom: 1px solid #c3d9f0;">
<td style="padding: 10px; font-weight: bold; color: #2c5282;">💰 지원 금액</td>
<td style="padding: 10px;">평균 <strong>4,000만원</strong> (1단계 2,000만원 + 2단계 추가)</td>
</tr>
<tr style="border-bottom: 1px solid #c3d9f0;">
<td style="padding: 10px; font-weight: bold; color: #2c5282;">👤 신청 대상</td>
<td style="padding: 10px;">사업자등록증 미보유 예비창업자 (기준일 '26.1.22.)</td>
</tr>
<tr style="border-bottom: 1px solid #c3d9f0;">
<td style="padding: 10px; font-weight: bold; color: #2c5282;">📝 선정 절차</td>
<td style="padding: 10px;">서류평가 → 인큐베이팅 → 발표평가 (30분)</td>
</tr>
<tr>
<td style="padding: 10px; font-weight: bold; color: #2c5282;">🌐 신청 방법</td>
<td style="padding: 10px;"><a href="https://www.k-startup.go.kr" target="_blank" style="color: #1a73e8;">K-Startup</a> 온라인 접수 | ☎ 1357</td>
</tr>
</table>
</div>
"""

# 4. 관련 사이트 링크 카드
link_cards = """
<div style="margin: 30px 0;">
<h3 style="margin-bottom: 15px;">📌 관련 사이트 바로가기</h3>

<a href="https://www.k-startup.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 15px;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 100%);">
<div style="min-width: 60px; height: 60px; background: #1a73e8; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 28px; font-weight: bold;">K</span>
</div>
<div>
<div style="font-size: 18px; font-weight: bold; color: #1a1a1a;">K-Startup (창업넷)</div>
<div style="font-size: 14px; color: #666; margin-top: 4px;">예비창업패키지 온라인 신청·접수 사이트</div>
<div style="font-size: 13px; color: #1a73e8; margin-top: 4px;">k-startup.go.kr →</div>
</div>
</div>
</a>

<a href="https://www.mss.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 15px;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #f0e8f8 100%);">
<div style="min-width: 60px; height: 60px; background: #6c3483; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 24px; font-weight: bold;">중기</span>
</div>
<div>
<div style="font-size: 18px; font-weight: bold; color: #1a1a1a;">중소벤처기업부</div>
<div style="font-size: 14px; color: #666; margin-top: 4px;">공고문 원본·첨부파일 다운로드</div>
<div style="font-size: 13px; color: #6c3483; margin-top: 4px;">mss.go.kr →</div>
</div>
</div>
</a>

<a href="https://www.bizinfo.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f8e8 100%);">
<div style="min-width: 60px; height: 60px; background: #27ae60; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 20px; font-weight: bold;">기업</span>
</div>
<div>
<div style="font-size: 18px; font-weight: bold; color: #1a1a1a;">기업마당</div>
<div style="font-size: 14px; color: #666; margin-top: 4px;">정부 지원사업 통합 검색·맞춤형 추천</div>
<div style="font-size: 13px; color: #27ae60; margin-top: 4px;">bizinfo.go.kr →</div>
</div>
</div>
</a>
</div>
"""

# 5. 첫 소제목(h2/h3) 앞에 요약카드 삽입
first_heading = re.search(r'<(h[23]|div\s+style="background)', cleaned)
if first_heading:
    idx = first_heading.start()
    cleaned = cleaned[:idx] + info_card + cleaned[idx:]

# 6. 마무리 섹션 앞에 링크카드 삽입
makmuri_match = re.search(r'(<div[^>]*>[\s\S]*?마무리[\s\S]*?</div>)', cleaned)
if makmuri_match:
    idx = makmuri_match.start()
    cleaned = cleaned[:idx] + link_cards + cleaned[idx:]
else:
    cleaned = cleaned + link_cards

# 7. 업데이트
resp = requests.post(
    f"{settings.wp_url}/wp-json/wp/v2/posts/{post_id}",
    auth=auth,
    json={"content": cleaned},
    timeout=15
)
if resp.status_code == 200:
    print(f"✅ 포스트 업데이트 완료 (ID: {post_id})")
else:
    print(f"❌ 실패: {resp.status_code} {resp.text[:200]}")
