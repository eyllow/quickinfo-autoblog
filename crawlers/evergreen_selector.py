"""
에버그린 키워드 선정 모듈

시즌별 키워드 필터링, 트렌드 반영, 미발행 키워드 우선 선정
"""
import json
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "evergreen_keywords.json"
DB_PATH = PROJECT_ROOT / "database" / "blog_publisher.db"


class EvergreenSelector:
    """시즌 기반 에버그린 키워드 선정기"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """설정 파일 로드"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"에버그린 설정 로드 실패: {e}")
            return {"keywords": [], "season_keywords": {}, "detection_keywords": []}

    def get_current_season_keywords(self) -> List[str]:
        """현재 월에 맞는 시즌 키워드 반환"""
        current_month = str(datetime.now().month)
        season_keywords = self.config.get("season_keywords", {})
        return season_keywords.get(current_month, [])

    def get_recently_published_keywords(self, days: int = 7) -> List[str]:
        """
        최근 N일 내 발행된 에버그린 키워드 목록

        Args:
            days: 조회할 기간 (일)

        Returns:
            발행된 키워드 목록
        """
        if not DB_PATH.exists():
            return []

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()

            since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT DISTINCT keyword
                FROM published_posts
                WHERE date(created_at) >= ?
            """, (since_date,))

            keywords = [row[0] for row in cursor.fetchall()]
            conn.close()

            logger.info(f"최근 {days}일 발행 키워드: {len(keywords)}개")
            return keywords

        except Exception as e:
            logger.error(f"발행 키워드 조회 실패: {e}")
            return []

    def select_keyword(self, exclude_keywords: List[str] = None) -> str:
        """
        에버그린 키워드 선정

        선정 우선순위:
        1. 현재 시즌에 맞는 키워드
        2. priority가 high인 키워드
        3. 최근 발행되지 않은 키워드

        Args:
            exclude_keywords: 제외할 키워드 목록

        Returns:
            선정된 키워드
        """
        exclude_keywords = exclude_keywords or []

        # 최근 발행 키워드 추가 제외
        recently_published = self.get_recently_published_keywords(days=7)
        all_excluded = set(exclude_keywords + recently_published)

        current_month = datetime.now().month
        season_hints = self.get_current_season_keywords()

        all_keywords = self.config.get("keywords", [])

        # 시즌 매칭 + 우선순위별 분류
        high_priority_season = []
        medium_priority_season = []
        low_priority_season = []
        other_keywords = []

        for kw_info in all_keywords:
            # 문자열이면 딕셔너리로 변환
            if isinstance(kw_info, str):
                kw_info = {"keyword": kw_info, "seasons": list(range(1, 13)), "priority": "medium"}

            keyword = kw_info.get("keyword", "")
            seasons = kw_info.get("seasons", list(range(1, 13)))
            priority = kw_info.get("priority", "medium")

            # 제외 키워드 건너뛰기
            if keyword in all_excluded:
                continue

            # 시즌 확인
            is_in_season = current_month in seasons

            # 시즌 힌트 매칭 확인
            is_season_hint_match = any(hint in keyword for hint in season_hints)

            if is_in_season or is_season_hint_match:
                if priority == "high":
                    high_priority_season.append(keyword)
                elif priority == "medium":
                    medium_priority_season.append(keyword)
                else:
                    low_priority_season.append(keyword)
            else:
                other_keywords.append(keyword)

        # 우선순위대로 선택
        if high_priority_season:
            selected = random.choice(high_priority_season)
            logger.info(f"High priority 시즌 키워드 선정: {selected}")
            return selected
        elif medium_priority_season:
            selected = random.choice(medium_priority_season)
            logger.info(f"Medium priority 시즌 키워드 선정: {selected}")
            return selected
        elif low_priority_season:
            selected = random.choice(low_priority_season)
            logger.info(f"Low priority 시즌 키워드 선정: {selected}")
            return selected
        elif other_keywords:
            selected = random.choice(other_keywords)
            logger.info(f"비시즌 키워드 선정: {selected}")
            return selected
        else:
            # 모든 키워드 발행됨 - 전체에서 랜덤 (제외 무시)
            all_kw_list = [
                kw if isinstance(kw, str) else kw.get("keyword", "")
                for kw in all_keywords
            ]
            selected = random.choice(all_kw_list) if all_kw_list else "신용점수 올리는 방법"
            logger.info(f"폴백 키워드 선정: {selected}")
            return selected

    def get_trending_evergreen(self) -> Optional[str]:
        """
        Google Trends에서 상승 중인 에버그린 키워드 찾기

        detection_keywords와 매칭되는 트렌드 키워드 반환

        Returns:
            매칭된 트렌드 키워드 또는 None
        """
        try:
            from crawlers.google_trends import get_trending_keywords_simple

            detection_keywords = self.config.get("detection_keywords", [])
            trending = get_trending_keywords_simple()

            for trend_kw in trending:
                keyword = trend_kw if isinstance(trend_kw, str) else trend_kw.get("keyword", "")

                # 에버그린 감지 키워드와 매칭되면 반환
                for detect in detection_keywords:
                    if detect in keyword:
                        logger.info(f"트렌드 에버그린 발견: {keyword} (매칭: {detect})")
                        return keyword

            return None

        except Exception as e:
            logger.warning(f"트렌드 에버그린 조회 실패: {e}")
            return None

    def get_keyword_for_publish(self) -> tuple:
        """
        발행용 에버그린 키워드 선정 (통합 메서드)

        Returns:
            (키워드, 선정 사유) 튜플
        """
        # 1. 트렌드 중 에버그린 키워드 확인
        trending_evergreen = self.get_trending_evergreen()
        if trending_evergreen:
            return trending_evergreen, "트렌드 매칭"

        # 2. 시즌 기반 선정
        keyword = self.select_keyword()
        return keyword, "시즌 기반"


def get_evergreen_keyword() -> str:
    """
    에버그린 키워드 선정 편의 함수

    Returns:
        선정된 키워드
    """
    selector = EvergreenSelector()
    keyword, reason = selector.get_keyword_for_publish()
    logger.info(f"에버그린 키워드 선정: {keyword} ({reason})")
    return keyword


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 에버그린 키워드 선정 테스트 ===\n")

    selector = EvergreenSelector()

    print(f"현재 월: {datetime.now().month}월")
    print(f"시즌 키워드: {selector.get_current_season_keywords()}")
    print(f"최근 발행 키워드: {selector.get_recently_published_keywords()}")
    print()

    # 5번 선정 테스트
    for i in range(5):
        keyword, reason = selector.get_keyword_for_publish()
        print(f"테스트 {i+1}: {keyword} ({reason})")

    print()
    print(f"트렌드 에버그린: {selector.get_trending_evergreen()}")
