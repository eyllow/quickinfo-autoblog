#!/usr/bin/env python3
"""
워드프레스 블로그 자동 발행 스케줄러

스케줄 (일 3개, 랜덤 시간):
    1. 오전 7:00~7:30 사이 랜덤   → 트렌드 1개
    2. 오후 3:00~3:30 사이 랜덤   → 트렌드 1개
    3. 오후 6:00~6:30 사이 랜덤   → 에버그린 1개

사용법:
    python scheduler.py              # 스케줄러 시작
    python scheduler.py --run-now    # 즉시 한 번 실행 후 스케줄러 시작
    python scheduler.py --status     # 스케줄 상태 확인
"""
import argparse
import logging
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import run_pipeline

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_dir / f'scheduler_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# APScheduler 로거 레벨 조정
logging.getLogger('apscheduler').setLevel(logging.WARNING)


# ============================================================
# 랜덤 딜레이 헬퍼
# ============================================================

def random_delay(min_minutes: int = 0, max_minutes: int = 30):
    """
    랜덤 딜레이 적용

    Args:
        min_minutes: 최소 대기 시간 (분)
        max_minutes: 최대 대기 시간 (분)

    Returns:
        실제 대기한 분 수
    """
    delay_minutes = random.randint(min_minutes, max_minutes)
    delay_seconds = delay_minutes * 60

    scheduled_time = datetime.now()
    actual_time = datetime.now()

    if delay_minutes > 0:
        logger.info(f"랜덤 딜레이: {delay_minutes}분 대기 중...")
        time.sleep(delay_seconds)
        actual_time = datetime.now()

    logger.info(f"실제 발행 시간: {actual_time.strftime('%Y-%m-%d %H:%M:%S')}")
    return delay_minutes


# ============================================================
# 스케줄 작업 정의
# ============================================================

def job_morning_evergreen():
    """오전 9:00~9:45 - 에버그린 키워드 1개 (시즌 기반)"""
    logger.info("=" * 60)
    logger.info("[09:00 시간대] 에버그린 발행 작업 시작")
    logger.info("=" * 60)

    delay = random_delay(0, 45)

    try:
        logger.info(f"에버그린 키워드 1개 발행 시작 (딜레이: {delay}분)")
        run_pipeline(dry_run=False, posts_limit=1, evergreen=True)
        logger.info("[09:00 시간대] 발행 완료!")
    except Exception as e:
        logger.error(f"[09:00 시간대] 발행 실패: {e}")


def job_evening_evergreen():
    """오후 6:00~6:30 - 에버그린 키워드 1개 (시즌/트렌드 기반 선정)"""
    logger.info("=" * 60)
    logger.info("[18:00 시간대] 에버그린 발행 작업 시작")
    logger.info("=" * 60)

    # 0~45분 사이 랜덤 딜레이
    delay = random_delay(0, 45)

    try:
        # 시즌/트렌드 기반 키워드 미리 로깅
        try:
            from crawlers.evergreen_selector import EvergreenSelector
            from datetime import datetime

            selector = EvergreenSelector()
            current_month = datetime.now().month
            season_keywords = selector.get_current_season_keywords()

            logger.info(f"현재 월: {current_month}월")
            logger.info(f"시즌 키워드: {season_keywords[:5]}...")  # 처음 5개만

            # 트렌드 에버그린 확인
            trending_eg = selector.get_trending_evergreen()
            if trending_eg:
                logger.info(f"트렌드 에버그린 발견: {trending_eg}")
        except Exception as e:
            logger.warning(f"에버그린 선정 로깅 실패: {e}")

        logger.info(f"에버그린 키워드 1개 발행 시작 (딜레이: {delay}분)")
        run_pipeline(dry_run=False, posts_limit=1, evergreen=True)
        logger.info("[18:00 시간대] 발행 완료!")
    except Exception as e:
        logger.error(f"[18:00 시간대] 발행 실패: {e}")


# ============================================================
# 스케줄러 관리
# ============================================================

def signal_handler(signum, frame):
    """시그널 핸들러 (graceful shutdown)"""
    logger.info("Received shutdown signal. Stopping scheduler...")
    sys.exit(0)


def run_scheduler(run_now: bool = False):
    """
    스케줄러 실행

    Args:
        run_now: 즉시 실행 여부
    """
    logger.info("=" * 60)
    logger.info("Auto Blog Publisher Scheduler")
    logger.info("=" * 60)
    logger.info("Schedule (랜덤 시간):")
    logger.info("  09:00~09:45 → 에버그린 1개 (시즌 기반)")
    logger.info("  18:00~18:45 → 에버그린 1개 (트렌드 매칭)")
    logger.info("-" * 60)
    logger.info("Total: 2 posts per day")
    logger.info("  - Evergreen: 2 posts")
    logger.info("=" * 60)

    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 스케줄러 생성
    scheduler = BlockingScheduler(timezone='Asia/Seoul')

    # 1. 오전 9:00 → 에버그린 1개 (시즌 키워드)
    scheduler.add_job(
        job_morning_evergreen,
        CronTrigger(hour=9, minute=0, timezone='Asia/Seoul'),
        id='job_09_evergreen',
        name='Morning Evergreen (09:00~09:30)',
        misfire_grace_time=3600
    )

    # 2. 오후 6:00 → 에버그린 1개 (트렌드 매칭 우선)
    scheduler.add_job(
        job_evening_evergreen,
        CronTrigger(hour=18, minute=0, timezone='Asia/Seoul'),
        id='job_18_evergreen',
        name='Evening Evergreen (18:00~18:30)',
        misfire_grace_time=3600
    )

    # 스케줄 확인
    logger.info("\nScheduled Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}")

    # 즉시 실행 옵션
    if run_now:
        logger.info("\n즉시 실행 모드...")
        job_morning_evergreen()

    logger.info("\nScheduler started. Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def show_status():
    """스케줄 상태 표시"""
    print("=" * 60)
    print("Auto Blog Publisher - Schedule Status")
    print("=" * 60)
    print("\nDaily Schedule (Asia/Seoul, 랜덤 시간):")
    print("  1. 09:00~09:30 → 에버그린 키워드 1개 (시즌 기반)")
    print("  2. 18:00~18:30 → 에버그린 키워드 1개 (트렌드 매칭 우선)")
    print("\nTotal: 2 posts per day (고품질 에버그린 중심)")
    print("  - Evergreen: 2 posts")
    print("\n랜덤 시간 작동 방식:")
    print("  - 각 시간대 시작 시 트리거")
    print("  - 0~30분 사이 랜덤 딜레이 후 발행")
    print("  - 실제 발행 시간이 로그에 기록됨")
    print("=" * 60)


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="Auto Blog Publisher Scheduler"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run morning job immediately before starting scheduler"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show schedule status and exit"
    )

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    run_scheduler(run_now=args.run_now)


if __name__ == "__main__":
    main()
