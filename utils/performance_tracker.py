"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
성과 추적 시스템 (4단계 + 5단계)
- GA4 API로 페이지 성과 수집
- Search Console API로 검색 성과 수집
- 우리 글 성과 DB 저장 + 패턴 학습에 반영
"""
import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# DB 경로
DB_PATH = Path(__file__).parent.parent / "data" / "blog_learning.db"

# GA4 설정
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")  # 예: "properties/123456789"
GA4_CREDENTIALS_PATH = os.environ.get("GA4_CREDENTIALS_PATH", "")

# Search Console 설정  
SC_SITE_URL = os.environ.get("SC_SITE_URL", "https://quickinfo.kr")
SC_CREDENTIALS_PATH = os.environ.get("SC_CREDENTIALS_PATH", "")


class PerformanceTracker:
    """GA4 + Search Console 성과 추적"""

    def __init__(self):
        self.db_path = DB_PATH
        self._ga4_client = None
        self._sc_client = None

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_ga4(self):
        """GA4 Data API 클라이언트 초기화"""
        if self._ga4_client:
            return self._ga4_client

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                GA4_CREDENTIALS_PATH,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            self._ga4_client = BetaAnalyticsDataClient(credentials=credentials)
            logger.info("GA4 client initialized")
            return self._ga4_client
        except Exception as e:
            logger.warning(f"GA4 init failed: {e}")
            return None

    def _init_sc(self):
        """Search Console API 클라이언트 초기화"""
        if self._sc_client:
            return self._sc_client

        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                SC_CREDENTIALS_PATH or GA4_CREDENTIALS_PATH,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
            )
            self._sc_client = build("searchconsole", "v1", credentials=credentials)
            logger.info("Search Console client initialized")
            return self._sc_client
        except Exception as e:
            logger.warning(f"Search Console init failed: {e}")
            return None

    def fetch_ga4_metrics(self, page_path: str, days: int = 30) -> Optional[Dict]:
        """GA4에서 페이지 성과 조회"""
        client = self._init_ga4()
        if not client or not GA4_PROPERTY_ID:
            return None

        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest, DateRange, Dimension, Metric, FilterExpression,
                Filter
            )

            request = RunReportRequest(
                property=GA4_PROPERTY_ID,
                date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate"),
                ],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="pagePath",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value=page_path
                        )
                    )
                )
            )

            response = client.run_report(request)

            for row in response.rows:
                return {
                    "pageviews": int(row.metric_values[0].value),
                    "avg_session_duration": float(row.metric_values[1].value),
                    "bounce_rate": float(row.metric_values[2].value),
                }

            return {"pageviews": 0, "avg_session_duration": 0, "bounce_rate": 0}

        except Exception as e:
            logger.warning(f"GA4 fetch failed for {page_path}: {e}")
            return None

    def fetch_sc_metrics(self, page_url: str, days: int = 30) -> Optional[Dict]:
        """Search Console에서 검색 성과 조회"""
        client = self._init_sc()
        if not client:
            return None

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            request = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": ["page"],
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "page",
                        "operator": "contains",
                        "expression": page_url
                    }]
                }],
                "rowLimit": 1
            }

            response = client.searchanalytics().query(
                siteUrl=SC_SITE_URL, body=request
            ).execute()

            rows = response.get("rows", [])
            if rows:
                return {
                    "impressions": int(rows[0].get("impressions", 0)),
                    "clicks": int(rows[0].get("clicks", 0)),
                    "position": float(rows[0].get("position", 0)),
                    "ctr": float(rows[0].get("ctr", 0)),
                }

            return {"impressions": 0, "clicks": 0, "position": 0, "ctr": 0}

        except Exception as e:
            logger.warning(f"SC fetch failed for {page_url}: {e}")
            return None

    def register_our_post(self, post_data: Dict) -> bool:
        """우리 글 등록 (발행 시 호출)"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO our_posts_performance
                    (post_id, url, keyword, category, title, length, heading_count,
                     image_count, tone, intro_pattern, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_data.get("post_id"),
                    post_data.get("url"),
                    post_data.get("keyword"),
                    post_data.get("category"),
                    post_data.get("title"),
                    post_data.get("length", 0),
                    post_data.get("heading_count", 0),
                    post_data.get("image_count", 0),
                    post_data.get("tone"),
                    post_data.get("intro_pattern"),
                    datetime.now().isoformat()
                ))
                conn.commit()
                logger.info(f"Registered our post: {post_data.get('title', '')[:50]}")
                return True
        except Exception as e:
            logger.error(f"Failed to register post: {e}")
            return False

    def update_post_performance(self, post_id: int = None, url: str = None, days: int = 30) -> bool:
        """특정 글의 성과 업데이트"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                # 글 정보 조회
                if post_id:
                    cursor.execute("SELECT url FROM our_posts_performance WHERE post_id = ?", (post_id,))
                elif url:
                    cursor.execute("SELECT url FROM our_posts_performance WHERE url = ?", (url,))
                else:
                    return False

                row = cursor.fetchone()
                if not row:
                    return False

                page_url = row[0]

                # GA4 성과
                ga4_data = self.fetch_ga4_metrics(page_url, days) or {}

                # Search Console 성과
                sc_data = self.fetch_sc_metrics(page_url, days) or {}

                # 성과 점수 계산
                performance_score = self._calc_performance_score(ga4_data, sc_data)

                # 업데이트
                cursor.execute("""
                    UPDATE our_posts_performance SET
                        pageviews = ?,
                        avg_time_on_page = ?,
                        bounce_rate = ?,
                        search_impressions = ?,
                        search_clicks = ?,
                        search_position = ?,
                        performance_score = ?,
                        last_measured = ?
                    WHERE url = ?
                """, (
                    ga4_data.get("pageviews", 0),
                    ga4_data.get("avg_session_duration", 0),
                    ga4_data.get("bounce_rate", 0),
                    sc_data.get("impressions", 0),
                    sc_data.get("clicks", 0),
                    sc_data.get("position", 0),
                    performance_score,
                    datetime.now().isoformat(),
                    page_url
                ))
                conn.commit()
                logger.info(f"Updated performance for {page_url}: score={performance_score}")
                return True

        except Exception as e:
            logger.error(f"Failed to update performance: {e}")
            return False

    def _calc_performance_score(self, ga4: Dict, sc: Dict) -> float:
        """성과 점수 계산 (0-100)"""
        score = 0

        # GA4 점수 (50점)
        pv = ga4.get("pageviews", 0)
        if pv >= 1000:
            score += 20
        elif pv >= 500:
            score += 15
        elif pv >= 100:
            score += 10
        elif pv >= 50:
            score += 5

        duration = ga4.get("avg_session_duration", 0)
        if duration >= 180:  # 3분 이상
            score += 15
        elif duration >= 120:
            score += 10
        elif duration >= 60:
            score += 5

        bounce = ga4.get("bounce_rate", 100)
        if bounce <= 40:
            score += 15
        elif bounce <= 60:
            score += 10
        elif bounce <= 80:
            score += 5

        # SC 점수 (50점)
        impressions = sc.get("impressions", 0)
        if impressions >= 5000:
            score += 15
        elif impressions >= 1000:
            score += 10
        elif impressions >= 100:
            score += 5

        clicks = sc.get("clicks", 0)
        if clicks >= 100:
            score += 15
        elif clicks >= 50:
            score += 10
        elif clicks >= 10:
            score += 5

        position = sc.get("position", 100)
        if position <= 3:
            score += 20
        elif position <= 10:
            score += 15
        elif position <= 20:
            score += 10
        elif position <= 50:
            score += 5

        return min(score, 100)

    def update_all_posts(self, days: int = 30) -> int:
        """모든 글 성과 업데이트"""
        updated = 0
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM our_posts_performance")
                urls = [row[0] for row in cursor.fetchall()]

            for url in urls:
                if self.update_post_performance(url=url, days=days):
                    updated += 1

            logger.info(f"Updated {updated}/{len(urls)} posts performance")
            return updated

        except Exception as e:
            logger.error(f"Failed to update all posts: {e}")
            return updated

    def get_high_performers(self, category: str = None, min_score: float = 60, limit: int = 10) -> List[Dict]:
        """고성과 글 목록 조회"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute("""
                        SELECT post_id, url, keyword, category, title, length, heading_count,
                               image_count, tone, intro_pattern, performance_score
                        FROM our_posts_performance
                        WHERE category = ? AND performance_score >= ?
                        ORDER BY performance_score DESC
                        LIMIT ?
                    """, (category, min_score, limit))
                else:
                    cursor.execute("""
                        SELECT post_id, url, keyword, category, title, length, heading_count,
                               image_count, tone, intro_pattern, performance_score
                        FROM our_posts_performance
                        WHERE performance_score >= ?
                        ORDER BY performance_score DESC
                        LIMIT ?
                    """, (min_score, limit))

                columns = ["post_id", "url", "keyword", "category", "title", "length",
                          "heading_count", "image_count", "tone", "intro_pattern", "performance_score"]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get high performers: {e}")
            return []

    def learn_from_performance(self, category: str) -> Optional[Dict]:
        """
        고성과 글에서 패턴 학습 → content_patterns 업데이트

        고성과 글(score>=60)의 구조적 특성을 학습
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                # 고성과 글 조회
                cursor.execute("""
                    SELECT length, heading_count, image_count, tone, intro_pattern,
                           performance_score
                    FROM our_posts_performance
                    WHERE category = ? AND performance_score >= 50
                    ORDER BY performance_score DESC
                    LIMIT 20
                """, (category,))

                rows = cursor.fetchall()
                if len(rows) < 3:
                    logger.info(f"Not enough performance data for {category} ({len(rows)} posts)")
                    return None

                # 가중 평균 계산 (성과 점수로 가중치)
                total_weight = sum(r[5] for r in rows)
                if total_weight == 0:
                    return None

                weighted_length = sum(r[0] * r[5] for r in rows if r[0]) / total_weight
                weighted_headings = sum(r[1] * r[5] for r in rows if r[1]) / total_weight
                weighted_images = sum(r[2] * r[5] for r in rows if r[2]) / total_weight

                from collections import Counter
                tones = [r[3] for r in rows if r[3]]
                intros = [r[4] for r in rows if r[4]]

                learned = {
                    "performance_avg_length": int(weighted_length),
                    "performance_avg_headings": int(weighted_headings),
                    "performance_avg_images": int(weighted_images),
                    "performance_dominant_tone": Counter(tones).most_common(1)[0][0] if tones else None,
                    "performance_dominant_intro": Counter(intros).most_common(1)[0][0] if intros else None,
                    "sample_count": len(rows),
                }

                logger.info(f"Learned from {len(rows)} high-performing posts in {category}")
                return learned

        except Exception as e:
            logger.error(f"Failed to learn from performance: {e}")
            return None


