"""성과 학습 시스템

WordPress REST API로 각 글의 조회수/트래픽 데이터 수집하고 분석:
- 고성과 글의 패턴 분석 (키워드, 카테고리, 템플릿, 글자수, 이미지수)
- 저성과 글의 공통 특징 분석
- 다음 글 생성 시 고성과 패턴 우선 적용
- 성과 데이터를 DB에 저장하고 주기적으로 분석
- 트렌드 키워드 선택 시 과거 성과 데이터 반영
"""
import logging
import sqlite3
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import requests

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)

# 데이터베이스 경로
PERFORMANCE_DB_PATH = Path(settings.database_path).parent / "performance_data.db"


@dataclass
class PostPerformance:
    """포스트 성과 데이터"""
    wp_post_id: int
    keyword: str
    title: str
    category: str
    views: int = 0
    comments: int = 0
    engagement_score: float = 0.0
    char_count: int = 0
    image_count: int = 0
    heading_count: int = 0
    published_at: str = ""
    collected_at: str = ""

    def to_dict(self) -> Dict:
        return {
            "wp_post_id": self.wp_post_id,
            "keyword": self.keyword,
            "title": self.title,
            "category": self.category,
            "views": self.views,
            "comments": self.comments,
            "engagement_score": round(self.engagement_score, 2),
            "char_count": self.char_count,
            "image_count": self.image_count,
            "heading_count": self.heading_count,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
        }


@dataclass
class PerformancePattern:
    """성과 패턴 분석 결과"""
    high_performing_categories: List[str] = field(default_factory=list)
    high_performing_keywords: List[str] = field(default_factory=list)
    optimal_char_count: Tuple[int, int] = (3000, 4000)
    optimal_image_count: Tuple[int, int] = (2, 4)
    optimal_heading_count: Tuple[int, int] = (5, 8)
    best_publish_hours: List[int] = field(default_factory=list)
    low_performing_patterns: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "high_performing_categories": self.high_performing_categories,
            "high_performing_keywords": self.high_performing_keywords,
            "optimal_char_count": self.optimal_char_count,
            "optimal_image_count": self.optimal_image_count,
            "optimal_heading_count": self.optimal_heading_count,
            "best_publish_hours": self.best_publish_hours,
            "low_performing_patterns": self.low_performing_patterns,
        }


