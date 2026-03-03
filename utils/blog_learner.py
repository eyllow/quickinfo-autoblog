"""
블로그 학습 시스템 (3단계)
- reference_blogs: 수집된 참조 블로그 데이터
- content_patterns: 카테고리별 최적 패턴
- 발행 시 학습된 패턴을 프롬프트에 자동 주입
"""
import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# DB 경로
DB_PATH = Path(__file__).parent.parent / "data" / "blog_learning.db"


@dataclass
class LearnedPattern:
    """카테고리별 학습된 패턴"""
    category: str
    avg_length: int
    avg_headings: int
    avg_images: int
    dominant_tone: str  # 리스트형, 설명형, 비교형, 스토리텔링
    dominant_intro: str  # question, statistic, story, direct
    use_table_ratio: float  # 0.0 ~ 1.0
    use_list_ratio: float
    common_keywords: List[str]
    heading_patterns: List[str]  # 자주 쓰이는 소제목 패턴
    sample_count: int
    last_updated: str


class BlogLearner:
    """블로그 학습 DB 관리"""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """테이블 초기화"""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # 1. 참조 블로그 데이터
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reference_blogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    keyword TEXT,
                    category TEXT,
                    title TEXT,
                    length INTEGER,
                    heading_count INTEGER,
                    image_count INTEGER,
                    tone TEXT,
                    intro_pattern TEXT,
                    has_table INTEGER,
                    has_list INTEGER,
                    quality_score REAL,
                    headings TEXT,  -- JSON array
                    subtopics TEXT,  -- JSON array
                    numbers_data TEXT,  -- JSON array
                    source TEXT,  -- naver, tistory, brunch
                    crawled_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. 카테고리별 학습 패턴
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT UNIQUE,
                    avg_length INTEGER,
                    avg_headings INTEGER,
                    avg_images INTEGER,
                    dominant_tone TEXT,
                    dominant_intro TEXT,
                    use_table_ratio REAL,
                    use_list_ratio REAL,
                    common_keywords TEXT,  -- JSON array
                    heading_patterns TEXT,  -- JSON array
                    sample_count INTEGER,
                    last_updated TEXT
                )
            """)

            # 3. 우리 글 성과 추적 (GA4/SC 연동용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS our_posts_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    url TEXT UNIQUE,
                    keyword TEXT,
                    category TEXT,
                    title TEXT,
                    length INTEGER,
                    heading_count INTEGER,
                    image_count INTEGER,
                    tone TEXT,
                    intro_pattern TEXT,
                    published_at TEXT,
                    -- 성과 지표 (나중에 업데이트)
                    pageviews INTEGER DEFAULT 0,
                    avg_time_on_page REAL DEFAULT 0,
                    bounce_rate REAL DEFAULT 0,
                    search_impressions INTEGER DEFAULT 0,
                    search_clicks INTEGER DEFAULT 0,
                    search_position REAL DEFAULT 0,
                    performance_score REAL DEFAULT 0,
                    last_measured TEXT
                )
            """)

            # 인덱스
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_category ON reference_blogs(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_keyword ON reference_blogs(keyword)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_our_category ON our_posts_performance(category)")

            conn.commit()
            logger.info(f"BlogLearner DB initialized: {self.db_path}")

    def save_reference_blog(self, data: Dict) -> bool:
        """참조 블로그 저장 (중복 시 업데이트)"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO reference_blogs 
                    (url, keyword, category, title, length, heading_count, image_count,
                     tone, intro_pattern, has_table, has_list, quality_score,
                     headings, subtopics, numbers_data, source, crawled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get("url"),
                    data.get("keyword"),
                    data.get("category", "기타"),
                    data.get("title"),
                    data.get("length", 0),
                    len(data.get("headings", [])),
                    data.get("image_count", 0),
                    data.get("tone"),
                    data.get("intro_pattern"),
                    1 if data.get("has_table") else 0,
                    1 if data.get("has_list") else 0,
                    data.get("quality_score", 0),
                    json.dumps(data.get("headings", []), ensure_ascii=False),
                    json.dumps(data.get("subtopics", []), ensure_ascii=False),
                    json.dumps(data.get("numbers_data", []), ensure_ascii=False),
                    data.get("source", "unknown"),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save reference blog: {e}")
            return False

    def update_category_patterns(self, category: str) -> Optional[LearnedPattern]:
        """해당 카테고리의 참조 블로그들을 분석해서 패턴 업데이트"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()

                # 해당 카테고리 참조 블로그 조회 (최근 90일, 품질 30점 이상)
                cursor.execute("""
                    SELECT length, heading_count, image_count, tone, intro_pattern,
                           has_table, has_list, headings, subtopics
                    FROM reference_blogs
                    WHERE category = ?
                      AND crawled_at >= datetime('now', '-90 days')
                      AND quality_score >= 30
                    ORDER BY quality_score DESC
                    LIMIT 50
                """, (category,))

                rows = cursor.fetchall()
                if not rows:
                    return None

                # 통계 계산
                lengths = [r[0] for r in rows if r[0]]
                headings = [r[1] for r in rows if r[1]]
                images = [r[2] for r in rows if r[2]]
                tones = [r[3] for r in rows if r[3]]
                intros = [r[4] for r in rows if r[4]]
                tables = sum(1 for r in rows if r[5])
                lists = sum(1 for r in rows if r[6])

                # 공통 키워드 추출
                all_subtopics = []
                all_headings = []
                for r in rows:
                    if r[7]:
                        all_headings.extend(json.loads(r[7]))
                    if r[8]:
                        all_subtopics.extend(json.loads(r[8]))

                from collections import Counter
                keyword_freq = Counter(all_subtopics)
                heading_freq = Counter(all_headings)

                # 패턴 생성
                pattern = LearnedPattern(
                    category=category,
                    avg_length=sum(lengths) // len(lengths) if lengths else 3000,
                    avg_headings=sum(headings) // len(headings) if headings else 6,
                    avg_images=sum(images) // len(images) if images else 3,
                    dominant_tone=Counter(tones).most_common(1)[0][0] if tones else "설명형",
                    dominant_intro=Counter(intros).most_common(1)[0][0] if intros else "direct",
                    use_table_ratio=round(tables / len(rows), 2),
                    use_list_ratio=round(lists / len(rows), 2),
                    common_keywords=[k for k, _ in keyword_freq.most_common(15)],
                    heading_patterns=[h for h, _ in heading_freq.most_common(10)],
                    sample_count=len(rows),
                    last_updated=datetime.now().isoformat()
                )

                # DB 저장
                cursor.execute("""
                    INSERT OR REPLACE INTO content_patterns
                    (category, avg_length, avg_headings, avg_images, dominant_tone,
                     dominant_intro, use_table_ratio, use_list_ratio, common_keywords,
                     heading_patterns, sample_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.category, pattern.avg_length, pattern.avg_headings,
                    pattern.avg_images, pattern.dominant_tone, pattern.dominant_intro,
                    pattern.use_table_ratio, pattern.use_list_ratio,
                    json.dumps(pattern.common_keywords, ensure_ascii=False),
                    json.dumps(pattern.heading_patterns, ensure_ascii=False),
                    pattern.sample_count, pattern.last_updated
                ))
                conn.commit()

                logger.info(f"Updated pattern for '{category}': {pattern.sample_count} samples")
                return pattern

        except Exception as e:
            logger.error(f"Failed to update category patterns: {e}")
            return None

    def get_category_pattern(self, category: str) -> Optional[LearnedPattern]:
        """카테고리별 학습 패턴 조회"""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT category, avg_length, avg_headings, avg_images, dominant_tone,
                           dominant_intro, use_table_ratio, use_list_ratio, common_keywords,
                           heading_patterns, sample_count, last_updated
                    FROM content_patterns
                    WHERE category = ?
                """, (category,))
                row = cursor.fetchone()
                if not row:
                    return None

                return LearnedPattern(
                    category=row[0],
                    avg_length=row[1],
                    avg_headings=row[2],
                    avg_images=row[3],
                    dominant_tone=row[4],
                    dominant_intro=row[5],
                    use_table_ratio=row[6],
                    use_list_ratio=row[7],
                    common_keywords=json.loads(row[8]) if row[8] else [],
                    heading_patterns=json.loads(row[9]) if row[9] else [],
                    sample_count=row[10],
                    last_updated=row[11]
                )
        except Exception as e:
            logger.error(f"Failed to get category pattern: {e}")
            return None

    def get_prompt_injection(self, category: str) -> str:
        """콘텐츠 생성 프롬프트에 주입할 학습 패턴 텍스트"""
        pattern = self.get_category_pattern(category)
        if not pattern or pattern.sample_count < 3:
            return ""

        intro_names = {
            "question": "질문형 (독자에게 질문으로 시작)",
            "statistic": "통계/수치형 (데이터로 시작)",
            "story": "스토리텔링형 (경험/사례로 시작)",
            "direct": "직접 설명형 (바로 본론)"
        }

        lines = [
            f"\n[📚 {category} 카테고리 학습 패턴 — 반드시 준수]",
            f"  (고성과 블로그 {pattern.sample_count}개 분석 결과)",
            f"",
            f"  📏 글 길이: {pattern.avg_length}자 이상 (평균 기준)",
            f"  📑 소제목: {pattern.avg_headings}개 이상",
            f"  🖼️ 이미지: {pattern.avg_images}개 삽입 ([IMAGE_N] 태그 사용)",
            f"  📝 글 톤: {pattern.dominant_tone}",
            f"  🎬 도입부: {intro_names.get(pattern.dominant_intro, pattern.dominant_intro)}",
        ]

        if pattern.use_table_ratio >= 0.3:
            lines.append(f"  📊 표 사용 권장 ({int(pattern.use_table_ratio * 100)}% 블로그가 표 사용)")
        if pattern.use_list_ratio >= 0.5:
            lines.append(f"  📋 리스트 사용 권장 ({int(pattern.use_list_ratio * 100)}% 블로그가 리스트 사용)")

        if pattern.common_keywords:
            lines.append(f"  🔑 자주 사용되는 키워드: {', '.join(pattern.common_keywords[:10])}")

        if pattern.heading_patterns:
            lines.append(f"  📌 인기 소제목 패턴: {', '.join(pattern.heading_patterns[:5])}")

        lines.append("")
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """학습 DB 통계"""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM reference_blogs")
            total_refs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM content_patterns")
            total_patterns = cursor.fetchone()[0]

            cursor.execute("SELECT category, COUNT(*) FROM reference_blogs GROUP BY category")
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_reference_blogs": total_refs,
                "total_patterns": total_patterns,
                "by_category": by_category
            }


