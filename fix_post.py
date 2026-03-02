import requests, json, sys, re, os
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)
base = settings.wp_url

# 1. 최근 포스트
r = requests.get(f"{base}/wp-json/wp/v2/posts?per_page=1&status=publish", auth=auth, timeout=10)
post = r.json()[0]
post_id = post["id"]
print(f"POST_ID: {post_id}")

# 2. 새 사진 업로드
new_photos = {}
for label, path in [("bar", "/tmp/photos/file_30---713170d7-e616-41ab-9612-756aeffa2dc4.jpg"),
                     ("drink", "/tmp/photos/file_31---f6ce93d9-fe74-4596-8466-3537886ed434.jpg")]:
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        file_data = f.read()
    resp = requests.post(
        f"{base}/wp-json/wp/v2/media",
        auth=auth,
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"},
        data=file_data, timeout=30
    )
    if resp.status_code in (200, 201):
        media = resp.json()
        new_photos[label] = media["source_url"]
        print(f"UPLOADED {label}: {media['source_url']}")

# 3. 기존 이미지 URL 추출
content = post["content"]["rendered"]
imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
for i, img in enumerate(imgs):
    print(f"IMG_{i}: {img}")

# 전체 content 저장
with open("/tmp/post_content.html", "w") as f:
    f.write(content)
print(f"\nContent saved to /tmp/post_content.html ({len(content)} chars)")
print(f"New photos: {json.dumps(new_photos)}")