class PerformanceLearner:
    """WordPress 성과 학습 시스템"""

    def __init__(self):
        self.wp_url = settings.wp_url.rstrip('/')
        self.api_base = f"{self.wp_url}/wp-json/wp/v2"

        # Basic Auth 토큰
        credentials = f"{settings.wp_user}:{settings.wp_app_password}"
        self.auth_token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth_token}",
            "Content-Type": "application/json",
        }

        self._init_db()

    def _init_db(self):
        """성과 데이터 DB 초기화"""
        try:
            PERFORMANCE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            # 포스트 성과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wp_post_id INTEGER UNIQUE NOT NULL,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT,
                    views INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0,
                    char_count INTEGER DEFAULT 0,
                    image_count INTEGER DEFAULT 0,
                    heading_count INTEGER DEFAULT 0,
                    published_at DATETIME,
                    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 성과 히스토리 테이블 (일별 조회수 추적)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wp_post_id INTEGER NOT NULL,
                    views INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    collected_at DATE NOT NULL,
                    UNIQUE(wp_post_id, collected_at)
                )
            """)

            # 분석 결과 캐시 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_keyword
                ON post_performance(keyword)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_category
                ON post_performance(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_views
                ON post_performance(views DESC)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Performance DB initialized at {PERFORMANCE_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize performance DB: {e}")

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """WordPress API 요청"""
        try:
            url = f"{self.api_base}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"WP API request failed: {e}")
            return None

    def collect_post_performance(self, wp_post_id: int) -> Optional[PostPerformance]:
        """
        단일 포스트의 성과 데이터 수집

        Args:
            wp_post_id: WordPress 포스트 ID

        Returns:
            PostPerformance 객체 또는 None
        """
        try:
            # 포스트 기본 정보
            post_data = self._make_request(f"posts/{wp_post_id}")
            if not post_data:
                return None

            # 조회수 (WP-Statistics 또는 Jetpack 플러그인 필요)
            views = self._get_post_views(wp_post_id)

            # 댓글 수
            comments = post_data.get("comment_count", 0)
            if isinstance(comments, str):
                comments = int(comments) if comments.isdigit() else 0

            # 콘텐츠 분석
            content = post_data.get("content", {}).get("rendered", "")
            import re
            text_only = re.sub(r'<[^>]+>', '', content)
            char_count = len(text_only)
            image_count = len(re.findall(r'<(?:img|figure)[^>]*>', content, re.IGNORECASE))
            heading_count = len(re.findall(r'<h[234][^>]*>', content, re.IGNORECASE))

            # 카테고리
            categories = post_data.get("categories", [])
            category = self._get_category_name(categories[0]) if categories else "미분류"

            # 발행일
            published_at = post_data.get("date", "")

            # Engagement Score 계산
            engagement_score = self._calculate_engagement(views, comments, char_count)

            performance = PostPerformance(
                wp_post_id=wp_post_id,
                keyword=self._extract_keyword_from_title(post_data.get("title", {}).get("rendered", "")),
                title=post_data.get("title", {}).get("rendered", ""),
                category=category,
                views=views,
                comments=comments,
                engagement_score=engagement_score,
                char_count=char_count,
                image_count=image_count,
                heading_count=heading_count,
                published_at=published_at,
                collected_at=datetime.now().isoformat(),
            )

            # DB 저장
            self._save_performance(performance)

            return performance

        except Exception as e:
            logger.error(f"Failed to collect performance for post {wp_post_id}: {e}")
            return None

    def _get_post_views(self, wp_post_id: int) -> int:
        """포스트 조회수 가져오기 (플러그인 의존)"""
        try:
            # WP-Statistics 플러그인 API
            stats_data = self._make_request(
                "wp-statistics/v2/hits",
                params={"post_id": wp_post_id}
            )
            if stats_data and "hits" in stats_data:
                return int(stats_data["hits"])

            # Jetpack 통계 (대안)
            jetpack_data = self._make_request(
                f"jetpack/v4/site/stats/post/{wp_post_id}"
            )
            if jetpack_data and "views" in jetpack_data:
                return int(jetpack_data["views"])

            # Post Views Counter 플러그인 (대안)
            pvc_data = self._make_request(f"posts/{wp_post_id}")
            if pvc_data and "post_views_count" in pvc_data:
                return int(pvc_data["post_views_count"])

        except Exception as e:
            logger.debug(f"Views fetch failed for {wp_post_id}: {e}")

        return 0

    def _get_category_name(self, category_id: int) -> str:
        """카테고리 ID로 이름 가져오기"""
        try:
            cat_data = self._make_request(f"categories/{category_id}")
            if cat_data:
                return cat_data.get("name", "미분류")
        except Exception:
            pass
        return "미분류"

    def _extract_keyword_from_title(self, title: str) -> str:
        """제목에서 주요 키워드 추출"""
        import re
        # HTML 엔티티 제거
        title = re.sub(r'&[^;]+;', '', title)
        # 특수문자 제거
        title = re.sub(r'[^\w\s가-힣]', ' ', title)
        # 첫 번째 의미있는 단어 추출
        words = [w for w in title.split() if len(w) >= 2]
        return words[0] if words else title[:20]

    def _calculate_engagement(self, views: int, comments: int, char_count: int) -> float:
        """Engagement Score 계산"""
        # 조회수 기반 (최대 60점)
        view_score = min(60, views / 100 * 10)

        # 댓글 기반 (최대 30점)
        comment_score = min(30, comments * 5)

        # 콘텐츠 길이 보너스 (최대 10점)
        if 3000 <= char_count <= 5000:
            length_bonus = 10
        elif char_count > 5000:
            length_bonus = 5
        else:
            length_bonus = char_count / 300

        return view_score + comment_score + length_bonus

    def _save_performance(self, perf: PostPerformance):
        """성과 데이터 DB 저장"""
        try:
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            # UPSERT
            cursor.execute("""
                INSERT INTO post_performance (
                    wp_post_id, keyword, title, category, views, comments,
                    engagement_score, char_count, image_count, heading_count,
                    published_at, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(wp_post_id) DO UPDATE SET
                    views = excluded.views,
                    comments = excluded.comments,
                    engagement_score = excluded.engagement_score,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                perf.wp_post_id, perf.keyword, perf.title, perf.category,
                perf.views, perf.comments, perf.engagement_score,
                perf.char_count, perf.image_count, perf.heading_count,
                perf.published_at, perf.collected_at
            ))

            # 히스토리 저장
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT OR REPLACE INTO performance_history
                (wp_post_id, views, comments, collected_at)
                VALUES (?, ?, ?, ?)
            """, (perf.wp_post_id, perf.views, perf.comments, today))

            conn.commit()
            conn.close()
            logger.info(f"Performance saved for post {perf.wp_post_id}: views={perf.views}, score={perf.engagement_score:.1f}")
        except Exception as e:
            logger.error(f"Failed to save performance: {e}")

    def collect_all_recent_posts(self, days: int = 30) -> List[PostPerformance]:
        """
        최근 N일 내 발행된 모든 포스트의 성과 수집

        Args:
            days: 조회 기간

        Returns:
            PostPerformance 리스트
        """
        try:
            after_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

            posts = self._make_request(
                "posts",
                params={
                    "per_page": 100,
                    "status": "publish",
                    "after": after_date,
                    "_fields": "id"
                }
            )

            if not posts:
                return []

            results = []
            for post in posts:
                perf = self.collect_post_performance(post["id"])
                if perf:
                    results.append(perf)

            logger.info(f"Collected performance for {len(results)} posts")
            return results

        except Exception as e:
            logger.error(f"Failed to collect all posts: {e}")
            return []

    def analyze_performance_patterns(self, days: int = 30) -> PerformancePattern:
        """
        성과 패턴 분석

        Args:
            days: 분석 기간

        Returns:
            PerformancePattern 객체
        """
        try:
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # 고성과 카테고리 (상위 5개)
            cursor.execute("""
                SELECT category, AVG(engagement_score) as avg_score
                FROM post_performance
                WHERE published_at >= ?
                GROUP BY category
                ORDER BY avg_score DESC
                LIMIT 5
            """, (cutoff_date,))
            high_categories = [row[0] for row in cursor.fetchall()]

            # 고성과 키워드 패턴 (상위 10개)
            cursor.execute("""
                SELECT keyword, engagement_score
                FROM post_performance
                WHERE published_at >= ?
                ORDER BY engagement_score DESC
                LIMIT 10
            """, (cutoff_date,))
            high_keywords = [row[0] for row in cursor.fetchall()]

            # 최적 글자 수 범위
            cursor.execute("""
                SELECT char_count, engagement_score
                FROM post_performance
                WHERE published_at >= ? AND engagement_score > 50
                ORDER BY engagement_score DESC
                LIMIT 20
            """, (cutoff_date,))
            high_char_counts = [row[0] for row in cursor.fetchall()]
            if high_char_counts:
                optimal_char = (
                    min(high_char_counts),
                    max(high_char_counts)
                )
            else:
                optimal_char = (3000, 4000)

            # 최적 이미지 수
            cursor.execute("""
                SELECT image_count, AVG(engagement_score) as avg_score
                FROM post_performance
                WHERE published_at >= ?
                GROUP BY image_count
                ORDER BY avg_score DESC
                LIMIT 3
            """, (cutoff_date,))
            optimal_images = [row[0] for row in cursor.fetchall()[:3]]
            optimal_image_range = (min(optimal_images), max(optimal_images)) if optimal_images else (2, 4)

            # 최적 소제목 수
            cursor.execute("""
                SELECT heading_count, AVG(engagement_score) as avg_score
                FROM post_performance
                WHERE published_at >= ?
                GROUP BY heading_count
                ORDER BY avg_score DESC
                LIMIT 3
            """, (cutoff_date,))
            optimal_headings = [row[0] for row in cursor.fetchall()[:3]]
            optimal_heading_range = (min(optimal_headings), max(optimal_headings)) if optimal_headings else (5, 8)

            # 저성과 패턴 분석
            cursor.execute("""
                SELECT category, AVG(char_count), AVG(image_count), AVG(heading_count)
                FROM post_performance
                WHERE published_at >= ? AND engagement_score < 30
                GROUP BY category
            """, (cutoff_date,))
            low_patterns = {}
            for row in cursor.fetchall():
                low_patterns[row[0]] = {
                    "avg_char_count": int(row[1]) if row[1] else 0,
                    "avg_image_count": int(row[2]) if row[2] else 0,
                    "avg_heading_count": int(row[3]) if row[3] else 0,
                }

            conn.close()

            pattern = PerformancePattern(
                high_performing_categories=high_categories,
                high_performing_keywords=high_keywords,
                optimal_char_count=optimal_char,
                optimal_image_count=optimal_image_range,
                optimal_heading_count=optimal_heading_range,
                low_performing_patterns=low_patterns,
            )

            logger.info(f"Performance pattern analysis completed: "
                       f"top categories={high_categories[:3]}, "
                       f"optimal chars={optimal_char}")

            return pattern

        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return PerformancePattern()

    def get_keyword_recommendations(self, candidate_keywords: List[str]) -> List[Tuple[str, float]]:
        """
        후보 키워드에 대해 과거 성과 기반 추천 점수 계산

        Args:
            candidate_keywords: 후보 키워드 리스트

        Returns:
            [(keyword, score), ...] 점수 내림차순 정렬
        """
        try:
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            scored_keywords = []
            for keyword in candidate_keywords:
                # 유사 키워드 성과 조회
                cursor.execute("""
                    SELECT AVG(engagement_score), COUNT(*)
                    FROM post_performance
                    WHERE keyword LIKE ?
                """, (f"%{keyword}%",))

                row = cursor.fetchone()
                avg_score = row[0] if row[0] else 50  # 기본값 50
                count = row[1] if row[1] else 0

                # 신규 키워드 보너스 (기존 발행 적으면 점수 up)
                novelty_bonus = max(0, 20 - count * 5)

                final_score = avg_score + novelty_bonus
                scored_keywords.append((keyword, final_score))

            conn.close()

            # 점수 내림차순 정렬
            scored_keywords.sort(key=lambda x: x[1], reverse=True)
            return scored_keywords

        except Exception as e:
            logger.error(f"Failed to get keyword recommendations: {e}")
            return [(kw, 50.0) for kw in candidate_keywords]

    def get_content_recommendations(self, category: str) -> Dict:
        """
        카테고리 기반 콘텐츠 구성 추천

        Args:
            category: 카테고리 이름

        Returns:
            추천 설정 딕셔너리
        """
        try:
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            # 해당 카테고리의 고성과 글 평균값
            cursor.execute("""
                SELECT
                    AVG(char_count),
                    AVG(image_count),
                    AVG(heading_count)
                FROM post_performance
                WHERE category = ? AND engagement_score > 50
            """, (category,))

            row = cursor.fetchone()
            conn.close()

            if row and row[0]:
                return {
                    "recommended_char_count": int(row[0]),
                    "recommended_image_count": int(row[1]) if row[1] else 3,
                    "recommended_heading_count": int(row[2]) if row[2] else 6,
                    "based_on": "performance_data"
                }

            # 기본값
            return {
                "recommended_char_count": 3500,
                "recommended_image_count": 3,
                "recommended_heading_count": 6,
                "based_on": "default"
            }

        except Exception as e:
            logger.error(f"Failed to get content recommendations: {e}")
            return {
                "recommended_char_count": 3500,
                "recommended_image_count": 3,
                "recommended_heading_count": 6,
                "based_on": "error_fallback"
            }

    def get_performance_summary(self, days: int = 30) -> Dict:
        """성과 요약 통계"""
        try:
            conn = sqlite3.connect(str(PERFORMANCE_DB_PATH))
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_posts,
                    AVG(views) as avg_views,
                    AVG(comments) as avg_comments,
                    AVG(engagement_score) as avg_score,
                    MAX(views) as max_views,
                    MAX(engagement_score) as max_score
                FROM post_performance
                WHERE published_at >= ?
            """, (cutoff_date,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "total_posts": row[0],
                    "avg_views": round(row[1], 1) if row[1] else 0,
                    "avg_comments": round(row[2], 1) if row[2] else 0,
                    "avg_engagement_score": round(row[3], 1) if row[3] else 0,
                    "max_views": row[4] if row[4] else 0,
                    "max_engagement_score": round(row[5], 1) if row[5] else 0,
                    "period_days": days,
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}


