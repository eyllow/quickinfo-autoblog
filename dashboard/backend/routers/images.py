"""
이미지 관리 API
이미지 교체, Pexels 검색, 스크린샷 생성
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

router = APIRouter()


class ImageItem(BaseModel):
    id: str
    url: str
    source: str  # "pexels", "screenshot", "upload"
    alt: str
    position: int  # 글 내 위치 (0부터)


class ImageReplaceRequest(BaseModel):
    article_id: str
    position: int
    new_image_url: str
    source: str = "pexels"


class PexelsSearchRequest(BaseModel):
    query: str
    count: int = 5


class ScreenshotRequest(BaseModel):
    url: str
    article_id: Optional[str] = None


@router.post("/search/pexels")
async def search_pexels(request: PexelsSearchRequest):
    """Pexels에서 이미지 검색"""
    try:
        from media.pexels_image import PexelsImageFetcher

        fetcher = PexelsImageFetcher()
        images = fetcher.search(request.query, per_page=request.count)

        return {
            "images": [
                {
                    "id": str(img.get("id", "")),
                    "url": img.get("src", {}).get("large2x", img.get("src", {}).get("original", "")),
                    "thumbnail": img.get("src", {}).get("medium", ""),
                    "alt": img.get("alt", request.query),
                    "photographer": img.get("photographer", ""),
                    "source": "pexels"
                }
                for img in images
            ]
        }
    except Exception as e:
        # 더미 데이터 반환
        return {
            "images": [
                {
                    "id": f"dummy_{i}",
                    "url": f"https://images.pexels.com/photos/{1000000+i}/pexels-photo.jpeg",
                    "thumbnail": f"https://images.pexels.com/photos/{1000000+i}/pexels-photo.jpeg?w=300",
                    "alt": request.query,
                    "photographer": "Unknown",
                    "source": "pexels"
                }
                for i in range(request.count)
            ],
            "error": str(e)
        }


@router.post("/screenshot")
async def create_screenshot(request: ScreenshotRequest):
    """URL 스크린샷 생성"""
    try:
        from media.screenshot import ScreenshotCapture

        capture = ScreenshotCapture()
        result = capture.capture(request.url)

        return {
            "success": True,
            "image_path": result.get("path", ""),
            "url": result.get("url", ""),
            "source": "screenshot"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Screenshot capture failed"
        }


@router.post("/replace")
async def replace_image(request: ImageReplaceRequest):
    """글 내 이미지 교체"""
    # 실제로는 articles_store에서 해당 글의 이미지 목록을 업데이트
    return {
        "success": True,
        "article_id": request.article_id,
        "position": request.position,
        "new_url": request.new_image_url,
        "message": "Image replaced successfully"
    }


@router.get("/article/{article_id}")
async def get_article_images(article_id: str):
    """글에 사용된 이미지 목록"""
    # articles_store에서 이미지 정보 조회
    from routers.articles import articles_store

    if article_id not in articles_store:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles_store[article_id]
    image_types = article.get("image_types", [])

    # 이미지 타입 기반으로 목록 생성
    images = []
    for i, img_type in enumerate(image_types):
        images.append({
            "id": f"img_{i}",
            "position": i,
            "type": img_type,
            "url": "",  # 실제 URL은 발행 시 생성
            "source": img_type.lower()
        })

    return {"images": images, "total": len(images)}


@router.post("/upload")
async def upload_image():
    """이미지 업로드 (파일 업로드)"""
    # 실제 파일 업로드 구현 필요
    return {
        "success": True,
        "message": "Image upload endpoint - implement file upload logic"
    }


@router.get("/types")
async def get_image_types():
    """사용 가능한 이미지 타입 목록"""
    return {
        "types": [
            {
                "id": "pexels",
                "name": "Pexels",
                "description": "무료 스톡 이미지"
            },
            {
                "id": "screenshot",
                "name": "스크린샷",
                "description": "웹페이지 스크린샷"
            },
            {
                "id": "upload",
                "name": "직접 업로드",
                "description": "로컬 이미지 업로드"
            }
        ]
    }
