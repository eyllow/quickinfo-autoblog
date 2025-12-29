"""
키워드 관리 API
트렌드 키워드 및 에버그린 키워드 조회
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from dashboard.backend.utils.log_manager import (
    log_info_sync, log_success_sync, log_progress_sync, log_warning_sync
)

router = APIRouter()


class KeywordItem(BaseModel):
    keyword: str
    trend_score: int  # 1-5
    category: str
    source: str  # "trends" or "evergreen"


class KeywordResponse(BaseModel):
    keywords: List[KeywordItem]


class RefreshRequest(BaseModel):
    type: str = "trend"  # "trend" or "evergreen"


@router.get("/trending", response_model=KeywordResponse)
async def get_trending_keywords():
    """Google Trends에서 실시간 인기 키워드 가져오기"""
    try:
        from crawlers.google_trends import GoogleTrendsCrawler

        crawler = GoogleTrendsCrawler()
        trend_data = crawler.get_trending_keywords(count=10)

        return {
            "keywords": [
                {
                    "keyword": item["keyword"],
                    "trend_score": 5 - i if i < 5 else 1,
                    "category": item.get("category", "트렌드"),
                    "source": "trends"
                }
                for i, item in enumerate(trend_data)
            ]
        }
    except Exception as e:
        # 실패 시 더미 데이터 반환
        return {
            "keywords": [
                {"keyword": "연말정산", "trend_score": 5, "category": "재테크", "source": "trends"},
                {"keyword": "청년도약계좌", "trend_score": 4, "category": "재테크", "source": "trends"},
                {"keyword": "실업급여", "trend_score": 4, "category": "생활", "source": "trends"},
                {"keyword": "국민연금", "trend_score": 3, "category": "재테크", "source": "trends"},
                {"keyword": "건강보험", "trend_score": 3, "category": "생활", "source": "trends"},
            ]
        }


@router.get("/evergreen", response_model=KeywordResponse)
async def get_evergreen_keywords():
    """에버그린 키워드 목록"""
    try:
        import json
        from config.settings import settings

        evergreen_path = settings.project_root / "config" / "evergreen_keywords.json"
        with open(evergreen_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        keywords = data.get("keywords", [])

        return {
            "keywords": [
                {
                    "keyword": kw,
                    "trend_score": 3,
                    "category": "에버그린",
                    "source": "evergreen"
                }
                for kw in keywords[:15]
            ]
        }
    except Exception as e:
        # 실패 시 기본 목록 반환
        return {
            "keywords": [
                {"keyword": "연말정산 하는 법", "trend_score": 3, "category": "에버그린", "source": "evergreen"},
                {"keyword": "실업급여 신청방법", "trend_score": 3, "category": "에버그린", "source": "evergreen"},
                {"keyword": "청년도약계좌 조건", "trend_score": 3, "category": "에버그린", "source": "evergreen"},
                {"keyword": "국민연금 수령액", "trend_score": 3, "category": "에버그린", "source": "evergreen"},
                {"keyword": "건강보험 피부양자", "trend_score": 3, "category": "에버그린", "source": "evergreen"},
            ]
        }


@router.post("/refresh")
async def refresh_keywords(request: RefreshRequest = RefreshRequest()):
    """키워드 새로고침 (트렌드 또는 에버그린)"""
    try:
        log_progress_sync("keyword", f"키워드 새로고침 시작 (유형: {request.type})")

        if request.type == "evergreen":
            # 에버그린: 하드코딩된 키워드 랜덤 셔플
            import random
            evergreen_list = [
                {"keyword": "연말정산 하는 법", "category": "에버그린"},
                {"keyword": "실업급여 신청방법", "category": "에버그린"},
                {"keyword": "청년도약계좌 조건", "category": "에버그린"},
                {"keyword": "국민연금 수령액", "category": "에버그린"},
                {"keyword": "건강보험 피부양자", "category": "에버그린"},
                {"keyword": "자동차보험 비교", "category": "에버그린"},
                {"keyword": "신용카드 추천", "category": "에버그린"},
                {"keyword": "적금 금리 비교", "category": "에버그린"},
                {"keyword": "주택청약 조건", "category": "에버그린"},
                {"keyword": "종합소득세 신고", "category": "에버그린"},
            ]
            random.shuffle(evergreen_list)
            result_keywords = evergreen_list[:10]
            log_success_sync("keyword", f"에버그린 키워드 {len(result_keywords)}개 로드 완료")
            return {
                "success": True,
                "keywords": [
                    {
                        "keyword": kw["keyword"],
                        "trend_score": 3,
                        "category": kw["category"],
                        "source": "evergreen"
                    }
                    for kw in result_keywords
                ]
            }
        else:
            # 트렌드: Google Trends에서 새로 가져오기
            log_progress_sync("keyword", "Google Trends에서 트렌드 키워드 수집 중...")
            from crawlers.google_trends import GoogleTrendsCrawler

            crawler = GoogleTrendsCrawler()
            trend_data = crawler.get_trending_keywords()  # 파라미터 없이 호출

            result_count = len(trend_data[:10])
            log_success_sync("keyword", f"트렌드 키워드 {result_count}개 수집 완료")

            return {
                "success": True,
                "keywords": [
                    {
                        "keyword": item["keyword"] if isinstance(item, dict) else str(item),
                        "trend_score": 5 - i if i < 5 else 1,
                        "category": item.get("category", "트렌드") if isinstance(item, dict) else "트렌드",
                        "source": "trends"
                    }
                    for i, item in enumerate(trend_data[:10])
                ]
            }
    except Exception as e:
        print(f"키워드 새로고침 오류: {e}")
        import traceback
        traceback.print_exc()
        log_warning_sync("keyword", f"키워드 수집 실패, 기본 키워드 사용: {str(e)}")
        # 실패해도 기본 키워드 반환
        return {
            "success": True,
            "keywords": [
                {"keyword": "연말정산", "trend_score": 5, "category": "재테크", "source": "fallback"},
                {"keyword": "청년도약계좌", "trend_score": 4, "category": "재테크", "source": "fallback"},
                {"keyword": "실업급여", "trend_score": 4, "category": "생활", "source": "fallback"},
                {"keyword": "국민연금", "trend_score": 3, "category": "재테크", "source": "fallback"},
                {"keyword": "건강보험", "trend_score": 3, "category": "생활", "source": "fallback"},
            ]
        }


@router.get("/recent")
async def get_recent_keywords():
    """최근 발행된 키워드 목록"""
    try:
        from database.db_manager import DBManager

        db = DBManager()
        recent = db.get_recent_posts(limit=10)

        return {
            "keywords": [
                {
                    "keyword": post["keyword"],
                    "published_at": post["published_at"],
                    "url": post.get("url", "")
                }
                for post in recent
            ]
        }
    except Exception as e:
        return {"keywords": [], "error": str(e)}
