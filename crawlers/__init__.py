"""크롤러 모듈"""
from .google_trends import GoogleTrendsCrawler
from .naver_news import NaverNewsCrawler

__all__ = ["GoogleTrendsCrawler", "NaverNewsCrawler"]
