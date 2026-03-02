"""
Google Indexing API — 포스트 발행 시 자동 색인 요청
"""
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

KEY_FILE = Path(__file__).resolve().parent.parent / "config" / "google-indexing-key.json"
INDEXING_API_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def request_indexing(url: str, action: str = "URL_UPDATED") -> bool:
    """
    Google Indexing API로 URL 색인 요청

    Args:
        url: 색인할 URL
        action: URL_UPDATED (신규/수정) 또는 URL_DELETED (삭제)

    Returns:
        성공 여부
    """
    try:
        from google.oauth2 import service_account
        import requests as req

        if not KEY_FILE.exists():
            logger.warning(f"Google Indexing key not found: {KEY_FILE}")
            return False

        credentials = service_account.Credentials.from_service_account_file(
            str(KEY_FILE),
            scopes=["https://www.googleapis.com/auth/indexing"]
        )

        # 액세스 토큰 발급
        from google.auth.transport.requests import Request
        credentials.refresh(Request())

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {credentials.token}",
        }

        body = {
            "url": url,
            "type": action,
        }

        resp = req.post(INDEXING_API_URL, headers=headers, json=body, timeout=10)

        if resp.status_code == 200:
            logger.info(f"✅ Google Indexing 요청 성공: {url}")
            print(f"  🔍 Google 색인 요청 완료: {url}")
            return True
        else:
            logger.warning(f"Google Indexing 실패 ({resp.status_code}): {resp.text[:200]}")
            print(f"  ⚠️ Google 색인 요청 실패: {resp.status_code}")
            return False

    except ImportError:
        logger.warning("google-auth 패키지 미설치. pip install google-auth")
        return False
    except Exception as e:
        logger.warning(f"Google Indexing 오류: {e}")
        return False


def request_indexing_batch(urls: list) -> dict:
    """여러 URL 일괄 색인 요청"""
    results = {"success": [], "failed": []}
    for url in urls:
        if request_indexing(url):
            results["success"].append(url)
        else:
            results["failed"].append(url)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        request_indexing(url)
    else:
        print("Usage: python google_indexing.py <URL>")
