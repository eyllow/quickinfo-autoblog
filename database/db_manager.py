"""
SQLite 발행 이력 관리 모듈
발행된 글의 이력을 관리하고 중복 발행을 방지합니다.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings

logger = logging.getLogger(__name__)


class DBManager:
    """SQLite 데이터베이스 관리자"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(settings.db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """데이터베이스 테이블 초기화"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 발행된 글 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS published_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    category TEXT,
                    template TEXT,
                    status TEXT DEFAULT 'published',
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(keyword)
                )
            ''')

            # 에버그린 키워드 인덱스 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evergreen_index (
                    id INTEGER PRIMARY KEY,
                    current_index INTEGER DEFAULT 0
                )
            ''')

            # 초기 인덱스 설정
            cursor.execute('''
                INSERT OR IGNORE INTO evergreen_index (id, current_index)
                VALUES (1, 0)
            ''')

            conn.commit()
            logger.info("데이터베이스 초기화 완료")

    def save_published_post(
        self,
        keyword: str,
        title: str,
        url: str = "",
        category: str = "",
        template: str = "",
        status: str = "published"
    ) -> bool:
        """
        발행된 글 저장

        Args:
            keyword: 키워드
            title: 제목
            url: 발행 URL
            category: 카테고리
            template: 사용된 템플릿
            status: 상태

        Returns:
            저장 성공 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO published_posts
                    (keyword, title, url, category, template, status, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (keyword, title, url, category, template, status, datetime.now()))
                conn.commit()

            logger.info(f"발행 이력 저장: {keyword} -> {url}")
            return True

        except Exception as e:
            logger.error(f"발행 이력 저장 실패: {e}")
            return False

    def is_keyword_published(self, keyword: str, days: int = 30) -> bool:
        """
        키워드가 최근에 발행되었는지 확인

        Args:
            keyword: 키워드
            days: 확인 기간 (일)

        Returns:
            발행 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)

                cursor.execute('''
                    SELECT COUNT(*) FROM published_posts
                    WHERE keyword = ? AND published_at > ?
                ''', (keyword, cutoff_date))

                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            logger.error(f"키워드 확인 실패: {e}")
            return False

    def get_published_keywords(self, days: int = 30) -> List[str]:
        """
        최근 발행된 키워드 목록 조회

        Args:
            days: 조회 기간 (일)

        Returns:
            키워드 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now() - timedelta(days=days)

                cursor.execute('''
                    SELECT keyword FROM published_posts
                    WHERE published_at > ?
                    ORDER BY published_at DESC
                ''', (cutoff_date,))

                return [row['keyword'] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"키워드 목록 조회 실패: {e}")
            return []

    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """
        최근 발행 글 조회

        Args:
            limit: 조회 개수

        Returns:
            발행 글 리스트
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM published_posts
                    ORDER BY published_at DESC
                    LIMIT ?
                ''', (limit,))

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"최근 글 조회 실패: {e}")
            return []

    def get_stats(self) -> Dict:
        """
        발행 통계 조회

        Returns:
            통계 딕셔너리
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 전체 발행 수
                cursor.execute('SELECT COUNT(*) FROM published_posts')
                total = cursor.fetchone()[0]

                # 오늘 발행 수
                today = datetime.now().date()
                cursor.execute('''
                    SELECT COUNT(*) FROM published_posts
                    WHERE DATE(published_at) = ?
                ''', (today,))
                today_count = cursor.fetchone()[0]

                # 이번 달 발행 수
                month_start = today.replace(day=1)
                cursor.execute('''
                    SELECT COUNT(*) FROM published_posts
                    WHERE DATE(published_at) >= ?
                ''', (month_start,))
                month_count = cursor.fetchone()[0]

                # 카테고리별 통계
                cursor.execute('''
                    SELECT category, COUNT(*) as count
                    FROM published_posts
                    GROUP BY category
                    ORDER BY count DESC
                ''')
                by_category = {row['category']: row['count'] for row in cursor.fetchall()}

                return {
                    "total": total,
                    "today": today_count,
                    "this_month": month_count,
                    "by_category": by_category,
                }

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}

    def get_evergreen_index(self) -> int:
        """에버그린 키워드 현재 인덱스 조회"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT current_index FROM evergreen_index WHERE id = 1')
                row = cursor.fetchone()
                return row['current_index'] if row else 0
        except Exception as e:
            logger.error(f"에버그린 인덱스 조회 실패: {e}")
            return 0

    def update_evergreen_index(self, index: int):
        """에버그린 키워드 인덱스 업데이트"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE evergreen_index SET current_index = ? WHERE id = 1
                ''', (index,))
                conn.commit()
                logger.info(f"에버그린 인덱스 업데이트: {index}")
        except Exception as e:
            logger.error(f"에버그린 인덱스 업데이트 실패: {e}")


# 전역 인스턴스
db = DBManager()


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    print("=== 데이터베이스 테스트 ===\n")

    manager = DBManager()

    # 테스트 데이터 저장
    manager.save_published_post(
        keyword="테스트 키워드",
        title="테스트 제목",
        url="https://example.com/test",
        category="트렌드",
        template="리스트형"
    )

    # 중복 확인
    is_dup = manager.is_keyword_published("테스트 키워드")
    print(f"중복 확인: {'중복' if is_dup else '새 키워드'}")

    # 최근 글 조회
    recent = manager.get_recent_posts(5)
    print(f"\n최근 글 ({len(recent)}개):")
    for post in recent:
        print(f"  - {post['keyword']}: {post['title']}")

    # 통계
    stats = manager.get_stats()
    print(f"\n통계:")
    print(f"  전체: {stats.get('total', 0)}개")
    print(f"  오늘: {stats.get('today', 0)}개")
    print(f"  이번 달: {stats.get('this_month', 0)}개")
