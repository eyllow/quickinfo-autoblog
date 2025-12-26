"""
자동 발행 스케줄러
APScheduler를 사용하여 정해진 시간에 자동 발행
"""
import logging
import random
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from main import run_auto_publish

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_path, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# APScheduler 로거 레벨 조정
logging.getLogger('apscheduler').setLevel(logging.WARNING)


def scheduled_publish(is_evergreen: bool = False):
    """
    스케줄된 발행 작업

    Args:
        is_evergreen: 에버그린 콘텐츠 여부
    """
    # 랜덤 딜레이 (0~30분)
    delay_minutes = random.randint(0, 30)
    logger.info(f"발행 시작 (딜레이: {delay_minutes}분 후)")

    if delay_minutes > 0:
        import time
        time.sleep(delay_minutes * 60)

    try:
        result = run_auto_publish(is_evergreen=is_evergreen)

        if result["success"]:
            logger.info(f"스케줄 발행 성공: {result['title']}")
        else:
            logger.error(f"스케줄 발행 실패: {result.get('error')}")

    except Exception as e:
        logger.error(f"스케줄 발행 중 오류: {e}")


def trend_publish_job():
    """트렌드 키워드 발행 작업"""
    logger.info("=" * 50)
    logger.info("트렌드 키워드 스케줄 발행 시작")
    logger.info("=" * 50)
    scheduled_publish(is_evergreen=False)


def evergreen_publish_job():
    """에버그린 키워드 발행 작업"""
    logger.info("=" * 50)
    logger.info("에버그린 키워드 스케줄 발행 시작")
    logger.info("=" * 50)
    scheduled_publish(is_evergreen=True)


def start_scheduler():
    """스케줄러 시작"""
    scheduler = BlockingScheduler()

    # 스케줄 설정
    # 발행 시간: 07:00, 15:00, 18:00 (+ 랜덤 0~30분 딜레이)
    schedule_times = [
        {"hour": 7, "minute": 0, "job": trend_publish_job, "name": "morning_trend"},
        {"hour": 15, "minute": 0, "job": trend_publish_job, "name": "afternoon_trend"},
        {"hour": 18, "minute": 0, "job": evergreen_publish_job, "name": "evening_evergreen"},
    ]

    for schedule in schedule_times:
        scheduler.add_job(
            schedule["job"],
            CronTrigger(hour=schedule["hour"], minute=schedule["minute"]),
            id=schedule["name"],
            name=schedule["name"],
            replace_existing=True
        )
        logger.info(f"스케줄 등록: {schedule['name']} ({schedule['hour']:02d}:{schedule['minute']:02d})")

    # 시그널 핸들러
    def signal_handler(signum, frame):
        logger.info("스케줄러 종료 중...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 50)
    logger.info("자동 발행 스케줄러 시작")
    logger.info("=" * 50)
    logger.info("발행 스케줄:")
    logger.info("  - 07:00 트렌드 키워드")
    logger.info("  - 15:00 트렌드 키워드")
    logger.info("  - 18:00 에버그린 키워드")
    logger.info("  (각 발행은 0~30분 랜덤 딜레이)")
    logger.info("=" * 50)
    logger.info("종료하려면 Ctrl+C를 누르세요.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("스케줄러가 종료되었습니다.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="자동 발행 스케줄러")
    parser.add_argument(
        "--now",
        action="store_true",
        help="즉시 한 번 발행 (테스트용)"
    )
    parser.add_argument(
        "--evergreen",
        action="store_true",
        help="에버그린 키워드로 발행 (--now와 함께 사용)"
    )

    args = parser.parse_args()

    if args.now:
        # 즉시 발행
        if args.evergreen:
            evergreen_publish_job()
        else:
            trend_publish_job()
    else:
        # 스케줄러 시작
        start_scheduler()
