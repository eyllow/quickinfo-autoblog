"""이미지 관리 API 라우터"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

# 프로젝트 루트 경로 설정
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.image_fetcher import ImageFetcher
from utils.unique_image import generate_unique_screenshot
from dashboard.backend.models import (
    ImageReplaceRequest,
    ImageReplaceResponse,
    ImageSearchResponse,
    ImageInfo
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


@router.get("/search", response_model=ImageSearchResponse)
async def search_images(
    query: str = Query(..., description="검색어"),
    count: int = Query(6, ge=1, le=20, description="반환할 이미지 수")
):
    """
    Pexels 이미지 검색

    키워드로 Pexels에서 이미지 검색
    """
    try:
        fetcher = ImageFetcher()
        photos = fetcher.search_pexels_single(query, per_page=count)

        images = []
        for photo in photos:
            img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
            if img_url:
                images.append(ImageInfo(
                    url=img_url,
                    alt=photo.get("alt", query),
                    type="pexels",
                    photographer=photo.get("photographer", "Unknown")
                ))

        logger.info(f"Image search: '{query}' -> {len(images)} results")

        return ImageSearchResponse(images=images)

    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replace", response_model=ImageReplaceResponse)
async def replace_image(request: ImageReplaceRequest):
    """
    이미지 교체

    action에 따라:
    - pexels: Pexels에서 새 이미지 검색
    - screenshot: 스크린샷 생성
    - delete: 이미지 삭제
    """
    try:
        fetcher = ImageFetcher()

        if request.action == "pexels":
            if not request.query:
                raise HTTPException(status_code=400, detail="검색어가 필요합니다")

            # Pexels 검색
            photos = fetcher.search_pexels_single(request.query, per_page=5)

            if photos:
                photo = photos[0]
                img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")

                if img_url:
                    return ImageReplaceResponse(
                        success=True,
                        image=ImageInfo(
                            url=img_url,
                            alt=photo.get("alt", request.query),
                            type="pexels",
                            photographer=photo.get("photographer", "Unknown")
                        )
                    )

            return ImageReplaceResponse(
                success=False,
                error="이미지를 찾을 수 없습니다"
            )

        elif request.action == "screenshot":
            if not request.query:
                raise HTTPException(status_code=400, detail="키워드가 필요합니다")

            # 스크린샷 생성
            overlay_text = f"{request.query} ({datetime.now().strftime('%Y.%m.%d')})"
            screenshot_path = generate_unique_screenshot(request.query, overlay_text)

            if screenshot_path:
                # 워드프레스에 업로드
                uploaded_url = fetcher.upload_to_wordpress_media(
                    screenshot_path,
                    alt_text=f"{request.query} 실시간 정보"
                )

                if uploaded_url:
                    return ImageReplaceResponse(
                        success=True,
                        image=ImageInfo(
                            url=uploaded_url,
                            alt=f"{request.query} 실시간 정보",
                            type="screenshot"
                        )
                    )

            return ImageReplaceResponse(
                success=False,
                error="스크린샷 생성 실패"
            )

        elif request.action == "delete":
            return ImageReplaceResponse(
                success=True,
                image=None
            )

        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image replace failed: {e}")
        return ImageReplaceResponse(
            success=False,
            error=str(e)
        )


@router.get("/ai-suggest")
async def ai_suggest_image(
    context: str = Query(..., description="섹션 내용"),
    keyword: str = Query(..., description="블로그 키워드")
):
    """
    AI가 컨텍스트에 맞는 이미지 검색어 추천
    """
    try:
        fetcher = ImageFetcher()
        search_query = fetcher.generate_image_search_query(context, keyword)

        # 추천된 검색어로 이미지 검색
        photos = fetcher.search_pexels_single(search_query, per_page=4)

        images = []
        for photo in photos:
            img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("medium", "")
            if img_url:
                images.append({
                    "url": img_url,
                    "alt": photo.get("alt", search_query),
                    "photographer": photo.get("photographer", "Unknown")
                })

        return {
            "suggested_query": search_query,
            "images": images
        }

    except Exception as e:
        logger.error(f"AI suggest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-to-wordpress")
async def upload_to_wordpress(
    local_path: str = Query(..., description="로컬 파일 경로"),
    alt_text: str = Query("", description="대체 텍스트")
):
    """
    로컬 이미지를 WordPress에 업로드
    """
    try:
        fetcher = ImageFetcher()
        uploaded_url = fetcher.upload_to_wordpress_media(local_path, alt_text)

        if uploaded_url:
            return {
                "success": True,
                "url": uploaded_url
            }
        else:
            return {
                "success": False,
                "error": "업로드 실패"
            }

    except Exception as e:
        logger.error(f"WordPress upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
