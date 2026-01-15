"""스케줄러 상태 모니터링 API"""
from fastapi import APIRouter
import subprocess
import os
from datetime import datetime
from pathlib import Path
import re

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_FILE = PROJECT_ROOT / "logs" / "scheduler.log"
SCHEDULER_SCRIPT = "scheduler.py"


@router.get("/status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    import sqlite3
    import logging

    logger = logging.getLogger(__name__)

    # 프로세스 실행 여부 확인
    try:
        result = subprocess.run(
            ["pgrep", "-f", SCHEDULER_SCRIPT],
            capture_output=True,
            text=True
        )
        is_running = result.returncode == 0
        pid = result.stdout.strip().split('\n')[0] if is_running else None
    except Exception:
        is_running = False
        pid = None

    # DB에서 오늘 발행 현황 조회
    today_posts = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        db_path = PROJECT_ROOT / "database" / "blog_publisher.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT title, keyword as category, wp_url as url, created_at
                FROM published_posts
                WHERE date(created_at) = ?
                ORDER BY created_at DESC
            """, (today_str,))

            for row in cursor.fetchall():
                time_str = row['created_at'].split(' ')[1][:5] if row['created_at'] and ' ' in row['created_at'] else ''
                today_posts.append({
                    "time": time_str,
                    "title": row['title'],
                    "category": row['category'],
                    "url": row['url'],
                    "status": "completed"
                })
            conn.close()
    except Exception as e:
        logger.error(f"DB 조회 실패: {e}")

    # 스케줄 정보
    schedule = [
        {"time": "07:00~07:30", "type": "트렌드", "status": "pending"},
        {"time": "15:00~15:30", "type": "트렌드", "status": "pending"},
        {"time": "18:00~18:30", "type": "에버그린", "status": "pending"},
    ]

    # 현재 시간 기준으로 상태 계산
    current_hour = datetime.now().hour
    completed_count = len(today_posts)

    # 발행 완료 시간대 매칭
    for post in today_posts:
        hour = int(post["time"].split(":")[0]) if post["time"] else 0
        if 7 <= hour < 12:
            schedule[0]["status"] = "completed"
        elif 12 <= hour < 18:
            schedule[1]["status"] = "completed"
        elif hour >= 18:
            schedule[2]["status"] = "completed"

    # 지난 시간대 중 미완료는 missed로 표시
    for i, s in enumerate(schedule):
        slot_hour = int(s["time"].split(":")[0])
        if current_hour > slot_hour + 1 and s["status"] == "pending":
            s["status"] = "missed"

    # 다음 발행 시간 계산
    next_publish = None
    for s in schedule:
        if s["status"] == "pending":
            next_publish = s
            break

    return {
        "is_running": is_running,
        "pid": pid,
        "today_completed": completed_count,
        "today_total": 3,
        "today_posts": today_posts[:5],
        "schedule": schedule,
        "next_publish": next_publish,
        "last_updated": datetime.now().isoformat()
    }


@router.get("/logs")
async def get_scheduler_logs(lines: int = 50):
    """스케줄러 로그 조회"""
    if not LOG_FILE.exists():
        return {"logs": [], "error": "로그 파일 없음"}

    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception as e:
        return {"logs": [], "error": str(e)}


@router.post("/restart")
async def restart_scheduler():
    """스케줄러 재시작"""
    try:
        # 기존 프로세스 종료
        subprocess.run(["pkill", "-f", SCHEDULER_SCRIPT], capture_output=True)

        # 잠시 대기
        import time
        time.sleep(1)

        # 새로 시작 (nohup 사용)
        log_file = open(LOG_FILE, 'a')
        subprocess.Popen(
            ["python", str(PROJECT_ROOT / SCHEDULER_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        return {"success": True, "message": "스케줄러가 재시작되었습니다."}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/stop")
async def stop_scheduler():
    """스케줄러 중지"""
    try:
        result = subprocess.run(["pkill", "-f", SCHEDULER_SCRIPT], capture_output=True)
        if result.returncode == 0:
            return {"success": True, "message": "스케줄러가 중지되었습니다."}
        else:
            return {"success": True, "message": "스케줄러가 이미 중지된 상태입니다."}
    except Exception as e:
        return {"success": False, "message": str(e)}
