"""Dashboard API Routers"""
from .articles import router as articles_router
from .publish import router as publish_router
from .images import router as images_router
from .sections import router as sections_router

__all__ = ["articles_router", "publish_router", "images_router", "sections_router"]
