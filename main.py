#!/usr/bin/env python3
"""
워드프레스 블로그 자동 발행 시스템 메인 파이프라인

사용법:
    python main.py                      # 전체 파이프라인 실행 (트렌드)
    python main.py --dry-run            # 실제 발행 없이 테스트
    python main.py --keyword "키워드"    # 특정 키워드로 테스트
    python main.py --draft              # draft 모드로 발행
    python main.py --limit 2            # 발행 개수 제한
    python main.py --evergreen          # 에버그린 키워드 발행
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from database.models import db
from crawlers import GoogleTrendsCrawler, NaverNewsCrawler
from crawlers.blog_reference import BlogReferenceCrawler
from generators import ContentGenerator
from publishers import WordPressPublisher
from utils.quality_scorer import score_generated_content
from utils.performance_learner import performance_learner, get_keyword_scores

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / 'logs' / f'pipeline_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# 에버그린 키워드 파일 경로
EVERGREEN_FILE = Path(__file__).parent / 'config' / 'evergreen_keywords.json'


def ensure_log_directory():
    """로그 디렉토리 생성"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)


def get_unpublished_keywords(keywords: list[str], limit: int = 5) -> list[str]:
    """
    발행되지 않은 키워드 필터링

    Args:
        keywords: 전체 키워드 목록
        limit: 반환할 최대 키워드 수

    Returns:
        미발행 키워드 목록
    """
    published_keywords = set(db.get_published_keywords())
    unpublished = [kw for kw in keywords if kw not in published_keywords]
    return unpublished[:limit]