def crawl_and_learn(keywords_by_category: Dict[str, List[str]], count_per_keyword: int = 5):
    """
    카테고리별 키워드로 블로그 크롤링 + 학습 DB 저장

    Args:
        keywords_by_category: {"재테크": ["연말정산", "청년도약"], ...}
        count_per_keyword: 키워드당 크롤링할 블로그 수
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from crawlers.blog_reference import BlogReferenceCrawler

    crawler = BlogReferenceCrawler()
    learner = BlogLearner()

    total_saved = 0

    for category, keywords in keywords_by_category.items():
        logger.info(f"\n=== {category} 카테고리 크롤링 ===")

        for keyword in keywords:
            try:
                result = crawler.get_detailed_analysis(keyword, count=count_per_keyword)
                blogs = result.get("blogs", [])

                for blog in blogs:
                    blog["keyword"] = keyword
                    blog["category"] = category
                    if learner.save_reference_blog(blog):
                        total_saved += 1

                logger.info(f"  '{keyword}': {len(blogs)}개 저장")

            except Exception as e:
                logger.error(f"  '{keyword}' 크롤링 실패: {e}")

        # 카테고리 패턴 업데이트
        learner.update_category_patterns(category)

    logger.info(f"\n✅ 크롤링 완료: 총 {total_saved}개 블로그 저장")
    return total_saved


# CLI
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if len(sys.argv) > 1 and sys.argv[1] == "crawl":
        # 기본 카테고리 + 키워드
        default_keywords = {
            "재테크": ["연말정산", "청년도약계좌", "근로장려금", "주택청약"],
            "건강": ["면역력", "수면", "다이어트", "영양제"],
            "생활정보": ["이사 준비", "청소 꿀팁", "수납 정리"],
            "IT/테크": ["AI 활용", "생산성 앱", "아이폰 팁"],
            "취업교육": ["자기소개서", "면접", "자격증"],
        }
        crawl_and_learn(default_keywords, count_per_keyword=5)

    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        learner = BlogLearner()
        stats = learner.get_stats()
        print(f"\n📊 학습 DB 통계:")
        print(f"  - 참조 블로그: {stats['total_reference_blogs']}개")
        print(f"  - 학습된 패턴: {stats['total_patterns']}개")
        print(f"  - 카테고리별: {stats['by_category']}")

    elif len(sys.argv) > 2 and sys.argv[1] == "pattern":
        category = sys.argv[2]
        learner = BlogLearner()
        prompt = learner.get_prompt_injection(category)
        if prompt:
            print(prompt)
        else:
            print(f"'{category}' 카테고리 패턴 없음")

    else:
        print("사용법:")
        print("  python blog_learner.py crawl    # 기본 키워드 크롤링 + 학습")
        print("  python blog_learner.py stats    # DB 통계")
        print("  python blog_learner.py pattern <카테고리>  # 패턴 조회")
