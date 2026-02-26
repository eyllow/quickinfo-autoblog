"""SQLite 데이터베이스 모델 및 관리"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class PublishedPost:
    """발행된 포스트 데이터 클래스"""
    id: Optional[int]
    keyword: str
    title: str
    wp_post_id: int
    wp_url: str
    created_at: datetime


class Database:
    """SQLite 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """데이터베이스 디렉토리 확인 및 생성"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """데이터베이스 테이블 초기화"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS published_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    wp_post_id INTEGER NOT NULL,
                    wp_url TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 키워드 인덱스 생성 (중복 체크 성능 향상)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword ON published_posts(keyword)
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def is_keyword_published(self, keyword: str) -> bool:
        """키워드가 이미 발행되었는지 확인"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM published_posts WHERE keyword = ?",
                (keyword,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def get_published_keywords(self) -> list[str]:
        """발행된 모든 키워드 목록 반환"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT keyword FROM published_posts")
            return [row[0] for row in cursor.fetchall()]

    def save_published_post(
        self,
        keyword: str,
        title: str,
        wp_post_id: int,
        wp_url: str
    ) -> int:
        """발행 이력 저장"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO published_posts (keyword, title, wp_post_id, wp_url)
                VALUES (?, ?, ?, ?)
                """,
                (keyword, title, wp_post_id, wp_url)
            )
            conn.commit()
            post_id = cursor.lastrowid
            logger.info(f"Saved published post: {keyword} -> {wp_url}")
            return post_id

    def get_recent_posts(self, limit: int = 10) -> list[PublishedPost]:
        """최근 발행된 포스트 목록 반환"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, keyword, title, wp_post_id, wp_url, created_at
                FROM published_posts
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                PublishedPost(
                    id=row["id"],
                    keyword=row["keyword"],
                    title=row["title"],
                    wp_post_id=row["wp_post_id"],
                    wp_url=row["wp_url"],
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in rows
            ]

    def is_similar_keyword_published(self, keyword: str, days: int = 7) -> bool:
        """
        최근 N일 내 유사 키워드가 발행되었는지 확인 (부분 문자열 매칭)

        Args:
            keyword: 확인할 키워드
            days: 조회 기간 (일)

        Returns:
            유사 키워드 존재 여부
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT keyword, title FROM published_posts
                WHERE created_at >= datetime('now', ?)
                """,
                (f'-{days} days',)
            )
            for row in cursor.fetchall():
                pub_keyword = row[0]
                pub_title = row[1]
                # 부분 문자열 매칭: 키워드가 서로 포함 관계
                if keyword in pub_keyword or pub_keyword in keyword:
                    logger.info(f"Similar keyword found: '{keyword}' ~ '{pub_keyword}'")
                    return True
                # 제목에 키워드가 포함되어 있는지
                if keyword in pub_title:
                    logger.info(f"Keyword found in recent title: '{keyword}' in '{pub_title}'")
                    return True
            return False

    def get_posts_count_today(self) -> int:
        """오늘 발행된 포스트 수 반환"""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM published_posts
                WHERE DATE(created_at) = ?
                """,
                (today,)
            )
            return cursor.fetchone()[0]


# 싱글톤 데이터베이스 인스턴스
db = Database()
