import requests, sys, re
sys.path.insert(0, ".")
from config.settings import settings

auth = (settings.wp_user, settings.wp_app_password)
base = settings.wp_url
post_id = 695

# Get current content
r = requests.get(f"{base}/wp-json/wp/v2/posts/{post_id}", auth=auth, timeout=10)
content = r.json()["content"]["rendered"]

# Remove the broken image block (file_27 alt text showing without img rendering)
# Pattern: the figure block with file_27
broken_pattern = r'<figure>\s*<img[^>]*file_27[^>]*>\s*<figcaption>[^<]*</figcaption>\s*</figure>'
new_content = re.sub(broken_pattern, '', content)

# Also remove the paragraph right before it that references it
new_content = new_content.replace(
    "건물 주변을 잠시 둘러보았는데, 곳곳에 놓인 조형물들도 인상 깊었어요. 단순히 스타벅스 매장이 아니라, 주변 가나아트파크와 연계되어 예술적인 분위기를 한층 더해주는 것 같았어요. 통나무 외관 덕분에 사계절 언제 찾아도 그 계절만의 아름다움을 느낄 수 있을 것 같다는 생각이 들었답니다.",
    "건물 주변 곳곳에 놓인 조형물들도 인상 깊었어요. 주변 가나아트파크와 연계되어 예술적인 분위기를 한층 더해주고 있었고요."
)

# Remove excessive repetition of "양주 스타벅스 가나아트파크점" - keep first 2-3 mentions, simplify the rest
count = 0
def replace_nth(match):
    global count
    count += 1
    if count <= 3:
        return match.group(0)
    return "이곳" if "양주" in match.group(0) else match.group(0)

# Clean up double newlines
new_content = re.sub(r'\n{3,}', '\n\n', new_content)

resp = requests.post(
    f"{base}/wp-json/wp/v2/posts/{post_id}",
    auth=auth,
    json={"content": new_content},
    timeout=30
)
print(f"Post update: {resp.status_code}")
