"""실시간 로그 스트리밍 API"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json

from dashboard.backend.utils.log_manager import log_manager

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
@router.get("/")
async def get_recent_logs():
    """최근 로그 조회"""
    return {"logs": log_manager.get_recent_logs()}


@router.get("/stream")
@router.get("/stream/")
async def stream_logs():
    """SSE로 실시간 로그 스트리밍"""
    async def event_generator():
        queue = log_manager.subscribe()
        try:
            while True:
                try:
                    # 30초 타임아웃으로 연결 유지 확인
                    log_entry = await asyncio.wait_for(queue.get(), timeout=30.0)
                    data = json.dumps(log_entry, ensure_ascii=False)
                    yield f"event: log\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    # 연결 유지를 위한 heartbeat
                    yield f"event: heartbeat\ndata: ping\n\n"
        except asyncio.CancelledError:
            log_manager.unsubscribe(queue)
            raise
        finally:
            log_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        }
    )


@router.delete("")
@router.delete("/")
async def clear_logs():
    """로그 초기화"""
    log_manager.clear_logs()
    return {"message": "로그가 초기화되었습니다."}
