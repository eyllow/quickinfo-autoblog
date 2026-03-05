"""최신 포스트에 링크카드 추가"""
import requests, sys
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)

# 최신 포스트
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts?per_page=1&orderby=date&order=desc", auth=auth, timeout=10)
post = r.json()[0]
post_id = post["id"]
content = post["content"]["rendered"]
print(f"Post {post_id}: {post['title']['rendered'][:40]}")

# WP 호환 링크카드 (table 구조, wpautop 영향 없음)
link_cards = '''<table style="border:none;border-collapse:collapse;width:100%;margin:0 0 30px 0;"><tr><td style="border:none;padding:0;"><h3 style="margin-bottom:15px;">📌 관련 사이트 바로가기</h3><a href="https://www.k-startup.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:block;margin-bottom:12px;border:2px solid #e0e0e0;border-radius:12px;padding:18px;background:linear-gradient(135deg,#f8f9fa 0%,#e8f4f8 100%);"><table style="border:none;border-collapse:collapse;width:100%;"><tr><td style="width:50px;border:none;padding:0;vertical-align:middle;"><span style="display:inline-block;width:50px;height:50px;background:#1a73e8;border-radius:10px;text-align:center;line-height:50px;color:white;font-size:24px;font-weight:bold;">K</span></td><td style="padding-left:15px;border:none;vertical-align:middle;"><span style="font-size:16px;font-weight:bold;color:#1a1a1a;">K-Startup (창업넷)</span><br/><span style="font-size:13px;color:#666;">예비창업패키지 온라인 신청·접수 사이트</span><br/><span style="font-size:12px;color:#1a73e8;">k-startup.go.kr →</span></td></tr></table></a><a href="https://www.mss.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:block;margin-bottom:12px;border:2px solid #e0e0e0;border-radius:12px;padding:18px;background:linear-gradient(135deg,#f8f9fa 0%,#f0e8f8 100%);"><table style="border:none;border-collapse:collapse;width:100%;"><tr><td style="width:50px;border:none;padding:0;vertical-align:middle;"><span style="display:inline-block;width:50px;height:50px;background:#6c3483;border-radius:10px;text-align:center;line-height:50px;color:white;font-size:20px;font-weight:bold;">중기</span></td><td style="padding-left:15px;border:none;vertical-align:middle;"><span style="font-size:16px;font-weight:bold;color:#1a1a1a;">중소벤처기업부</span><br/><span style="font-size:13px;color:#666;">공고문 원본·첨부파일 다운로드</span><br/><span style="font-size:12px;color:#6c3483;">mss.go.kr →</span></td></tr></table></a><a href="https://www.bizinfo.go.kr" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:block;border:2px solid #e0e0e0;border-radius:12px;padding:18px;background:linear-gradient(135deg,#f8f9fa 0%,#e8f8e8 100%);"><table style="border:none;border-collapse:collapse;width:100%;"><tr><td style="width:50px;border:none;padding:0;vertical-align:middle;"><span style="display:inline-block;width:50px;height:50px;background:#27ae60;border-radius:10px;text-align:center;line-height:50px;color:white;font-size:18px;font-weight:bold;">기업</span></td><td style="padding-left:15px;border:none;vertical-align:middle;"><span style="font-size:16px;font-weight:bold;color:#1a1a1a;">기업마당</span><br/><span style="font-size:13px;color:#666;">정부 지원사업 통합 검색·맞춤형 추천</span><br/><span style="font-size:12px;color:#27ae60;">bizinfo.go.kr →</span></td></tr></table></a></td></tr></table>'''

# 정보카드(📋) 뒤에 삽입
info_end = content.find('</table>')
if info_end > 0:
    # 정보카드 닫는 </div> 찾기
    div_end = content.find('</div>', info_end)
    if div_end > 0:
        insert_at = div_end + 6
        content = content[:insert_at] + "\n" + link_cards + "\n" + content[insert_at:]
        print("✅ 링크카드 삽입")

resp = requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/{post_id}",
                     auth=auth, json={"content": content}, timeout=15)
print(f"Update: {resp.status_code}")
