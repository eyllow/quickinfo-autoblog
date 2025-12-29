"""대시보드 API Pydantic 모델"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# =============================================================================
# 글 생성 관련 모델
# =============================================================================

class ArticleCreate(BaseModel):
    """글 생성 요청"""
    keyword: str
    mode: str = "semi"  # "semi" or "evergreen"
    is_evergreen: bool = False  # 프론트엔드 호환용
    category: Optional[str] = None  # 직접 작성 시 카테고리 지정
    custom_context: Optional[str] = None  # 직접 작성 시 작성 방향


class AdjustLengthRequest(BaseModel):
    """글 길이 조절 요청"""
    target_length: str  # "short" or "long"


class AdjustLengthResponse(BaseModel):
    """글 길이 조절 응답"""
    success: bool
    new_length: int = 0
    error: Optional[str] = None


class Section(BaseModel):
    """글 섹션"""
    id: str
    title: str
    content: str
    order: int


class ArticleResponse(BaseModel):
    """글 응답"""
    id: str
    keyword: str
    title: str
    sections: List[Section]
    raw_content: str
    category: str = "트렌드"
    template: str = "trend"
    has_coupang: bool = False
    sources: List[dict] = []
    created_at: str
    status: str = "draft"
    wp_url: Optional[str] = None
    wp_id: Optional[int] = None


class SectionEditRequest(BaseModel):
    """섹션 수정 요청"""
    section_id: str
    instruction: str  # 수정 지시 (예: "더 친근하게", "내용 추가")
    new_content: Optional[str] = None  # 직접 수정된 내용


class SectionEditResponse(BaseModel):
    """섹션 수정 응답"""
    success: bool
    section: Optional[Section] = None
    error: Optional[str] = None


class NaturalEditRequest(BaseModel):
    """자연어 수정 요청"""
    instruction: str  # 자연어 수정 지시
    section_id: Optional[str] = None  # 특정 섹션 지정 (선택)


class NaturalEditResponse(BaseModel):
    """자연어 수정 응답"""
    success: bool
    action_type: str = ""  # "screenshot", "image_delete", "section_edit", "full_edit"
    message: str = ""
    updated_content: Optional[str] = None
    error: Optional[str] = None


class ElementEditRequest(BaseModel):
    """개별 요소 수정 요청 (섹션 단위, 서버 저장 없음)"""
    element_content: str  # 수정할 요소의 현재 HTML
    instruction: str  # 수정 지시
    element_type: str = "paragraph"  # title, paragraph, list, table, quote, image
    keyword: str = ""  # 키워드 (컨텍스트용)


class ElementEditResponse(BaseModel):
    """개별 요소 수정 응답"""
    success: bool
    updated_content: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# 발행 관련 모델
# =============================================================================

class PublishRequest(BaseModel):
    """발행 요청"""
    article_id: str
    status: str = "publish"  # "publish" or "draft"


class PublishResponse(BaseModel):
    """발행 응답"""
    success: bool
    url: Optional[str] = None
    post_id: Optional[int] = None
    error: Optional[str] = None


# =============================================================================
# 이미지 관련 모델
# =============================================================================

class ImageInfo(BaseModel):
    """이미지 정보"""
    url: str
    alt: str = ""
    type: str = "pexels"  # "pexels" or "screenshot"
    photographer: Optional[str] = None


class ImageReplaceRequest(BaseModel):
    """이미지 교체 요청"""
    article_id: str
    section_id: Optional[str] = None
    action: str  # "pexels", "screenshot", "delete"
    query: Optional[str] = None  # 검색어
    url: Optional[str] = None  # 스크린샷용 URL


class ImageReplaceResponse(BaseModel):
    """이미지 교체 응답"""
    success: bool
    image: Optional[ImageInfo] = None
    error: Optional[str] = None


class ImageSearchResponse(BaseModel):
    """이미지 검색 응답"""
    images: List[ImageInfo]


# =============================================================================
# 키워드/설정 관련 모델
# =============================================================================

class KeywordSuggestion(BaseModel):
    """키워드 추천"""
    keyword: str
    category: str
    is_evergreen: bool
    source: str  # "google_trends", "evergreen_config"


class DashboardStats(BaseModel):
    """대시보드 통계"""
    total_articles: int
    published_today: int
    draft_count: int
    categories: dict
