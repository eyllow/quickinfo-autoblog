"""
스마트 이미지 삽입 모듈
- 소제목별 연관 키워드 추출 → 다양한 이미지 검색
- 중복 방지 (이미 사용된 이미지 ID 추적)
- 소제목 내용과 연관된 위치에 삽입
- 이미지 필요성 판단 (글 길이, 소제목 수 기반)
"""
import re
import logging
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 카테고리별 이미지 검색 키워드 매핑
CATEGORY_IMAGE_KEYWORDS = {
    "재테크": ["money savings", "finance planning", "investment growth", "bank account", "budget management"],
    "건강": ["healthy lifestyle", "exercise fitness", "nutrition food", "wellness meditation", "healthcare"],
    "생활정보": ["home organization", "daily life tips", "household items", "cleaning home", "lifestyle"],
    "IT/테크": ["technology gadgets", "computer workspace", "smartphone apps", "digital innovation", "coding"],
    "취업교육": ["job interview", "career development", "office workplace", "resume writing", "education study"],
    "여행": ["travel destination", "vacation scenery", "tourism landmark", "adventure outdoor", "beach sunset"],
    "트렌드": ["modern lifestyle", "trendy items", "popular culture", "fashion style", "urban life"],
}

# 한국어 → 영어 키워드 매핑 (Pexels 검색용)
KO_EN_KEYWORDS = {
    "봄": "spring nature", "여름": "summer beach", "가을": "autumn leaves", "겨울": "winter snow",
    "나들이": "outdoor picnic", "여행": "travel vacation", "건강": "health wellness",
    "운동": "fitness exercise", "다이어트": "diet healthy food", "요리": "cooking food",
    "재테크": "money finance", "저축": "savings piggy bank", "투자": "investment growth",
    "청년": "young professional", "직장": "office workplace", "취업": "job interview",
    "공부": "study education", "자격증": "certificate achievement", "면접": "interview meeting",
    "인테리어": "interior design", "청소": "cleaning home", "정리": "organization storage",
    "꽃": "flowers garden", "벚꽃": "cherry blossom", "카페": "coffee cafe",
}


