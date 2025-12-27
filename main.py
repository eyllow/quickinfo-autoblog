"""
워드프레스 자동 블로그 발행 시스템
메인 실행 파일
"""
import argparse
import logging
import sys
from datetime import datetime

from config.settings import settings
from crawlers.google_trends import GoogleTrendsCrawler
from crawlers.web_search import WebSearcher
from generators.content_generator import ContentGenerator
from publishers.wordpress import WordPressPublisher
from publishers.coupang import insert_coupang_banner
from database.db_manager import DBManager
from media.image_fetcher import ImageFetcher

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


def run_auto_publish(
    keyword: str = None,
    category: str = None,
    is_draft: bool = False,
    is_evergreen: bool = False
) -> dict:
    """
    자동 발행 실행

    Args:
        keyword: 수동 지정 키워드 (없으면 자동 수집)
        category: 수동 지정 카테고리
        is_draft: 임시 저장 여부
        is_evergreen: 에버그린 콘텐츠 여부

    Returns:
        발행 결과 딕셔너리
    """
    logger.info("=" * 50)
    logger.info("자동 발행 시작")
    logger.info("=" * 50)

    db = DBManager()
    trends = GoogleTrendsCrawler()
    generator = ContentGenerator()
    publisher = WordPressPublisher()

    # 이미지 중복 방지 캐시 초기화
    ImageFetcher.reset_used_images()

    result = {
        "success": False,
        "keyword": None,
        "title": None,
        "url": None,
        "error": None,
    }

    try:
        # 1. 키워드 선택
        if keyword:
            selected_keyword = keyword
            logger.info(f"수동 키워드 사용: {selected_keyword}")
        elif is_evergreen:
            # 에버그린 키워드 순환 선택
            from config.settings import settings
            import json

            evergreen_path = settings.project_root / "config" / "evergreen_keywords.json"
            with open(evergreen_path, 'r', encoding='utf-8') as f:
                evergreen_data = json.load(f)

            keywords = evergreen_data.get("keywords", [])
            current_index = db.get_evergreen_index()

            if not keywords:
                raise ValueError("에버그린 키워드가 없습니다.")

            selected_keyword = keywords[current_index % len(keywords)]
            next_index = (current_index + 1) % len(keywords)
            db.update_evergreen_index(next_index)

            logger.info(f"에버그린 키워드 선택: {selected_keyword} (인덱스: {current_index})")
        else:
            # 트렌드 키워드 자동 수집
            published_keywords = db.get_published_keywords(days=30)
            trend_data = trends.get_best_keyword(exclude_keywords=published_keywords)

            if not trend_data:
                raise ValueError("사용 가능한 트렌드 키워드가 없습니다.")

            selected_keyword = trend_data["keyword"]
            logger.info(f"트렌드 키워드 선택: {selected_keyword}")

        result["keyword"] = selected_keyword

        # 2. 중복 확인
        if db.is_keyword_published(selected_keyword):
            logger.warning(f"이미 발행된 키워드: {selected_keyword}")
            result["error"] = "이미 발행된 키워드입니다."
            return result

        # 3. 콘텐츠 생성
        logger.info("콘텐츠 생성 중...")
        post = generator.generate_full_post(
            keyword=selected_keyword,
            is_evergreen=is_evergreen
        )

        if not post:
            raise ValueError("콘텐츠 생성 실패")

        result["title"] = post.title

        # 카테고리 오버라이드
        if category:
            post.category = category

        # 4. 쿠팡 배너 삽입
        content, has_coupang = insert_coupang_banner(
            content=post.content,
            keyword=selected_keyword,
            category=post.category,
            position="bottom"
        )
        post.content = content
        post.has_coupang = has_coupang

        # 5. 이미지 삽입 (AI 판단에 따라 스크린샷 또는 Pexels 이미지 사용)
        logger.info("이미지 삽입 중...")
        logger.info(f"이미지 타입: {post.image_types}")
        content_with_images, featured_image_id = publisher.insert_images_to_content(
            content=post.content,
            keyword=selected_keyword,
            image_types=post.image_types,
            count=5
        )
        post.content = content_with_images

        # 글자수 최종 확인
        final_char_count = len(post.content)
        logger.info(f"최종 글자수: {final_char_count}자")

        # 6. 워드프레스 발행
        status = "draft" if is_draft else "publish"
        logger.info(f"워드프레스 발행 중... (상태: {status})")

        publish_result = publisher.publish_post(
            title=post.title,
            content=post.content,
            excerpt=post.excerpt,
            category=post.category,
            featured_image_id=featured_image_id,
            status=status
        )

        if publish_result:
            result["success"] = True
            result["url"] = publish_result.get("url", "")

            # 7. 발행 이력 저장
            db.save_published_post(
                keyword=selected_keyword,
                title=post.title,
                url=result["url"],
                category=post.category,
                template=post.template,
                status=status
            )

            logger.info(f"발행 완료: {result['url']}")
        else:
            result["error"] = "워드프레스 발행 실패"

    except Exception as e:
        logger.error(f"자동 발행 실패: {e}")
        result["error"] = str(e)

    logger.info("=" * 50)
    logger.info(f"발행 결과: {'성공' if result['success'] else '실패'}")
    logger.info("=" * 50)

    return result


