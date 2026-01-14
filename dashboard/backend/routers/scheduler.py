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

    # 오늘 발행 현황 파싱
    today_posts = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-500:]  # 최근 500줄
                for line in lines:
                    if today_str in line:
                        # 발행 성공 로그 파싱
                        if "Successfully published" in line or "발행 완료" in line:
                            try:
                                # 시간 추출
                                time_match = re.search(r'(\d{2}:\d{2})', line)
                                time_str = time_match.group(1) if time_match else ""

                                # URL 추출
                                url_match = re.search(r'(https?://[^\s]+)', line)
                                url = url_match.group(1) if url_match else ""

                                # 키워드/제목 추출
                                keyword_match = re.search(r'키워드[:\s]+([^\s,]+)', line)
                                keyword = keyword_match.group(1) if keyword_match else ""

                                today_posts.append({
                                    "time": time_str,
                                    "url": url.rstrip(')').rstrip(','),
                                    "keyword": keyword,
                                    "status": "completed"
                                })
                            except Exception:
                                pass
        except Exception:
            pass

    # 스케줄 정보
    schedule = [
        {"time": "07:00~07:30", "type": "트렌드", "status": "pending"},
        {"time": "15:00~15:30", "type": "트렌드", "status": "pending"},
        {"time": "18:00~18:30", "type": "에버그린", "status": "pending"},
    ]

    # 현재 시간 기준으로 상태 업데이트
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    completed_count = len(today_posts)

    for i, s in enumerate(schedule):
        hour = int(s["time"].split(":")[0])
        if current_hour > hour or (current_hour == hour and current_minute > 30):
            if i < completed_count:
                schedule[i]["status"] = "completed"
            else:
                schedule[i]["status"] = "missed"
        elif current_hour == hour and current_minute <= 30:
            schedule[i]["status"] = "running"

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
        "today_posts": today_posts[-5:],  # 최근 5개만
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
