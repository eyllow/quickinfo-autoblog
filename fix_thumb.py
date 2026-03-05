"""포스트 716에 썸네일 설정"""
import requests, sys
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)

# 최근 미디어에서 thumbnail 찾기
r = requests.get(f"{settings.wp_url}/wp-json/wp/v2/media?per_page=10&orderby=date&order=desc", auth=auth, timeout=10)
for m in r.json():
    name = m["source_url"].split("/")[-1]
    mid = m["id"]
    print(f"  ID:{mid} - {name}")
    if "thumbnail" in name:
        # 이 썸네일을 포스트 716에 설정
        resp = requests.post(f"{settings.wp_url}/wp-json/wp/v2/posts/716",
                            auth=auth, json={"featured_media": mid}, timeout=10)
        print(f"  ✅ Featured media set: {resp.status_code}")
        break