class SmartImageInserter:
    """스마트 이미지 삽입기"""

    def __init__(self, pexels_api_key: str, wp_url: str, wp_auth: Tuple[str, str]):
        self.pexels_key = pexels_api_key
        self.wp_url = wp_url
        self.wp_auth = wp_auth
        self.used_image_ids = set()  # 중복 방지

    def analyze_content_for_images(self, content: str, keyword: str, category: str) -> Dict:
        """본문 분석 → 이미지 삽입 계획"""
        # 소제목 추출
        headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', content, re.DOTALL)
        headings = [re.sub(r'<[^>]+>', '', h).strip() for h in headings]

        # 글 길이
        text_length = len(re.sub(r'<[^>]+>', '', content))

        # 이미지 필요 여부 판단
        need_images = text_length >= 1500 or len(headings) >= 3

        # 이미지 수 결정 (소제목 2개당 1개, 최대 4개)
        image_count = min(max(len(headings) // 2, 1), 4) if need_images else 0

        # 삽입 위치 결정 (균등 분배)
        insert_positions = []
        if image_count > 0 and len(headings) > 0:
            step = max(len(headings) // image_count, 1)
            for i in range(image_count):
                pos = min(i * step, len(headings) - 1)
                if pos not in insert_positions:
                    insert_positions.append(pos)

        # 각 위치별 검색 키워드 생성
        search_queries = []
        for i, pos in enumerate(insert_positions):
            if pos < len(headings):
                heading_text = headings[pos]
                query = self._generate_search_query(heading_text, keyword, category, i)
                search_queries.append({
                    "position": pos,
                    "heading": heading_text,
                    "query": query,
                })

        return {
            "need_images": need_images,
            "image_count": image_count,
            "headings": headings,
            "text_length": text_length,
            "search_queries": search_queries,
        }

    def _generate_search_query(self, heading: str, keyword: str, category: str, index: int) -> str:
        """소제목 + 키워드 + 카테고리 기반 검색어 생성"""
        # 1. 소제목에서 키워드 추출
        heading_keywords = []
        for ko, en in KO_EN_KEYWORDS.items():
            if ko in heading:
                heading_keywords.append(en)

        # 2. 메인 키워드에서 추출
        for ko, en in KO_EN_KEYWORDS.items():
            if ko in keyword:
                heading_keywords.append(en)

        # 3. 카테고리 기본 키워드
        category_keywords = CATEGORY_IMAGE_KEYWORDS.get(category, CATEGORY_IMAGE_KEYWORDS["트렌드"])

        # 조합 (다양성을 위해 index 활용)
        if heading_keywords:
            query = heading_keywords[index % len(heading_keywords)]
        elif category_keywords:
            query = category_keywords[index % len(category_keywords)]
        else:
            query = "lifestyle modern"

        return query

    def fetch_and_upload_images(self, search_queries: List[Dict]) -> List[Dict]:
        """Pexels 검색 → WP 업로드"""
        uploaded = []

        for sq in search_queries:
            query = sq["query"]
            heading = sq["heading"]
            position = sq["position"]

            try:
                # Pexels 검색 (여러 장 가져와서 미사용 이미지 선택)
                pr = requests.get(
                    "https://api.pexels.com/v1/search",
                    params={"query": query, "per_page": 5, "orientation": "landscape"},
                    headers={"Authorization": self.pexels_key},
                    timeout=10
                )

                if pr.status_code != 200:
                    logger.warning(f"Pexels search failed for '{query}': {pr.status_code}")
                    continue

                photos = pr.json().get("photos", [])

                # 미사용 이미지 찾기
                selected_photo = None
                for photo in photos:
                    if photo["id"] not in self.used_image_ids:
                        selected_photo = photo
                        self.used_image_ids.add(photo["id"])
                        break

                if not selected_photo:
                    logger.warning(f"No unused image for '{query}'")
                    continue

                img_url = selected_photo["src"]["large2x"]
                alt_text = selected_photo.get("alt", heading)[:100]

                # WP 업로드
                img_data = requests.get(img_url, timeout=30).content
                filename = f"{query.replace(' ', '_')}_{position}.jpg"
                files = {"file": (filename, img_data, "image/jpeg")}

                mr = requests.post(
                    f"{self.wp_url}/wp-json/wp/v2/media",
                    files=files,
                    auth=self.wp_auth,
                    timeout=30
                )

                if mr.status_code == 201:
                    media_data = mr.json()
                    uploaded.append({
                        "position": position,
                        "heading": heading,
                        "media_id": media_data["id"],
                        "url": media_data["source_url"],
                        "alt": alt_text,
                        "query": query,
                    })
                    logger.info(f"Uploaded image for '{heading[:30]}': {query}")

            except Exception as e:
                logger.warning(f"Image fetch/upload failed for '{query}': {e}")

        return uploaded

    def insert_images_into_content(self, content: str, images: List[Dict]) -> str:
        """본문에 이미지 삽입 (소제목 앞)"""
        if not images:
            return content

        # 소제목 위치 찾기
        heading_matches = list(re.finditer(r'<h[23][^>]*>', content))

        # 이미지를 position 역순으로 삽입 (offset 문제 방지)
        images_sorted = sorted(images, key=lambda x: x["position"], reverse=True)

        for img in images_sorted:
            pos_idx = img["position"]
            if pos_idx >= len(heading_matches):
                continue

            insert_pos = heading_matches[pos_idx].start()

            img_html = f'''
<figure style="margin:30px 0;text-align:center;">
  <img src="{img['url']}" alt="{img['alt']}" 
       style="max-width:100%;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);" 
       loading="lazy"/>
  <figcaption style="margin-top:12px;font-size:14px;color:#666;font-style:italic;">
    {img['alt'][:50]}
  </figcaption>
</figure>
'''
            content = content[:insert_pos] + img_html + content[insert_pos:]

        return content


def smart_insert_images(
    content: str,
    keyword: str,
    category: str,
    pexels_key: str,
    wp_url: str,
    wp_auth: Tuple[str, str]
) -> Tuple[str, int, Optional[int]]:
    """
    스마트 이미지 삽입 메인 함수

    Returns:
        (updated_content, image_count, featured_media_id)
    """
    inserter = SmartImageInserter(pexels_key, wp_url, wp_auth)

    # 1. 분석
    analysis = inserter.analyze_content_for_images(content, keyword, category)

    if not analysis["need_images"]:
        logger.info("Images not needed for this content")
        return content, 0, None

    logger.info(f"Image plan: {analysis['image_count']} images for {len(analysis['headings'])} headings")

    # 2. 이미지 가져오기 + 업로드
    uploaded = inserter.fetch_and_upload_images(analysis["search_queries"])

    if not uploaded:
        logger.warning("No images uploaded")
        return content, 0, None

    # 3. 본문에 삽입
    updated_content = inserter.insert_images_into_content(content, uploaded)

    # 4. 썸네일 ID (첫 번째 이미지)
    featured_id = uploaded[0]["media_id"] if uploaded else None

    return updated_content, len(uploaded), featured_id
