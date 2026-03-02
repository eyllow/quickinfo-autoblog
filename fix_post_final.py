"""포스트 703 최종 수정: 이미지 삭제, &#8 수정, 정보카드→본문 시작, 링크카드→본문 시작 바로 아래"""
import requests, sys, re
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)

# 포스트 가져오기
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts/703", auth=auth, timeout=10)
post = r.json()
content = post["content"]["rendered"]
print(f"원본 길이: {len(content)}자")

# 1. 모든 figure/img 태그 삭제 (Pexels 이미지)
content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL)
print("✅ 이미지 삭제")

# 2. &#8 깨진 문자 수정 — HTML 엔티티 깨진 것들
content = content.replace("&#8", "")
content = content.replace("&amp;#8", "")
# 혹시 다른 깨진 엔티티도
content = re.sub(r'&#\d{1,2}(?!\d)', '', content)  # 불완전한 HTML entity 제거
print("✅ 깨진 문자 수정")

# 3. 기존 정보카드 + 링크카드 위치 찾아서 제거
# 정보카드 (📋 2026 예비창업패키지 핵심 요약)
content = re.sub(r'<div[^>]*>[\s]*<h3[^>]*>📋[^<]*</h3>[\s\S]*?</table>[\s]*</div>', '', content)
# 링크카드 (📌 관련 사이트 바로가기)
content = re.sub(r'<div[^>]*>[\s]*<h3[^>]*>📌[^<]*</h3>[\s\S]*?bizinfo\.go\.kr[^<]*</div>[\s]*</div>[\s]*</a>[\s]*</div>', '', content, flags=re.DOTALL)
print("✅ 기존 카드 제거")

# 4. 빈 p태그 정리
content = re.sub(r'<p>\s*</p>', '', content)
content = re.sub(r'\n{3,}', '\n\n', content)

# 5. 새 정보카드 + 링크카드 (본문 시작 부분에 삽입)
top_cards = """
<div style="border: 2px solid #4a90d9; border-radius: 12px; padding: 25px; margin: 0 0 25px 0; background: linear-gradient(135deg, #eef5ff 0%, #f0f7ff 100%);">
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

<div style="margin: 0 0 30px 0;">
<h3 style="margin-bottom: 15px;">📌 관련 사이트 바로가기</h3>

<a href="https://www.k-startup.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; margin-bottom: 12px;">
<div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 18px; display: flex; align-items: center; gap: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4f8 100%);">
<div style="min-width: 50px; height: 50px; background: #1a73e8; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-size: 24px; font-weight: bold;">K</span>
</div>
<div>
<div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">K-Startup (창업넷)</div>
<div style="font-size: 13px; color: #666; margin-top: 3px;">예비창업패키지 온라인 신청·접수</div>
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

# 6. 본문 시작에 카드 삽입
content = top_cards + content.strip()

# 7. 업데이트
resp = requests.post(
    f"{settings.wp_url}/wp-json/wp/v2/posts/703",
    auth=auth,
    json={"content": content},
    timeout=15
)
if resp.status_code == 200:
    print(f"✅ 최종 수정 완료! 길이: {len(content)}자")
else:
    print(f"❌ 실패: {resp.status_code} {resp.text[:200]}")
