import requests, sys
sys.path.insert(0, ".")
from config.settings import settings

with open("/tmp/quickinfo-og.png", "rb") as f:
    data = f.read()

resp = requests.post(
    f"{settings.wp_url}/wp-json/wp/v2/media",
    auth=(settings.wp_user, settings.wp_app_password),
    headers={"Content-Disposition": 'attachment; filename="quickinfo-og.png"', "Content-Type": "image/png"},
    data=data, timeout=30
)
if resp.status_code in (200, 201):
    media = resp.json()
    print(f"URL: {media['source_url']}")
    print(f"ID: {media['id']}")
else:
    print(f"Error: {resp.status_code} {resp.text[:200]}")