def load_evergreen_keywords() -> dict:
    """에버그린 키워드 파일 로드"""
    try:
        with open(EVERGREEN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Evergreen keywords file not found: {EVERGREEN_FILE}")
        return {"keywords": [], "last_index": 0}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing evergreen keywords: {e}")
        return {"keywords": [], "last_index": 0}


def save_evergreen_index(index: int):
    """에버그린 키워드 인덱스 저장 (순환용)"""
    try:
        data = load_evergreen_keywords()
        data["last_index"] = index
        with open(EVERGREEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving evergreen index: {e}")


def get_next_evergreen_keyword() -> str | None:
    """
    다음 에버그린 키워드 반환

    개선된 선정 로직:
    1. 현재 시즌에 맞는 키워드 우선
    2. 트렌드에서 에버그린 키워드 발견 시 우선 사용
    3. priority (high > medium > low) 반영
    4. 최근 7일 내 발행된 키워드 제외
    """
    try:
        from crawlers.evergreen_selector import EvergreenSelector

        selector = EvergreenSelector()
        keyword, reason = selector.get_keyword_for_publish()

        logger.info(f"에버그린 키워드 선정: {keyword} ({reason})")
        return keyword

    except Exception as e:
        logger.error(f"EvergreenSelector 에러, 기존 방식 폴백: {e}")

        # 폴백: 기존 순환 방식
        data = load_evergreen_keywords()
        keywords = data.get("keywords", [])
        last_index = data.get("last_index", 0)

        if not keywords:
            logger.warning("No evergreen keywords available")
            return None

        # 문자열/딕셔너리 혼합 처리
        keyword_list = [
            kw if isinstance(kw, str) else kw.get("keyword", "")
            for kw in keywords
        ]

        published_keywords = set(db.get_published_keywords())

        # 전체 키워드를 순환하며 미발행 키워드 찾기
        for i in range(len(keyword_list)):
            index = (last_index + i) % len(keyword_list)
            keyword = keyword_list[index]

            if keyword not in published_keywords:
                save_evergreen_index((index + 1) % len(keyword_list))
                return keyword

        # 모든 키워드가 발행된 경우
        logger.info("All evergreen keywords published. Restarting from beginning.")
        keyword = keyword_list[last_index % len(keyword_list)]
        save_evergreen_index((last_index + 1) % len(keyword_list))
        return keyword


def process_keyword(
    keyword: str,
    news_crawler: NaverNewsCrawler,
    content_generator: ContentGenerator,
    wp_publisher: WordPressPublisher,
    dry_run: bool = False,
    status: str = "publish"
) -> bool:
    """
    단일 키워드 처리

    Args:
        keyword: 처리할 키워드
        news_crawler: 뉴스 크롤러 인스턴스
        content_generator: 콘텐츠 생성기 인스턴스
        wp_publisher: 워드프레스 발행기 인스턴스
        dry_run: 실제 발행 없이 테스트
        status: 발행 상태

    Returns:
        성공 여부
    """
    try:
        logger.info(f"Processing keyword: {keyword}")

        # 0. 블로그 참조 분석 (강화 버전)
        logger.info("Step 0: Blog reference analysis (enhanced)...")
        blog_crawler = BlogReferenceCrawler()
        blog_analysis = blog_crawler.get_detailed_analysis(keyword, count=5)
        reference_keywords = blog_analysis.get("common_patterns", {}).get("common_keywords", [])
        logger.info(f"Blog analysis: {len(blog_analysis.get('blogs', []))} blogs, {len(reference_keywords)} common keywords")

        # 1. 네이버 뉴스 검색 및 요약
        logger.info("Step 1: Fetching news data...")
        news_data = news_crawler.get_news_summary(keyword, max_articles=3)
        logger.info(f"News data fetched: {len(news_data)} characters")

        # 2. Claude로 블로그 글 생성 (고품질 콘텐츠 + 이미지 + 버튼)
        logger.info("Step 2: Generating high-quality blog content with Claude...")
        post = content_generator.generate_full_post(keyword, news_data)
        logger.info(f"Content generated: {post.title}")
        logger.info(f"  - Length: {len(post.content)} characters")
        logger.info(f"  - Category: {post.category}")
        logger.info(f"  - Has Coupang: {post.has_coupang}")
        logger.info(f"  - Web Sources: {len(post.sources)}")

        # 이미지 삽입 확인 로그
        image_count = len(re.findall(r'<figure[^>]*>.*?<img[^>]*>.*?</figure>', post.content, re.DOTALL | re.IGNORECASE))
        logger.info(f"  - Images inserted: {image_count}")
        logger.info(f"  - Excerpt: {post.excerpt[:50]}..." if post.excerpt else "  - Excerpt: (none)")

        # 2.5. 품질 점수 체크 (새로운 기능)
        logger.info("Step 2.5: Quality score check...")
        quality_result = score_generated_content(
            content=post.content,
            keyword=keyword,
            title=post.title,
            reference_keywords=reference_keywords
        )
        logger.info(f"  - Quality Score: {quality_result.total_score:.1f}/100")
        logger.info(f"  - Char: {quality_result.char_count}, Headings: {quality_result.heading_count}, Images: {quality_result.image_count}")
        if quality_result.suggestions:
            logger.info(f"  - Suggestions: {'; '.join(quality_result.suggestions[:3])}")

        # 품질 점수 미달 시 경고 (재생성은 미래 버전에서)
        if quality_result.needs_regeneration:
            logger.warning(f"  ⚠️ Quality score below threshold ({quality_result.total_score:.1f} < 60). Consider improvement.")

        # 웹검색 출처 표시
        if post.sources:
            logger.info("  - Sources used:")
            for src in post.sources[:5]:
                logger.info(f"      * {src['title'][:50]}...")
                logger.info(f"        {src['url']}")

        if dry_run:
            logger.info("=== DRY RUN MODE ===")
            logger.info(f"Title: {post.title}")
            logger.info(f"Category: {post.category}")
            logger.info(f"Excerpt: {post.excerpt}")
            logger.info(f"Has Coupang Link: {post.has_coupang}")
            logger.info(f"Content preview:\n{post.content[:1000]}...")
            logger.info("=== DRY RUN END ===")
            return True

        # 2.5. 발행 직전 최종 중복 체크
        try:
            recent = wp_publisher.get_recent_post_titles(days=14)
            for rt, rs in recent:
                rt_lower = rt.lower().strip()
                title_lower = post.title.lower().strip()
                kw_lower = keyword.lower().strip()
                # 제목이 80% 이상 겹치거나 키워드가 최근 제목에 포함
                if (kw_lower in rt_lower) or (title_lower in rt_lower) or (rt_lower in title_lower):
                    logger.warning(f"DUPLICATE BLOCKED at publish time: '{post.title}' ~ '{rt}'")
                    return False
        except Exception as e:
            logger.warning(f"Pre-publish dedup check failed: {e}")

        # 3. 워드프레스에 발행
        logger.info(f"Step 3: Publishing to WordPress (status: {status})...")
        result = wp_publisher.publish_with_image(
            title=post.title,
            content=post.content,
            keyword=keyword,
            status=status,
            categories=[post.category],
            tags=None,  # generate_tags 함수가 자동 생성
            excerpt=post.excerpt,
            category=post.category  # 카테고리별 태그 생성용
        )

        if result.success:
            # 4. DB에 발행 이력 저장
            logger.info("Step 4: Saving to database...")
            db.save_published_post(
                keyword=keyword,
                title=post.title,
                wp_post_id=result.post_id,
                wp_url=result.url
            )
            logger.info(f"Successfully published: {result.url}")
            return True
        else:
            logger.error(f"Failed to publish: {result.error}")
            return False

    except Exception as e:
        logger.error(f"Error processing keyword '{keyword}': {e}")
        return False


def run_pipeline(
    dry_run: bool = False,
    specific_keyword: str = None,
    posts_limit: int = None,
    status: str = "publish",
    evergreen: bool = False
):
    """
    메인 파이프라인 실행

    Args:
        dry_run: 실제 발행 없이 테스트
        specific_keyword: 특정 키워드만 처리
        posts_limit: 발행할 포스트 수 제한
        status: 발행 상태
        evergreen: 에버그린 키워드 사용 여부
    """
    mode = "Evergreen" if evergreen else "Trending"
    logger.info("=" * 60)
    logger.info(f"Starting Auto Blog Publisher Pipeline [{mode}]")
    logger.info(f"Dry run: {dry_run}, Status: {status}")
    logger.info("=" * 60)

    # 인스턴스 초기화
    trends_crawler = GoogleTrendsCrawler()
    news_crawler = NaverNewsCrawler()
    content_generator = ContentGenerator()
    wp_publisher = WordPressPublisher()

    # 발행할 포스트 수
    posts_count = posts_limit or 1

    # 키워드 수집
    if specific_keyword:
        keywords = [specific_keyword]
        logger.info(f"Using specific keyword: {specific_keyword}")
    elif evergreen:
        # 에버그린 키워드 가져오기
        keywords = []
        for _ in range(posts_count):
            kw = get_next_evergreen_keyword()
            if kw:
                keywords.append(kw)
        logger.info(f"Evergreen keywords: {keywords}")
    else:
        # 주제 선정 알고리즘 (다중 소스 + 스코어링)
        logger.info("Selecting best keywords with TopicSelector...")
        try:
            from crawlers.topic_selector import TopicSelector
            topic_selector = TopicSelector()
            keywords = topic_selector.get_best_keywords(limit=posts_count * 2)  # 성과 기반 필터링용 여유분
            logger.info(f"TopicSelector keywords: {keywords}")

            # 성과 학습 기반 키워드 우선순위 조정
            if len(keywords) > posts_count:
                logger.info("Applying performance-based keyword scoring...")
                scored_keywords = get_keyword_scores(keywords)
                keywords = [kw for kw, _ in scored_keywords[:posts_count]]
                logger.info(f"Performance-optimized keywords: {keywords}")

        except Exception as e:
            logger.warning(f"TopicSelector failed, falling back to Google Trends: {e}")
            all_keywords = trends_crawler.get_trending_keywords_simple(limit=20)
            keywords = get_unpublished_keywords(all_keywords, limit=posts_count)

        if not keywords:
            logger.info("No suitable keywords found. Exiting.")
            return

    if not keywords:
        logger.warning("No keywords to process. Exiting.")
        return

    # 중복 발행 방지: WP 최근 글 제목 + DB 유사 키워드 체크
    if not specific_keyword:
        try:
            recent_titles = wp_publisher.get_recent_post_titles(days=7)
            recent_title_texts = [t[0].lower() for t in recent_titles]
            logger.info(f"Recent WP posts: {len(recent_titles)}")

            filtered_keywords = []
            for kw in keywords:
                # WP 제목에서 중복 체크
                is_dup = False
                for title_text in recent_title_texts:
                    if kw.lower() in title_text or title_text in kw.lower():
                        logger.info(f"Skipping '{kw}' - similar to recent WP title")
                        is_dup = True
                        break
                if is_dup:
                    continue
                # DB 유사 키워드 체크
                if db.is_similar_keyword_published(kw, days=7):
                    logger.info(f"Skipping '{kw}' - similar keyword in DB")
                    continue
                filtered_keywords.append(kw)

            logger.info(f"After dedup filter: {len(filtered_keywords)}/{len(keywords)} keywords")
            keywords = filtered_keywords
        except Exception as e:
            logger.warning(f"Dedup check failed, proceeding with all keywords: {e}")

    if not keywords:
        logger.info("All keywords filtered by dedup. Exiting.")
        return

    # 키워드별 처리
    success_count = 0
    fail_count = 0

    for i, keyword in enumerate(keywords, 1):
        logger.info(f"\n--- Processing {i}/{len(keywords)}: {keyword} ---")

        success = process_keyword(
            keyword=keyword,
            news_crawler=news_crawler,
            content_generator=content_generator,
            wp_publisher=wp_publisher,
            dry_run=dry_run,
            status=status
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info(f"Pipeline Complete! [{mode}]")
    logger.info(f"Success: {success_count}, Failed: {fail_count}")
    logger.info("=" * 60)


def main():
    """CLI 엔트리포인트"""
    ensure_log_directory()

    parser = argparse.ArgumentParser(
        description="WordPress Auto Blog Publisher"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually publishing"
    )
    parser.add_argument(
        "--keyword",
        type=str,
        help="Process a specific keyword"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of posts to publish"
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Publish as draft instead of publish"
    )
    parser.add_argument(
        "--evergreen",
        action="store_true",
        help="Use evergreen keywords instead of trending"
    )

    args = parser.parse_args()

    status = "draft" if args.draft else "publish"

    run_pipeline(
        dry_run=args.dry_run,
        specific_keyword=args.keyword,
        posts_limit=args.limit,
        status=status,
        evergreen=args.evergreen
    )


if __name__ == "__main__":
    main()
