#!/usr/bin/env python3
"""
주간 블로그 학습 크롤러 (크론용)
매주 수/토 새벽 4시 실행

사용법:
  python3 weekly_learn.py

크론 설정 예시:
  0 4 * * 3,6 cd ~/quickinfo-autoblog && ~/quickinfo-autoblog/venv/bin/python weekly_learn.py >> logs/weekly_learn.log 2>&1
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger(__name__)

# 카테고리별 학습 키워드 (에버그린 + 시즌)
LEARNING_KEYWORDS = {
    "재테크": [
        "연말정산", "근로장려금", "청년도약계좌", "주택청약",
        "적금 추천", "예금 금리 비교", "신용점수 올리기",
        "주식 배당", "ETF 추천"
    ],
    "건강": [
        "면역력 높이는 방법", "수면 질 개선", "영양제 추천",
        "다이어트 방법", "운동 루틴", "피부 관리",
        "눈 건강", "허리 통증"
    ],
    "생활정보": [
        "이사 준비", "청소 꿀팁", "수납 정리", "인테리어 아이디어",
        "절약 방법", "생활비 줄이기", "가전제품 추천"
    ],
    "IT/테크": [
        "AI 활용법", "생산성 앱 추천", "아이폰 팁",
        "맥북 활용", "윈도우 단축키", "유튜브 설정"
    ],
    "취업교육": [
        "자기소개서 쓰는법", "면접 준비", "자격증 추천",
        "이직 준비", "포트폴리오 만들기"
    ],
    "여행": [
        "국내 여행지 추천", "해외 여행 준비물", "항공권 싸게 사는법",
        "숙소 예약 팁"
    ],
}

def main():
    logger.info("=" * 50)
    logger.info(f"🧠 주간 블로그 학습 시작: {datetime.now()}")
    logger.info("=" * 50)

    try:
        from utils.blog_learner import crawl_and_learn, BlogLearner

        # 크롤링 + 학습
        total = crawl_and_learn(LEARNING_KEYWORDS, count_per_keyword=5)

        # 통계 출력
        learner = BlogLearner()
        stats = learner.get_stats()

        logger.info("\n" + "=" * 50)
        logger.info(f"✅ 학습 완료!")
        logger.info(f"  - 이번 저장: {total}개")
        logger.info(f"  - 전체 참조 블로그: {stats['total_reference_blogs']}개")
        logger.info(f"  - 학습된 패턴: {stats['total_patterns']}개 카테고리")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ 학습 실패: {e}")
        raise

if __name__ == "__main__":
    main()
