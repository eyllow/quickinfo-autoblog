"""생성된 글 품질 점수 시스템

생성된 글을 자동으로 품질 체크:
- 글자 수 체크 (3000~4000자 목표)
- 소제목 수 (5~8개)
- 이미지 수 (적정 범위)
- 수치/예시 포함 여부
- 참조 블로그 대비 키워드 커버리지 (%)
- 전체 품질 점수 (0~100)
- 점수 미달(60점 미만) 시 재생성 플래그 반환
- 결과를 SQLite DB에 저장 (학습용)
"""
import logging
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)

# 데이터베이스 경로
QUALITY_DB_PATH = Path(settings.database_path).parent / "quality_scores.db"


@dataclass
class QualityScore:
    """품질 점수 결과"""
    keyword: str
    title: str
    total_score: float = 0.0
    length_score: float = 0.0
    heading_score: float = 0.0
    image_score: float = 0.0
    data_score: float = 0.0
    keyword_coverage: float = 0.0
    needs_regeneration: bool = False

    # 세부 데이터
    char_count: int = 0
    heading_count: int = 0
    image_count: int = 0
    number_count: int = 0
    example_count: int = 0
    covered_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)

    # 개선 제안
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "keyword": self.keyword,
            "title": self.title,
            "total_score": round(self.total_score, 1),
            "length_score": round(self.length_score, 1),
            "heading_score": round(self.heading_score, 1),
            "image_score": round(self.image_score, 1),
            "data_score": round(self.data_score, 1),
            "keyword_coverage": round(self.keyword_coverage, 1),
            "needs_regeneration": self.needs_regeneration,
            "char_count": self.char_count,
            "heading_count": self.heading_count,
            "image_count": self.image_count,
            "number_count": self.number_count,
            "example_count": self.example_count,
            "covered_keywords": self.covered_keywords,
            "missing_keywords": self.missing_keywords,
            "suggestions": self.suggestions,
        }


