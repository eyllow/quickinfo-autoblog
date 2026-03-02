"""
사진 기반 블로그 자동 생성기

사용자가 사진 + 간단한 메모를 보내면:
1. 장소명/브랜드명 추출
2. 네이버 블로그에서 인기 블로그 참조 수집
3. 참조 스타일로 글 작성
4. 사진을 WP에 업로드 후 본문에 삽입
5. 워드프레스에 발행
"""
import logging
import re
import json
import os
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


@dataclass
class PhotoBlogRequest:
    """사진 블로그 요청"""
    photos: List[str]         # 사진 파일 경로 또는 URL 리스트
    memo: str                 # 간단한 메모 (장소명, 설명 등)
    category: str = ""        # 카테고리 (자동 분류)
    publish: bool = True      # 바로 발행 여부 (False면 초안)


@dataclass
class PhotoBlogResult:
    """사진 블로그 생성 결과"""
    success: bool
    title: str = ""
    url: str = ""
    post_id: int = 0
    error: str = ""


class PhotoBlogGenerator:
    """사진 기반 블로그 생성기"""

    def __init__(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from config.settings import settings
        self.settings = settings

        # Gemini 초기화
        if HAS_GEMINI and settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model or "gemini-2.0-flash")
        else:
            raise RuntimeError("Gemini API required for photo blog generation")

        # WP 퍼블리셔
        from publishers.wordpress import WordPressPublisher
        self.wp = WordPressPublisher()

    def extract_keywords(self, memo: str) -> Dict:
        """메모에서 장소명, 브랜드명, 카테고리 추출"""
        prompt = f"""다음 메모에서 정보를 추출해주세요.

메모: "{memo}"

JSON으로만 응답 (다른 텍스트 없이):
{{
  "place_name": "장소/가게 이름 (없으면 빈 문자열)",
  "brand_name": "브랜드명 (없으면 빈 문자열)",
  "location": "지역/주소 (없으면 빈 문자열)",
  "category": "카페|맛집|여행|행사|일상 중 하나",
  "search_keyword": "네이버 블로그 검색에 사용할 최적 키워드 (예: '성수동 카페 OOO')",
  "tags": ["관련 태그 3~5개"]
}}"""

        result = self.model.generate_content(prompt)
        text = result.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    def search_reference_blogs(self, keyword: str, count: int = 5) -> List[Dict]:
        """네이버 블로그에서 참조 블로그 수집"""
        references = []

        try:
            from crawlers.blog_reference import BlogReferenceCrawler
            crawler = BlogReferenceCrawler()
            detailed = crawler.get_detailed_analysis(keyword, count=count)

            if detailed and detailed.get("blogs"):
                for blog in detailed["blogs"]:
                    references.append({
                        "title": blog.get("title", ""),
                        "headings": blog.get("headings", []),
                        "word_count": blog.get("word_count", 0),
                        "tone": blog.get("tone", ""),
                    })
                logger.info(f"Found {len(references)} reference blogs for '{keyword}'")

            # 분석 텍스트도 가져오기
            analysis_text = crawler.get_blog_analysis(keyword, count=count)
            return references, analysis_text

        except Exception as e:
            logger.warning(f"Blog reference search failed: {e}")

            # 폴백: 웹 검색으로 제목만 수집
            try:
                from utils.web_search import GoogleSearcher
                searcher = GoogleSearcher()
                if searcher.is_configured():
                    results = searcher.search_and_crawl(f"{keyword} 블로그", num_results=count)
                    for src in results.get("sources", []):
                        references.append({"title": src.get("title", ""), "headings": [], "word_count": 0})
            except Exception:
                pass

            return references, ""

    def upload_photos_to_wp(self, photo_paths: List[str]) -> List[Dict]:
        """사진을 워드프레스 미디어에 업로드"""
        uploaded = []
        import requests

        for i, path in enumerate(photo_paths):
            try:
                if path.startswith("http"):
                    # URL인 경우
                    media_id = self.wp.upload_image(image_url=path, title=f"photo-{i+1}")
                else:
                    # 로컬 파일인 경우
                    filename = os.path.basename(path)
                    with open(path, "rb") as f:
                        file_data = f.read()

                    resp = requests.post(
                        f"{self.settings.wp_url}/wp-json/wp/v2/media",
                        auth=(self.settings.wp_user, self.settings.wp_app_password),
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"',
                            "Content-Type": "image/jpeg",
                        },
                        data=file_data,
                        timeout=30,
                    )

                    if resp.status_code in (200, 201):
                        media_data = resp.json()
                        media_id = media_data["id"]
                    else:
                        logger.error(f"WP upload failed for {path}: {resp.status_code}")
                        continue

                if media_id:
                    # 업로드된 이미지 URL 가져오기
                    media_resp = requests.get(
                        f"{self.settings.wp_url}/wp-json/wp/v2/media/{media_id}",
                        auth=(self.settings.wp_user, self.settings.wp_app_password),
                        timeout=10,
                    )
                    if media_resp.status_code == 200:
                        url = media_resp.json().get("source_url", "")
                        uploaded.append({"id": media_id, "url": url, "index": i})
                        logger.info(f"Photo {i+1} uploaded: {url}")

            except Exception as e:
                logger.error(f"Failed to upload photo {i+1}: {e}")

        return uploaded

    def generate_blog_content(
        self,
        memo: str,
        keywords: Dict,
        photos: List[Dict],
        reference_analysis: str = "",
    ) -> Dict:
        """AI로 블로그 글 생성"""

        # 사진 배치 계획
        photo_slots = ""
        for p in photos:
            photo_slots += f'\n- [PHOTO_{p["index"]+1}]: {p["url"]}'

        prompt = f"""너는 네이버/구글 블로그 SEO 전문 작가야. 아래 정보를 바탕으로 블로그 글을 작성해.

[기본 정보]
- 장소/주제: {keywords.get('place_name', '')} {keywords.get('brand_name', '')}
- 지역: {keywords.get('location', '')}
- 카테고리: {keywords.get('category', '일상')}
- 작성자 메모: {memo}

[사용 가능한 사진] ({len(photos)}장)
{photo_slots}

{f'[참조 블로그 분석]{chr(10)}{reference_analysis}' if reference_analysis else ''}

[작성 규칙]
1. HTML 형식으로 작성 (마크다운 **금지**, ** 절대 사용 금지)
2. 2,000~3,000자 분량
3. 자연스럽고 따뜻한 1인칭 톤 ("~했어요", "~더라고요")
4. 소제목 4~6개 (h2 태그)
5. 사진은 적절한 위치에 figure/img 태그로 삽입
6. 각 사진에 자연스러운 캡션 추가
7. 인기 블로그 스타일 참고하되 표절하지 않기
8. 장소 정보 (주소, 영업시간 등)가 있으면 마지막에 정리
9. SEO 키워드: "{keywords.get('search_keyword', memo)}" 본문에 3~5회 자연스럽게 포함

[출력 형식] JSON만 출력 (다른 텍스트 없이):
{{
  "title": "블로그 제목 (30~40자, SEO 최적화)",
  "content": "HTML 본문 (사진 img 태그 포함)",
  "excerpt": "요약 (100자 이내)",
  "tags": ["태그1", "태그2", "태그3"]
}}"""

        result = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=8000,
                temperature=0.7,
            ),
        )

        text = result.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        # ** 마크다운 잔여물 제거
        if data.get("content"):
            data["content"] = data["content"].replace("**", "")
        if data.get("title"):
            data["title"] = data["title"].replace("**", "")

        return data

    def generate_and_publish(self, request: PhotoBlogRequest) -> PhotoBlogResult:
        """전체 파이프라인: 사진 → 분석 → 참조 수집 → 글 생성 → 발행"""
        try:
            logger.info(f"📸 사진 블로그 생성 시작: {request.memo}")
            print(f"\n{'='*50}")
            print(f"📸 사진 블로그 생성")
            print(f"{'='*50}")

            # 1. 키워드 추출
            print(f"\n[1/5] 키워드 추출 중...")
            keywords = self.extract_keywords(request.memo)
            print(f"  장소: {keywords.get('place_name', '-')}")
            print(f"  카테고리: {keywords.get('category', '-')}")
            print(f"  검색 키워드: {keywords.get('search_keyword', '-')}")

            # 2. 참조 블로그 수집
            print(f"\n[2/5] 참조 블로그 수집 중...")
            search_kw = keywords.get("search_keyword", request.memo)
            references, analysis_text = self.search_reference_blogs(search_kw)
            print(f"  참조 블로그: {len(references)}개")
            for ref in references[:3]:
                print(f"    - {ref['title'][:40]}")

            # 3. 사진 업로드
            print(f"\n[3/5] 사진 업로드 중 ({len(request.photos)}장)...")
            uploaded_photos = self.upload_photos_to_wp(request.photos)
            print(f"  업로드 완료: {len(uploaded_photos)}장")

            if not uploaded_photos:
                return PhotoBlogResult(success=False, error="사진 업로드 실패")

            # 4. 글 생성
            print(f"\n[4/5] AI 글 생성 중...")
            blog_data = self.generate_blog_content(
                memo=request.memo,
                keywords=keywords,
                photos=uploaded_photos,
                reference_analysis=analysis_text,
            )
            print(f"  제목: {blog_data['title']}")
            print(f"  본문: {len(blog_data.get('content', ''))}자")

            # 5. 발행
            print(f"\n[5/5] 워드프레스 발행 중...")

            # 카테고리 매핑
            category_map = {
                "카페": "생활정보",
                "맛집": "생활정보",
                "여행": "생활정보",
                "행사": "트렌드",
                "일상": "생활정보",
            }
            wp_category = category_map.get(keywords.get("category", ""), "생활정보")

            # 대표 이미지 설정
            featured_media_id = uploaded_photos[0]["id"] if uploaded_photos else None

            post_status = "publish" if request.publish else "draft"

            post_result = self.wp.publish_post(
                title=blog_data["title"],
                content=blog_data["content"],
                excerpt=blog_data.get("excerpt", ""),
                categories=[wp_category],
                tags=blog_data.get("tags", keywords.get("tags", [])),
                featured_media_id=featured_media_id,
                status=post_status,
            )

            if post_result and post_result.success:
                post_url = post_result.url or ""
                post_id = post_result.post_id or 0
                print(f"\n✅ 발행 완료!")
                print(f"  URL: {post_url}")
                print(f"{'='*50}\n")

                return PhotoBlogResult(
                    success=True,
                    title=blog_data["title"],
                    url=post_url,
                    post_id=post_id,
                )
            else:
                return PhotoBlogResult(success=False, error="워드프레스 발행 실패")

        except Exception as e:
            logger.error(f"Photo blog generation failed: {e}")
            return PhotoBlogResult(success=False, error=str(e))
