#!/usr/bin/env python3
"""
주간 성과 업데이트 크론
매주 월요일 새벽 5시 실행

GA4 + Search Console에서 성과 데이터 수집
→ 고성과 글 패턴 학습 → 콘텐츠 생성에 반영

크론 설정:
  0 5 * * 1 cd ~/quickinfo-autoblog && ~/quickinfo-autoblog/venv/bin/python weekly_performance.py >> logs/weekly_performance.log 2>&1
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 50)
    logger.info(f"📊 주간 성과 업데이트 시작: {datetime.now()}")
    logger.info("=" * 50)

    try:
        from utils.performance_tracker import PerformanceTracker
        from utils.blog_learner import BlogLearner

        tracker = PerformanceTracker()
        learner = BlogLearner()

        # 1. 모든 글 성과 업데이트
        logger.info("\n[1/3] GA4 + Search Console 성과 수집...")
        updated = tracker.update_all_posts(days=30)
        logger.info(f"  ✅ {updated}개 글 성과 업데이트")

        # 2. 카테고리별 고성과 글 분석
        logger.info("\n[2/3] 카테고리별 성과 학습...")
        categories = ["재테크", "건강", "생활정보", "IT/테크", "취업교육", "여행"]
        for cat in categories:
            result = tracker.learn_from_performance(cat)
            if result:
                logger.info(f"  📚 {cat}: {result['sample_count']}개 고성과 글 학습")

        # 3. 고성과 글 리포트
        logger.info("\n[3/3] 고성과 글 Top 10...")
        top_posts = tracker.get_high_performers(min_score=50, limit=10)
        for i, p in enumerate(top_posts, 1):
            logger.info(f"  {i}. [{p['performance_score']:.0f}점] {p['title'][:40]}...")

        # 통계
        stats = learner.get_stats()
        logger.info("\n" + "=" * 50)
        logger.info("✅ 성과 업데이트 완료!")
        logger.info(f"  - 참조 블로그: {stats['total_reference_blogs']}개")
        logger.info(f"  - 학습된 패턴: {stats['total_patterns']}개 카테고리")
        logger.info(f"  - 고성과 글: {len(top_posts)}개")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ 성과 업데이트 실패: {e}")
        raise


if __name__ == "__main__":
    main()