class QualityScorer:
    """생성된 콘텐츠 품질 점수 시스템"""

    # 품질 기준 (조정 가능)
    TARGET_CHAR_MIN = 3000
    TARGET_CHAR_MAX = 4000
    TARGET_HEADINGS_MIN = 5
    TARGET_HEADINGS_MAX = 8
    TARGET_IMAGES_MIN = 2
    TARGET_IMAGES_MAX = 5
    MINIMUM_PASS_SCORE = 60

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """품질 점수 DB 초기화"""
        try:
            QUALITY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(QUALITY_DB_PATH))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    total_score REAL NOT NULL,
                    length_score REAL,
                    heading_score REAL,
                    image_score REAL,
                    data_score REAL,
                    keyword_coverage REAL,
                    char_count INTEGER,
                    heading_count INTEGER,
                    image_count INTEGER,
                    needs_regeneration BOOLEAN,
                    suggestions TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_keyword
                ON quality_scores(keyword)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_score
                ON quality_scores(total_score)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Quality DB initialized at {QUALITY_DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize quality DB: {e}")

    def score_content(
        self,
        content: str,
        keyword: str,
        title: str,
        reference_keywords: List[str] = None
    ) -> QualityScore:
        """
        콘텐츠 품질 점수 계산

        Args:
            content: HTML 콘텐츠
            keyword: 메인 키워드
            title: 글 제목
            reference_keywords: 참조 블로그에서 추출한 핵심 키워드 목록

        Returns:
            QualityScore 객체
        """
        result = QualityScore(keyword=keyword, title=title)

        # 1. 글자 수 체크 (25점 만점)
        result.char_count, result.length_score = self._score_length(content)

        # 2. 소제목 수 체크 (25점 만점)
        result.heading_count, result.heading_score = self._score_headings(content)

        # 3. 이미지 수 체크 (20점 만점)
        result.image_count, result.image_score = self._score_images(content)

        # 4. 수치/예시 포함 여부 (15점 만점)
        result.number_count, result.example_count, result.data_score = self._score_data(content)

        # 5. 키워드 커버리지 (15점 만점)
        if reference_keywords:
            result.covered_keywords, result.missing_keywords, result.keyword_coverage = \
                self._score_keyword_coverage(content, reference_keywords)
        else:
            result.keyword_coverage = 15  # 참조 키워드 없으면 만점 처리

        # 총점 계산
        result.total_score = (
            result.length_score +
            result.heading_score +
            result.image_score +
            result.data_score +
            result.keyword_coverage
        )

        # 재생성 필요 여부
        result.needs_regeneration = result.total_score < self.MINIMUM_PASS_SCORE

        # 개선 제안 생성
        result.suggestions = self._generate_suggestions(result)

        # DB에 저장
        self._save_score(result)

        logger.info(f"Quality score for '{keyword}': {result.total_score:.1f}/100 "
                   f"(regenerate: {result.needs_regeneration})")

        return result

    def _score_length(self, content: str) -> Tuple[int, float]:
        """글자 수 점수 (25점 만점)"""
        # HTML 태그 제거
        text_only = re.sub(r'<[^>]+>', '', content)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        char_count = len(text_only)

        # 점수 계산
        if self.TARGET_CHAR_MIN <= char_count <= self.TARGET_CHAR_MAX:
            score = 25.0
        elif char_count < self.TARGET_CHAR_MIN:
            # 최소 기준 미달 - 비례 감점
            ratio = char_count / self.TARGET_CHAR_MIN
            score = 25.0 * ratio
        else:
            # 최대 기준 초과 - 약간 감점 (너무 길어도 문제)
            excess_ratio = (char_count - self.TARGET_CHAR_MAX) / 1000
            score = max(15.0, 25.0 - excess_ratio * 5)

        return char_count, round(score, 1)

    def _score_headings(self, content: str) -> Tuple[int, float]:
        """소제목 수 점수 (25점 만점)"""
        # h2, h3, h4 태그 카운트
        headings = re.findall(r'<h[234][^>]*>.*?</h[234]>', content, re.IGNORECASE | re.DOTALL)
        heading_count = len(headings)

        # 점수 계산
        if self.TARGET_HEADINGS_MIN <= heading_count <= self.TARGET_HEADINGS_MAX:
            score = 25.0
        elif heading_count < self.TARGET_HEADINGS_MIN:
            score = 25.0 * (heading_count / self.TARGET_HEADINGS_MIN)
        else:
            # 너무 많은 소제목 - 약간 감점
            score = max(18.0, 25.0 - (heading_count - self.TARGET_HEADINGS_MAX) * 2)

        return heading_count, round(score, 1)

    def _score_images(self, content: str) -> Tuple[int, float]:
        """이미지 수 점수 (20점 만점)"""
        # img, figure 태그 카운트
        images = re.findall(r'<(?:img|figure)[^>]*>', content, re.IGNORECASE)
        image_count = len(images)

        # 점수 계산
        if self.TARGET_IMAGES_MIN <= image_count <= self.TARGET_IMAGES_MAX:
            score = 20.0
        elif image_count < self.TARGET_IMAGES_MIN:
            score = 20.0 * (image_count / self.TARGET_IMAGES_MIN) if self.TARGET_IMAGES_MIN > 0 else 0
        else:
            # 너무 많은 이미지 - 약간 감점
            score = max(12.0, 20.0 - (image_count - self.TARGET_IMAGES_MAX) * 2)

        return image_count, round(score, 1)

    def _score_data(self, content: str) -> Tuple[int, int, float]:
        """수치/예시 포함 점수 (15점 만점)"""
        # HTML 태그 제거
        text_only = re.sub(r'<[^>]+>', '', content)

        # 수치 데이터 카운트 (금액, 퍼센트, 날짜 등)
        number_patterns = [
            r'\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:원|만원|억원)',  # 금액
            r'\d+(?:\.\d+)?%',  # 퍼센트
            r'\d{4}년\s*\d{1,2}월',  # 날짜
            r'\d+(?:개월|년|일|명|건|회|개)',  # 단위
        ]
        number_count = 0
        for pattern in number_patterns:
            number_count += len(re.findall(pattern, text_only))

        # 예시/사례 패턴 카운트
        example_patterns = [
            r'예[를시]?\s*들[면어]',
            r'예시[로는]?',
            r'사례[로는]?',
            r'실제로',
            r'구체적으로',
            r'예컨대',
            r'가령',
        ]
        example_count = 0
        for pattern in example_patterns:
            example_count += len(re.findall(pattern, text_only))

        # 점수 계산
        # 수치 데이터: 최대 10점 (3개 이상이면 만점)
        number_score = min(10.0, number_count * 3.3)

        # 예시/사례: 최대 5점 (2개 이상이면 만점)
        example_score = min(5.0, example_count * 2.5)

        total_score = round(number_score + example_score, 1)

        return number_count, example_count, total_score

    def _score_keyword_coverage(
        self,
        content: str,
        reference_keywords: List[str]
    ) -> Tuple[List[str], List[str], float]:
        """키워드 커버리지 점수 (15점 만점)"""
        if not reference_keywords:
            return [], [], 15.0

        # HTML 태그 제거
        text_only = re.sub(r'<[^>]+>', '', content).lower()

        covered = []
        missing = []

        for kw in reference_keywords[:15]:  # 최대 15개 키워드 체크
            if kw.lower() in text_only:
                covered.append(kw)
            else:
                missing.append(kw)

        # 커버리지 비율
        coverage_ratio = len(covered) / len(reference_keywords) if reference_keywords else 1.0
        score = round(15.0 * coverage_ratio, 1)

        return covered, missing, score

    def _generate_suggestions(self, result: QualityScore) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        # 글자 수
        if result.char_count < self.TARGET_CHAR_MIN:
            diff = self.TARGET_CHAR_MIN - result.char_count
            suggestions.append(f"글 길이가 부족합니다. 약 {diff}자 추가 필요")
        elif result.char_count > self.TARGET_CHAR_MAX + 500:
            suggestions.append("글이 너무 깁니다. 핵심 내용 위주로 정리 필요")

        # 소제목
        if result.heading_count < self.TARGET_HEADINGS_MIN:
            suggestions.append(f"소제목이 부족합니다. {self.TARGET_HEADINGS_MIN - result.heading_count}개 추가 권장")
        elif result.heading_count > self.TARGET_HEADINGS_MAX + 2:
            suggestions.append("소제목이 너무 많습니다. 통합 정리 권장")

        # 이미지
        if result.image_count < self.TARGET_IMAGES_MIN:
            suggestions.append(f"이미지가 부족합니다. {self.TARGET_IMAGES_MIN - result.image_count}개 추가 권장")

        # 수치/예시
        if result.number_count < 2:
            suggestions.append("구체적인 수치/데이터 추가 권장 (금액, 퍼센트 등)")
        if result.example_count < 1:
            suggestions.append("실제 사례나 예시 추가 권장")

        # 키워드 커버리지
        if result.missing_keywords and len(result.missing_keywords) > 3:
            missing_preview = ", ".join(result.missing_keywords[:5])
            suggestions.append(f"다음 키워드 포함 권장: {missing_preview}")

        return suggestions

    def _save_score(self, result: QualityScore):
        """점수 결과 DB 저장"""
        try:
            conn = sqlite3.connect(str(QUALITY_DB_PATH))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO quality_scores (
                    keyword, title, total_score, length_score, heading_score,
                    image_score, data_score, keyword_coverage, char_count,
                    heading_count, image_count, needs_regeneration, suggestions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.keyword,
                result.title,
                result.total_score,
                result.length_score,
                result.heading_score,
                result.image_score,
                result.data_score,
                result.keyword_coverage,
                result.char_count,
                result.heading_count,
                result.image_count,
                result.needs_regeneration,
                ", ".join(result.suggestions)
            ))

            conn.commit()
            conn.close()
            logger.info(f"Quality score saved for '{result.keyword}'")
        except Exception as e:
            logger.error(f"Failed to save quality score: {e}")

    def get_average_scores(self, days: int = 30) -> Dict:
        """최근 N일 평균 점수 조회"""
        try:
            conn = sqlite3.connect(str(QUALITY_DB_PATH))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    AVG(total_score) as avg_total,
                    AVG(length_score) as avg_length,
                    AVG(heading_score) as avg_heading,
                    AVG(image_score) as avg_image,
                    AVG(data_score) as avg_data,
                    AVG(keyword_coverage) as avg_coverage,
                    COUNT(*) as count,
                    SUM(CASE WHEN needs_regeneration THEN 1 ELSE 0 END) as regen_count
                FROM quality_scores
                WHERE created_at >= datetime('now', ?)
            """, (f'-{days} days',))

            row = cursor.fetchone()
            conn.close()

            if row and row[0]:
                return {
                    "avg_total": round(row[0], 1),
                    "avg_length": round(row[1], 1),
                    "avg_heading": round(row[2], 1),
                    "avg_image": round(row[3], 1),
                    "avg_data": round(row[4], 1),
                    "avg_coverage": round(row[5], 1),
                    "total_count": row[6],
                    "regeneration_count": row[7],
                    "pass_rate": round((row[6] - row[7]) / row[6] * 100, 1) if row[6] > 0 else 0,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get average scores: {e}")
            return {}

    def get_low_score_keywords(self, limit: int = 10) -> List[Dict]:
        """저점수 키워드 목록 조회"""
        try:
            conn = sqlite3.connect(str(QUALITY_DB_PATH))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT keyword, title, total_score, suggestions, created_at
                FROM quality_scores
                WHERE needs_regeneration = 1
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "keyword": row[0],
                    "title": row[1],
                    "score": row[2],
                    "suggestions": row[3],
                    "created_at": row[4],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get low score keywords: {e}")
            return []


# 싱글톤 인스턴스
quality_scorer = QualityScorer()


def score_generated_content(
    content: str,
    keyword: str,
    title: str,
    reference_keywords: List[str] = None
) -> QualityScore:
    """
    생성된 콘텐츠 품질 점수 계산 (편의 함수)

    Args:
        content: HTML 콘텐츠
        keyword: 메인 키워드
        title: 글 제목
        reference_keywords: 참조 블로그 핵심 키워드 목록

    Returns:
        QualityScore 객체
    """
    return quality_scorer.score_content(content, keyword, title, reference_keywords)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 테스트
    test_content = """
    <h2>연말정산 환급 총정리</h2>
    <p>연말정산은 근로소득자가 매년 1월에 진행하는 세금 정산 절차입니다.</p>

    <h3>1. 연말정산 기간</h3>
    <p>2025년 연말정산은 2025년 1월 15일부터 2월 15일까지 진행됩니다.</p>
    <figure><img src="test.jpg" alt="연말정산"/></figure>

    <h3>2. 필요 서류</h3>
    <p>소득공제 신고서, 의료비 영수증, 기부금 영수증 등이 필요합니다.</p>
    <p>예를 들어, 의료비 공제는 총 급여의 3% 초과분에 대해 15%를 공제받습니다.</p>

    <h3>3. 환급 금액 계산</h3>
    <p>평균 환급 금액은 약 50만원~100만원 정도입니다.</p>
    <figure><img src="test2.jpg" alt="환급"/></figure>

    <h3>4. 주의사항</h3>
    <p>서류 누락 시 환급이 지연될 수 있으니 주의하세요.</p>
    """

    scorer = QualityScorer()
    result = scorer.score_content(
        content=test_content,
        keyword="연말정산",
        title="2025 연말정산 환급 총정리",
        reference_keywords=["연말정산", "환급", "소득공제", "세액공제", "의료비", "기부금", "신용카드"]
    )

    print("\n=== 품질 점수 결과 ===")
    print(f"총점: {result.total_score}/100")
    print(f"재생성 필요: {result.needs_regeneration}")
    print(f"\n세부 점수:")
    print(f"  - 글자 수: {result.length_score}/25 ({result.char_count}자)")
    print(f"  - 소제목: {result.heading_score}/25 ({result.heading_count}개)")
    print(f"  - 이미지: {result.image_score}/20 ({result.image_count}개)")
    print(f"  - 수치/예시: {result.data_score}/15 (수치 {result.number_count}개, 예시 {result.example_count}개)")
    print(f"  - 키워드 커버리지: {result.keyword_coverage}/15")
    print(f"\n커버된 키워드: {', '.join(result.covered_keywords)}")
    print(f"누락 키워드: {', '.join(result.missing_keywords)}")
    print(f"\n개선 제안:")
    for s in result.suggestions:
        print(f"  - {s}")