# 싱글톤 인스턴스
performance_learner = PerformanceLearner()


def collect_performance_data(days: int = 30) -> List[PostPerformance]:
    """성과 데이터 수집 (편의 함수)"""
    return performance_learner.collect_all_recent_posts(days)


def get_performance_patterns(days: int = 30) -> PerformancePattern:
    """성과 패턴 분석 (편의 함수)"""
    return performance_learner.analyze_performance_patterns(days)


def get_keyword_scores(keywords: List[str]) -> List[Tuple[str, float]]:
    """키워드 점수 계산 (편의 함수)"""
    return performance_learner.get_keyword_recommendations(keywords)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    learner = PerformanceLearner()

    print("=== 성과 학습 시스템 테스트 ===\n")

    # 성과 데이터 수집 (실제 WP 연동 필요)
    print("1. 최근 30일 성과 데이터 수집 중...")
    # results = learner.collect_all_recent_posts(30)
    # print(f"   수집된 포스트: {len(results)}개")

    print("\n2. 성과 패턴 분석...")
    patterns = learner.analyze_performance_patterns(30)
    print(f"   고성과 카테고리: {patterns.high_performing_categories}")
    print(f"   최적 글자 수: {patterns.optimal_char_count}")
    print(f"   최적 이미지 수: {patterns.optimal_image_count}")

    print("\n3. 키워드 추천 테스트...")
    test_keywords = ["연말정산", "비트코인", "다이어트", "아이폰"]
    recommendations = learner.get_keyword_recommendations(test_keywords)
    for kw, score in recommendations:
        print(f"   - {kw}: {score:.1f}점")

    print("\n4. 카테고리별 콘텐츠 추천...")
    rec = learner.get_content_recommendations("재테크")
    print(f"   재테크: 글자수 {rec['recommended_char_count']}, "
          f"이미지 {rec['recommended_image_count']}개, "
          f"소제목 {rec['recommended_heading_count']}개")

    print("\n5. 성과 요약...")
    summary = learner.get_performance_summary(30)
    print(f"   총 포스트: {summary.get('total_posts', 0)}개")
    print(f"   평균 조회수: {summary.get('avg_views', 0)}")
    print(f"   평균 Engagement: {summary.get('avg_engagement_score', 0)}")