def run_batch_publish(count: int = 3, is_draft: bool = False) -> list:
    """
    다중 글 발행

    Args:
        count: 발행할 글 수
        is_draft: 임시 저장 여부

    Returns:
        발행 결과 리스트
    """
    results = []

    for i in range(count):
        logger.info(f"\n{'='*50}")
        logger.info(f"다중 발행 {i+1}/{count}")
        logger.info(f"{'='*50}\n")

        result = run_auto_publish(is_draft=is_draft)
        results.append(result)

        if not result["success"]:
            logger.warning(f"발행 실패로 중단: {result.get('error')}")
            break

    return results


def show_stats():
    """통계 출력"""
    db = DBManager()
    stats = db.get_stats()

    print("\n" + "=" * 40)
    print("📊 발행 통계")
    print("=" * 40)
    print(f"  전체 발행: {stats.get('total', 0)}개")
    print(f"  오늘 발행: {stats.get('today', 0)}개")
    print(f"  이번 달:   {stats.get('this_month', 0)}개")

    by_category = stats.get('by_category', {})
    if by_category:
        print("\n  카테고리별:")
        for cat, cnt in by_category.items():
            print(f"    - {cat}: {cnt}개")

    print("=" * 40 + "\n")


def show_recent_posts(limit: int = 10):
    """최근 발행 글 출력"""
    db = DBManager()
    posts = db.get_recent_posts(limit)

    print("\n" + "=" * 40)
    print(f"📝 최근 발행 글 ({len(posts)}개)")
    print("=" * 40)

    for post in posts:
        print(f"  [{post.get('category', '-')}] {post['keyword']}")
        print(f"    제목: {post['title'][:40]}...")
        print(f"    발행: {post['published_at']}")
        print()

    print("=" * 40 + "\n")


def test_connection():
    """연결 테스트"""
    from media.screenshot import is_screenshot_available

    print("\n" + "=" * 40)
    print("🔌 연결 테스트")
    print("=" * 40)

    # 워드프레스
    publisher = WordPressPublisher()
    if publisher.is_configured():
        if publisher.test_connection():
            print("  ✅ 워드프레스: 연결 성공")
        else:
            print("  ❌ 워드프레스: 연결 실패")
    else:
        print("  ⚠️  워드프레스: 설정 없음")

    # Claude API
    if settings.anthropic_api_key:
        print("  ✅ Claude API: 설정됨")
    else:
        print("  ❌ Claude API: 설정 없음")

    # Pexels API
    if settings.pexels_api_key:
        print("  ✅ Pexels API: 설정됨")
    else:
        print("  ⚠️  Pexels API: 설정 없음 (이미지 기능 제한)")

    # Google Custom Search
    if settings.google_api_key and settings.google_cse_id:
        print("  ✅ Google Search: 설정됨")
    else:
        print("  ⚠️  Google Search: 설정 없음 (웹 검색 제한)")

    # 스크린샷 기능 (Node.js + Puppeteer)
    if is_screenshot_available():
        print("  ✅ 스크린샷: 사용 가능 (Node.js + Puppeteer)")
    else:
        print("  ⚠️  스크린샷: 사용 불가 (Node.js/Puppeteer 필요)")

    print("=" * 40 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="워드프레스 자동 블로그 발행 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py                        # 트렌드 키워드로 자동 발행
  python main.py --keyword "아이폰16"    # 특정 키워드로 발행
  python main.py --draft                # 임시 저장으로 발행
  python main.py --evergreen            # 에버그린 키워드로 발행
  python main.py --batch 3              # 3개 글 연속 발행
  python main.py --stats                # 발행 통계 보기
  python main.py --recent               # 최근 발행 글 보기
  python main.py --test                 # 연결 테스트
        """
    )

    parser.add_argument(
        "--keyword", "-k",
        type=str,
        help="발행할 키워드 (지정하지 않으면 트렌드에서 자동 선택)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="카테고리 (지정하지 않으면 자동 분류)"
    )
    parser.add_argument(
        "--draft", "-d",
        action="store_true",
        help="임시 저장으로 발행"
    )
    parser.add_argument(
        "--evergreen", "-e",
        action="store_true",
        help="에버그린 키워드 사용"
    )
    parser.add_argument(
        "--batch", "-b",
        type=int,
        metavar="COUNT",
        help="다중 발행 (지정한 개수만큼 발행)"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="발행 통계 출력"
    )
    parser.add_argument(
        "--recent", "-r",
        action="store_true",
        help="최근 발행 글 출력"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="연결 테스트"
    )

    args = parser.parse_args()

    # 명령 실행
    if args.stats:
        show_stats()
    elif args.recent:
        show_recent_posts()
    elif args.test:
        test_connection()
    elif args.batch:
        results = run_batch_publish(count=args.batch, is_draft=args.draft)
        success_count = sum(1 for r in results if r["success"])
        print(f"\n📊 다중 발행 결과: {success_count}/{len(results)} 성공")
    else:
        result = run_auto_publish(
            keyword=args.keyword,
            category=args.category,
            is_draft=args.draft,
            is_evergreen=args.evergreen
        )

        if result["success"]:
            print(f"\n✅ 발행 성공!")
            print(f"   키워드: {result['keyword']}")
            print(f"   제목: {result['title']}")
            print(f"   URL: {result['url']}")
        else:
            print(f"\n❌ 발행 실패: {result.get('error', '알 수 없는 오류')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
