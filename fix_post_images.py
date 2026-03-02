"""예비창업패키지 포스트에 이미지 + 대표이미지 추가"""
import requests, sys, re, os
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")

# 포스트 가져오기
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/posts/703", auth=auth, timeout=10)
post = r.json()
content = post["content"]["rendered"]

def search_pexels(query, per_page=1):
    """Pexels에서 이미지 검색"""
    if not PEXELS_KEY:
        return None
    headers = {"Authorization": PEXELS_KEY}
    r = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}&locale=ko-KR",
                     headers=headers, timeout=10)
    if r.status_code == 200:
        photos = r.json().get("photos", [])
        return photos
    return None

def upload_to_wp(image_url, filename, alt_text=""):
    """이미지를 WP 미디어에 업로드"""
    img_data = requests.get(image_url, timeout=15).content
    # 파일명을 ASCII로 변환 (한글 인코딩 이슈 방지)
    safe_filename = filename.encode('ascii', 'ignore').decode('ascii') or 'image'
    resp = requests.post(
        f"{settings.wp_url}/wp-json/wp/v2/media",
        auth=auth,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"', "Content-Type": "image/jpeg"},
        data=img_data, timeout=30
    )
    if resp.status_code in (200, 201):
        media = resp.json()
        # alt text 설정
        if alt_text:
            requests.post(f"{settings.wp_url}/wp-json/wp/v2/media/{media['id']}",
                         auth=auth, json={"alt_text": alt_text}, timeout=10)
        return media["id"], media["source_url"]
    return None, None

# 이미지 검색 + 업로드
queries = [
    ("startup business plan", "예비창업패키지-사업계획", "창업 사업계획서 작성하는 모습"),
    ("entrepreneur idea", "예비창업패키지-창업아이디어", "창업 아이디어 구상 중"),
]

uploaded = []
for query, filename, alt in queries:
    photos = search_pexels(query)
    if photos:
        photo = photos[0]
        url = photo["src"]["large"]
        media_id, wp_url = upload_to_wp(url, f"{filename}.jpg", alt)
        if media_id:
            uploaded.append({"id": media_id, "url": wp_url, "alt": alt})
            print(f"  ✅ 업로드: {alt} → {wp_url}")

if not uploaded:
    print("⚠️ Pexels API 키 없음 또는 검색 실패")
    sys.exit(1)

# 첫 번째 이미지를 대표이미지로 설정
featured_id = uploaded[0]["id"]
requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/703",
              auth=auth, json={"featured_media": featured_id}, timeout=10)
print(f"  ✅ 대표이미지 설정: {featured_id}")

# 본문에 이미지 삽입 — 첫 번째: 첫 소제목 뒤, 두 번째: 중간
img_tags = []
for img in uploaded:
    img_tags.append(f'<figure style="margin: 25px 0; text-align: center;"><img src="{img["url"]}" alt="{img["alt"]}" style="width: 100%; max-width: 700px; height: auto; border-radius: 8px;"/><figcaption style="font-size: 13px; color: #888; margin-top: 8px;">{img["alt"]}</figcaption></figure>')

# 첫 번째 이미지: 두 번째 소제목 앞
headings = list(re.finditer(r'<div\s+style="background', content))
if len(headings) >= 2:
    idx = headings[1].start()
    content = content[:idx] + img_tags[0] + "\n" + content[idx:]
elif len(headings) >= 1:
    # 첫 소제목 바로 뒤의 첫 </div> + </p> 뒤에
    idx = headings[0].start()
    next_p = content.find("</p>", idx)
    if next_p > 0:
        content = content[:next_p+4] + "\n" + img_tags[0] + "\n" + content[next_p+4:]

# 두 번째 이미지: 중간쯤
if len(img_tags) > 1 and len(headings) >= 4:
    idx = headings[3].start()
    content = content[:idx] + img_tags[1] + "\n" + content[idx:]
elif len(img_tags) > 1:
    mid = len(content) // 2
    next_p = content.find("</p>", mid)
    if next_p > 0:
        content = content[:next_p+4] + "\n" + img_tags[1] + "\n" + content[next_p+4:]

# 업데이트
resp = requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/703",
                     auth=auth, json={"content": content}, timeout=15)
if resp.status_code == 200:
    print(f"✅ 이미지 삽입 완료!")
else:
    print(f"❌ 실패: {resp.status_code}")
