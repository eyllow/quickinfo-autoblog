"""유니크 이미지 생성 모듈 - Puppeteer 스크린샷 연동"""
import subprocess
import os
import random
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 스크린샷 저장 디렉토리
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "temp_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# 스크린샷 생성 스크립트 경로
SCRIPT_PATH = Path(__file__).resolve().parent / "screenshot_generator.js"

# 스크린샷이 효과적인 키워드
SCREENSHOT_KEYWORDS = [
    "환율", "비트코인", "이더리움", "코인", "주식", "코스피", "코스닥",
    "날씨", "부동산", "시세", "차트", "그래프", "지수", "금리", "금값"
]

# 스크린샷 사용 카테고리 (50% 확률)
SCREENSHOT_CATEGORIES = ["재테크", "트렌드"]


def generate_unique_screenshot(keyword: str, overlay_text: str = None) -> str:
    """
    Puppeteer로 유니크 스크린샷 생성

    Args:
        keyword: 검색/캡쳐 키워드
        overlay_text: 이미지에 추가할 텍스트 (선택)

    Returns:
        생성된 스크린샷 파일 경로 또는 None
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = random.randint(1000, 9999)
    output_path = str(SCREENSHOT_DIR / f"screenshot_{timestamp}_{random_suffix}.png")

    # Node.js 스크립트 실행
    cmd = [
        'node', str(SCRIPT_PATH),
        '--keyword', keyword,
        '--output', output_path
    ]

    if overlay_text:
        cmd.extend(['--text', overlay_text])

    try:
        print(f"📸 스크린샷 생성 중: {keyword}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60초 타임아웃
            cwd=str(Path(__file__).resolve().parent.parent)  # 프로젝트 루트에서 실행
        )

        if result.returncode == 0:
            # 출력에서 최종 파일 경로 추출 (RESULT: 접두사로 시작)
            for line in result.stdout.strip().split('\n'):
                if line.startswith('RESULT:'):
                    final_path = line.replace('RESULT:', '').strip()

                    if final_path == 'FAILED':
                        logger.warning("Screenshot generation failed")
                        return None

                    if os.path.exists(final_path):
                        logger.info(f"Screenshot generated: {final_path}")
                        print(f"✅ 스크린샷 생성 완료: {final_path}")
                        return final_path

            # RESULT 없이 output_path가 존재하면 사용
            if os.path.exists(output_path):
                logger.info(f"Screenshot generated (no overlay): {output_path}")
                print(f"✅ 스크린샷 생성 완료: {output_path}")
                return output_path

        logger.warning(f"Screenshot failed: {result.stderr}")
        print(f"⚠️ 스크린샷 실패: {result.stderr[:200]}")
        return None

    except subprocess.TimeoutExpired:
        logger.warning("Screenshot timeout (60s)")
        print("⚠️ 스크린샷 타임아웃 (60초 초과)")
        return None
    except FileNotFoundError:
        logger.warning("Node.js not installed or script not found")
        print("⚠️ Node.js가 설치되지 않았거나 스크립트를 찾을 수 없음")
        return None
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        print(f"⚠️ 스크린샷 에러: {e}")
        return None


def should_use_screenshot(keyword: str, category: str) -> bool:
    """
    스크린샷 사용 여부 결정 — 비활성화됨
    (정부사이트 봇 차단으로 깨진 이미지 발생)
    """
    return False


def cleanup_old_screenshots(max_age_hours: int = 24):
    """
    오래된 스크린샷 파일 정리

    Args:
        max_age_hours: 삭제 기준 시간 (시간 단위)
    """
    if not SCREENSHOT_DIR.exists():
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0

    for file in SCREENSHOT_DIR.glob("*.png"):
        try:
            file_age = current_time - file.stat().st_mtime
            if file_age > max_age_seconds:
                file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old screenshot: {file.name}")
        except Exception as e:
            logger.warning(f"Failed to delete {file.name}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old screenshots")
        print(f"🗑️ 오래된 스크린샷 {deleted_count}개 삭제됨")


def get_screenshot_info(keyword: str) -> dict:
    """
    스크린샷 정보 조회 (디버깅용)

    Args:
        keyword: 키워드

    Returns:
        스크린샷 대상 정보 딕셔너리
    """
    from datetime import datetime

    for kw in SCREENSHOT_KEYWORDS:
        if kw in keyword:
            return {
                "matched_keyword": kw,
                "will_capture": True,
                "source": "keyword_match"
            }

    return {
        "matched_keyword": None,
        "will_capture": False,
        "source": "no_match"
    }


if __name__ == "__main__":
    # 테스트
    print("=== 유니크 스크린샷 생성 테스트 ===\n")

    # 테스트 1: 비트코인 스크린샷
    print("테스트 1: 비트코인 키워드")
    result = generate_unique_screenshot(
        keyword="비트코인",
        overlay_text=f"비트코인 실시간 시세 ({datetime.now().strftime('%Y.%m.%d')})"
    )
    print(f"결과: {result}\n")

    # 테스트 2: 일반 키워드
    print("테스트 2: 일반 키워드 (연말정산)")
    result = generate_unique_screenshot(
        keyword="연말정산",
        overlay_text=f"연말정산 정보 ({datetime.now().strftime('%Y.%m.%d')})"
    )
    print(f"결과: {result}\n")

    # 테스트 3: 스크린샷 사용 여부 확인
    print("테스트 3: 스크린샷 사용 여부 확인")
    test_cases = [
        ("비트코인 전망", "재테크"),
        ("연말정산 환급", "재테크"),
        ("아이폰16 스펙", "IT테크"),
    ]

    for kw, cat in test_cases:
        should_use = should_use_screenshot(kw, cat)
        print(f"  {kw} ({cat}): {'✅ 스크린샷 사용' if should_use else '❌ Pexels 사용'}")
