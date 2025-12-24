"""콘텐츠 생성 모듈"""
from .content_generator import ContentGenerator, GeneratedPost
from .prompts import (
    SYSTEM_PROMPT,
    STRUCTURE_PROMPT,
    CATEGORY_TEMPLATES,
    get_template,
    OFFICIAL_BUTTON_TEMPLATE,
    COUPANG_BUTTON_TEMPLATE,
    COUPANG_DISCLAIMER,
    HEALTH_DISCLAIMER,
    AFFILIATE_NOTICE,
    CATEGORY_BADGE_TEMPLATE
)

__all__ = [
    "ContentGenerator",
    "GeneratedPost",
    "SYSTEM_PROMPT",
    "STRUCTURE_PROMPT",
    "CATEGORY_TEMPLATES",
    "get_template",
    "OFFICIAL_BUTTON_TEMPLATE",
    "COUPANG_BUTTON_TEMPLATE",
    "COUPANG_DISCLAIMER",
    "HEALTH_DISCLAIMER",
    "AFFILIATE_NOTICE",
    "CATEGORY_BADGE_TEMPLATE"
]