def get_enhanced_prompt_injection(category: str) -> str:
    """
    4단계: 강화된 프롬프트 주입

    - 학습 DB 패턴 + 성과 데이터 기반 추천 통합
    """
    from .blog_learner import BlogLearner

    learner = BlogLearner()
    tracker = PerformanceTracker()

    lines = []

    # 1. 학습 DB 패턴
    pattern = learner.get_category_pattern(category)
    if pattern and pattern.sample_count >= 3:
        intro_names = {
            "question": "질문형 (독자에게 질문으로 시작)",
            "statistic": "통계/수치형 (데이터로 시작)",
            "story": "스토리텔링형 (경험/사례로 시작)",
            "direct": "직접 설명형 (바로 본론)"
        }

        lines.append(f"\n[📚 {category} 카테고리 — 고성과 블로그 패턴]")
        lines.append(f"  (참조 블로그 {pattern.sample_count}개 분석)")
        lines.append(f"")
        lines.append(f"  ✅ 필수 요구사항:")
        lines.append(f"    - 글 길이: {pattern.avg_length}자 이상")
        lines.append(f"    - 소제목: {pattern.avg_headings}개 이상")
        lines.append(f"    - 이미지: {pattern.avg_images}개 ([IMAGE_N] 태그)")
        lines.append(f"    - 글 톤: {pattern.dominant_tone}")
        lines.append(f"    - 도입부: {intro_names.get(pattern.dominant_intro, pattern.dominant_intro)}")

        if pattern.use_table_ratio >= 0.3:
            lines.append(f"    - 표 사용 권장 ({int(pattern.use_table_ratio * 100)}%)")
        if pattern.use_list_ratio >= 0.5:
            lines.append(f"    - 리스트 사용 권장 ({int(pattern.use_list_ratio * 100)}%)")

        if pattern.common_keywords:
            lines.append(f"")
            lines.append(f"  🔑 반드시 포함할 키워드:")
            lines.append(f"    {', '.join(pattern.common_keywords[:12])}")

        if pattern.heading_patterns:
            lines.append(f"")
            lines.append(f"  📌 추천 소제목 패턴:")
            for i, h in enumerate(pattern.heading_patterns[:5], 1):
                lines.append(f"    {i}. {h[:40]}...")

    # 2. 우리 글 성과 데이터
    perf_data = tracker.learn_from_performance(category)
    if perf_data:
        lines.append(f"")
        lines.append(f"  📊 우리 블로그 고성과 글 패턴 (추가 참고):")
        lines.append(f"    - 평균 글 길이: {perf_data['performance_avg_length']}자")
        lines.append(f"    - 평균 소제목: {perf_data['performance_avg_headings']}개")
        lines.append(f"    - 평균 이미지: {perf_data['performance_avg_images']}개")

    # 3. 제목 패턴 가이드
    lines.append(f"")
    lines.append(f"  📝 제목 작성 가이드:")
    lines.append(f"    - 숫자 포함 (예: '5가지', '3단계')")
    lines.append(f"    - 구체적 대상 명시 (예: '직장인을 위한', '초보자 필수')")
    lines.append(f"    - 긴급성/희소성 (예: '꼭 알아야 할', '놓치면 손해')")
    lines.append(f"    - 30자 내외, 핵심 키워드 앞에 배치")

    lines.append(f"")

    return "\n".join(lines) if lines else ""


# CLI
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "update-all":
            tracker = PerformanceTracker()
            updated = tracker.update_all_posts(days=30)
            print(f"Updated {updated} posts")

        elif cmd == "high-performers":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            tracker = PerformanceTracker()
            posts = tracker.get_high_performers(category, min_score=50)
            for p in posts:
                print(f"  [{p['performance_score']:.0f}] {p['title'][:50]}")

        elif cmd == "prompt" and len(sys.argv) > 2:
            category = sys.argv[2]
            prompt = get_enhanced_prompt_injection(category)
            print(prompt)

        elif cmd == "learn" and len(sys.argv) > 2:
            category = sys.argv[2]
            tracker = PerformanceTracker()
            result = tracker.learn_from_performance(category)
            print(json.dumps(result, ensure_ascii=False, indent=2) if result else "No data")

    else:
        print("사용법:")
        print("  python performance_tracker.py update-all          # 모든 글 성과 업데이트")
        print("  python performance_tracker.py high-performers [카테고리]  # 고성과 글 조회")
        print("  python performance_tracker.py prompt <카테고리>   # 강화된 프롬프트")
        print("  python performance_tracker.py learn <카테고리>    # 성과 기반 학습")
