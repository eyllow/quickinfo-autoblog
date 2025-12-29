"""실시간 로그 관리 시스템"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
import json


class LogManager:
    """실시간 로그 관리 싱글톤"""
    _instance = None
    _logs: deque
    _subscribers: List[asyncio.Queue]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs = deque(maxlen=100)  # 최근 100개 로그 유지
            cls._instance._subscribers = []
        return cls._instance

    async def add_log(self, level: str, stage: str, message: str, details: Optional[Dict] = None):
        """로그 추가 및 구독자들에게 브로드캐스트"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,  # "info", "success", "warning", "error", "progress"
            "stage": stage,  # "keyword", "context", "generate", "image", "publish"
            "message": message,
            "details": details
        }
        self._logs.append(log_entry)

        # 모든 구독자에게 전송
        for queue in self._subscribers:
            try:
                await queue.put(log_entry)
            except Exception:
                pass

    def subscribe(self) -> asyncio.Queue:
        """새 구독자 등록"""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """구독 해제"""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_recent_logs(self, count: int = 50) -> List[Dict]:
        """최근 로그 조회"""
        return list(self._logs)[-count:]

    def clear_logs(self):
        """로그 초기화"""
        self._logs.clear()


# 전역 인스턴스
log_manager = LogManager()


# 편의 함수들 (동기 버전 - 비동기 컨텍스트 외부에서 사용)
def add_log_sync(level: str, stage: str, message: str, details: Dict = None):
    """동기 방식으로 로그 추가 (비동기 컨텍스트 외부용)"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "stage": stage,
        "message": message,
        "details": details
    }
    log_manager._logs.append(log_entry)

    # 구독자에게 전송 시도
    for queue in log_manager._subscribers:
        try:
            queue.put_nowait(log_entry)
        except Exception:
            pass


# 비동기 편의 함수들
async def log_info(stage: str, message: str, details: Dict = None):
    await log_manager.add_log("info", stage, message, details)


async def log_success(stage: str, message: str, details: Dict = None):
    await log_manager.add_log("success", stage, message, details)


async def log_warning(stage: str, message: str, details: Dict = None):
    await log_manager.add_log("warning", stage, message, details)


async def log_error(stage: str, message: str, details: Dict = None):
    await log_manager.add_log("error", stage, message, details)


async def log_progress(stage: str, message: str, details: Dict = None):
    await log_manager.add_log("progress", stage, message, details)


# 동기 편의 함수들 (generators 등 비동기 컨텍스트 외부에서 사용)
def log_info_sync(stage: str, message: str, details: Dict = None):
    add_log_sync("info", stage, message, details)


def log_success_sync(stage: str, message: str, details: Dict = None):
    add_log_sync("success", stage, message, details)


def log_warning_sync(stage: str, message: str, details: Dict = None):
    add_log_sync("warning", stage, message, details)


def log_error_sync(stage: str, message: str, details: Dict = None):
    add_log_sync("error", stage, message, details)


def log_progress_sync(stage: str, message: str, details: Dict = None):
    add_log_sync("progress", stage, message, details)
