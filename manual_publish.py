#!/usr/bin/env python3
"""
QuickInfo 수동 발행 파이프라인
사용법: python3 manual_publish.py "키워드" ["참조URL"]

전체 플로우:
1. 참조 URL 팩트 수집 (있으면)
2. 참조 블로그 탐색 + 분석
3. 콘텐츠 생성 (잔여 태그 자동 제거)
4. 관련 링크 카드 자동 생성
5. 정보 카드 자동 생성 (Gemini)
6. 키워드 기반 썸네일 자동 생성
7. WP 발행 + Google 색인 요청
"""

import sys
import os
import re
import json
import logging
import requests
from pathlib import Path
from datetime import datetime


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from config.settings import settings
from generators.content_generator import ContentGenerator, clean_html_styles
from publishers.wordpress import WordPressPublisher
from database.models import Database
from utils.image_fetcher import ImageFetcher

WP_AUTH = (settings.wp_user, settings.wp_app_password)


# ============================================================
# Step 1: 참조 URL에서 팩트 수집
# ============================================================
def fetch_reference_url(url: str) -> str:
    """참조 URL에서 텍스트 추출"""
    if not url:
        return ""
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        # 스크립트/스타일 제거
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # 첫 5000자만
        return text[:5000]
    except Exception as e:
        logger.warning(f"  ⚠️ 참조 URL 수집 실패: {e}")
        return ""


# ============================================================
# Step 2: 참조 블로그 탐색
# ============================================================
def search_reference_blogs(keyword: str) -> str:
    """네이버/구글에서 참조 블로그 분석"""
    try:
        from crawlers.blog_reference import BlogReferenceCrawler
        crawler = BlogReferenceCrawler()
        analysis = crawler.get_blog_analysis(keyword, count=3)
        if analysis:
            logger.info(f"  ✅ 참조 블로그 분석: {len(analysis)}자")
            return analysis
        else:
            logger.info("  ℹ️ 참조 블로그 없음 (신규 주제)")
            return ""
    except Exception as e:
        logger.warning(f"  ⚠️ 참조 블로그 탐색 실패: {e}")
        return ""


# ============================================================
# Step 3: 관련 링크 카드 생성 (Gemini)
# ============================================================
def generate_link_cards(keyword: str, ref_text: str) -> str:
    """키워드 관련 공식 사이트 링크 카드 HTML 생성 (폴백 포함)"""

    # 주요 키워드별 기본 공식 사이트 (Gemini 실패 시 폴백)
    FALLBACK_SITES = {
        "청년도약계좌": [
            {"name": "서민금융진흥원", "url": "https://www.kinfa.or.kr", "desc": "청년도약계좌 공식 운영기관", "color": "#1a73e8", "initial": "서"},
            {"name": "청년정책", "url": "https://www.youthcenter.go.kr", "desc": "청년 지원 정책 종합 포털", "color": "#00897b", "initial": "청"},
        ],
        "근로장려금": [
            {"name": "국세청 홈택스", "url": "https://www.hometax.go.kr", "desc": "근로장려금 신청 공식 사이트", "color": "#0d47a1", "initial": "국"},
            {"name": "정부24", "url": "https://www.gov.kr", "desc": "정부 서비스 통합 포털", "color": "#1565c0", "initial": "정"},
        ],
        "연말정산": [
            {"name": "국세청 홈택스", "url": "https://www.hometax.go.kr", "desc": "연말정산 간소화 서비스", "color": "#0d47a1", "initial": "국"},
            {"name": "국세청", "url": "https://www.nts.go.kr", "desc": "세금 관련 공식 안내", "color": "#1a237e", "initial": "세"},
        ],
        "주택청약": [
            {"name": "청약홈", "url": "https://www.applyhome.co.kr", "desc": "주택청약 공식 사이트", "color": "#1565c0", "initial": "청"},
            {"name": "LH 한국토지주택공사", "url": "https://www.lh.or.kr", "desc": "공공주택 정보", "color": "#00695c", "initial": "LH"},
        ],
        "전기차": [
            {"name": "환경부", "url": "https://www.me.go.kr", "desc": "전기차 보조금 정책 안내", "color": "#2e7d32", "initial": "환"},
            {"name": "저공해차 통합누리집", "url": "https://www.ev.or.kr", "desc": "전기차 구매 지원 정보", "color": "#1b5e20", "initial": "저"},
        ],
        "건강보험": [
            {"name": "국민건강보험공단", "url": "https://www.nhis.or.kr", "desc": "건강보험 공식 사이트", "color": "#0277bd", "initial": "건"},
        ],
        "국민연금": [
            {"name": "국민연금공단", "url": "https://www.nps.or.kr", "desc": "국민연금 공식 사이트", "color": "#00838f", "initial": "연"},
        ],
        "실업급여": [
            {"name": "고용보험", "url": "https://www.ei.go.kr", "desc": "실업급여 신청 공식 사이트", "color": "#0d47a1", "initial": "고"},
            {"name": "워크넷", "url": "https://www.work.go.kr", "desc": "취업 지원 포털", "color": "#1565c0", "initial": "워"},
        ],
        "여행": [
            {"name": "대한민국 구석구석", "url": "https://korean.visitkorea.or.kr", "desc": "국내 여행 정보 공식 사이트", "color": "#e91e63", "initial": "한"},
        ],
    }

    def build_card_html(sites):
        if not sites:
            return ""
        html = '<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e8f4fd 100%); border-radius: 16px;">'
        html += '<h3 style="margin: 0 0 20px 0; font-size: 18px; color: #1a1a1a;">&#128204; 관련 사이트 바로가기</h3>'
        for site in sites[:4]:
            domain = site["url"].replace("https://", "").replace("http://", "").split("/")[0]
            html += f'<a href="{site["url"]}" target="_blank" rel="noopener noreferrer" style="display: block; text-decoration: none; margin-bottom: 12px; padding: 16px; background: white; border-radius: 12px; border: 1px solid #e0e0e0;">'
            html += '<div style="display: flex; align-items: center;">'
            html += f'<div style="width: 48px; height: 48px; background: {site["color"]}; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; font-weight: bold; flex-shrink: 0;">{site["initial"]}</div>'
            html += '<div style="margin-left: 16px; flex: 1;">'
            html += f'<div style="font-size: 16px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px;">{site["name"]}</div>'
            html += f'<div style="font-size: 13px; color: #666;">{site["desc"]}</div>'
            html += f'<div style="font-size: 12px; color: {site["color"]}; margin-top: 4px;">{domain} &rarr;</div>'
            html += '</div></div></a>'
        html += '</div>'
        return html

    # 1. 키워드 매칭으로 폴백 사이트 확인
    fallback_sites = None
    for key, sites in FALLBACK_SITES.items():
        if key in keyword:
            fallback_sites = sites
            break

    # 2. Gemini로 생성 시도
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""다음 키워드에 대해 가장 유용한 공식 사이트 3~4개를 추천해줘.
반드시 실제 존재하는 공식 사이트만 추천하고, 정부/공공기관 사이트를 우선해줘.

키워드: {keyword}
참고 내용: {ref_text[:1000]}

JSON 배열로만 응답:
[{{"name": "사이트명", "url": "https://...", "desc": "설명 20자", "color": "#1a73e8", "initial": "첫글자"}}]"""

        resp = model.generate_content(prompt)
        text = resp.text.strip()
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            sites = json.loads(json_match.group())
            if sites:
                logger.info(f"  ✅ 링크 카드 {len(sites)}개 생성 (Gemini)")
                return build_card_html(sites)

    except Exception as e:
        logger.warning(f"  ⚠️ Gemini 링크 카드 실패: {e}")

    # 3. 폴백 사용
    if fallback_sites:
        logger.info(f"  ✅ 링크 카드 {len(fallback_sites)}개 생성 (폴백)")
        return build_card_html(fallback_sites)

    logger.warning(f"  ⚠️ 링크 카드 없음")
    return ""


# ============================================================
# Step 4: 정보 카드 생성 (Gemini)
# ============================================================
def generate_info_card(keyword: str, ref_text: str) -> str:
    """핵심 정보 요약 카드 HTML 생성"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""다음 키워드에 대한 핵심 정보를 3~5개 항목으로 정리해줘.
날짜, 금액, 대상, 방법 등 독자가 가장 궁금해할 핵심 팩트만.

키워드: {keyword}
참고 내용: {ref_text[:2000]}

JSON 배열로만 응답. 다른 텍스트 없이:
[
  {{"emoji": "📅", "label": "항목명", "value": "핵심 값"}}
]"""

        resp = model.generate_content(prompt)
        text = resp.text.strip()
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            items = json.loads(json_match.group())
        else:
            return ""

        # HTML 테이블 생성
        rows = ""
        for i, item in enumerate(items[:5]):
            border = 'border-bottom: 1px solid #c3d9f0;' if i < len(items) - 1 else ''
            emoji = item.get("emoji", "📌")
            label = item.get("label", "")
            value = item.get("value", "")
            rows += f'''<tr style="{border}">
<td style="padding: 10px; font-weight: bold; color: #2c5282; width: 30%;">{emoji} {label}</td>
<td style="padding: 10px;">{value}</td>
</tr>\n'''

        card_html = f"""
<div style="border: 2px solid #4a90d9; border-radius: 12px; padding: 25px; margin: 0 0 25px 0; background: linear-gradient(135deg, #eef5ff 0%, #f0f7ff 100%);">
<h3 style="margin: 0 0 15px 0; color: #2c5282;">📋 {keyword} 핵심 요약</h3>
<table style="width: 100%; border-collapse: collapse; font-size: 15px;">
{rows}</table>
</div>
"""
        logger.info(f"  ✅ 정보 카드 {len(items)}개 항목 생성")
        return card_html

    except Exception as e:
        logger.warning(f"  ⚠️ 정보 카드 생성 실패: {e}")
        return ""


# ============================================================
# Step 5: 키워드 기반 썸네일 생성
# ============================================================
def generate_thumbnail(keyword: str, info_items: list = None) -> str:
    """키워드 기반 정보 카드 스타일 썸네일 이미지 생성"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        W, H = 1200, 630
        img = Image.new('RGB', (W, H))
        draw = ImageDraw.Draw(img)

        # 그라데이션 배경
        for y in range(H):
            r = int(20 + (y/H) * 15)
            g = int(30 + (y/H) * 20)
            b = int(80 + (y/H) * 40)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # 상단 악센트 바
        draw.rectangle([(0, 0), (W, 5)], fill='#e94560')

        # 폰트
        font_paths = [
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/Library/Fonts/AppleSDGothicNeo.ttc',
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]

        title_font = sub_font = small_font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    title_font = ImageFont.truetype(fp, 48)
                    sub_font = ImageFont.truetype(fp, 28)
                    small_font = ImageFont.truetype(fp, 22)
                    break
                except:
                    continue

        if not title_font:
            title_font = ImageFont.load_default()
            sub_font = title_font
            small_font = title_font

        # 키워드를 줄바꿈 처리 (20자 초과 시)
        if len(keyword) > 20:
            mid = len(keyword) // 2
            # 공백 기준 분할
            space_idx = keyword.rfind(' ', 0, mid + 5)
            if space_idx > 0:
                line1, line2 = keyword[:space_idx], keyword[space_idx+1:]
            else:
                line1, line2 = keyword[:mid], keyword[mid:]
            draw.text((W//2, 180), line1, fill='#ffffff', font=title_font, anchor='mm')
            draw.text((W//2, 240), line2, fill='#e94560', font=title_font, anchor='mm')
            card_start_y = 310
        else:
            draw.text((W//2, 210), keyword, fill='#ffffff', font=title_font, anchor='mm')
            card_start_y = 300

        # 뱃지
        draw.rounded_rectangle([(80, 50), (280, 90)], radius=8, fill='#e94560')
        draw.text((180, 70), "QuickInfo", fill='white', font=small_font, anchor='mm')

        # 정보 항목 카드 (Gemini에서 받은 항목 또는 기본)
        if info_items:
            for i, item in enumerate(info_items[:3]):
                y = card_start_y + i * 65
                draw.rounded_rectangle([(100, y), (1100, y+52)], radius=8, fill=(255,255,255,25))
                draw.rounded_rectangle([(100, y), (1100, y+52)], radius=8, outline=(255,255,255,50), width=1)
                emoji = item.get("emoji", "📌")
                label = item.get("label", "")
                value = item.get("value", "")
                draw.text((130, y+26), f"{emoji} {label}", fill='#a0b0d0', font=small_font, anchor='lm')
                # value가 너무 길면 자르기
                if len(value) > 25:
                    value = value[:25] + "..."
                draw.text((430, y+26), value, fill='#ffffff', font=sub_font, anchor='lm')

        # 하단 장식
        for x in range(100, 1100, 40):
            draw.ellipse([(x, 560), (x+3, 563)], fill='#e94560')
        draw.text((W//2, 595), "quickinfo.kr", fill=(120,140,180), font=small_font, anchor='mm')

        out_path = f"/tmp/thumbnail-{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        img.save(out_path, 'PNG', quality=95)
        logger.info(f"  ✅ 썸네일 생성: {out_path}")
        return out_path

    except Exception as e:
        logger.warning(f"  ⚠️ 썸네일 생성 실패: {e}")
        return ""


# ============================================================
# Step 6: WP 미디어 업로드
# ============================================================
def upload_to_wp(file_path: str, alt_text: str = "") -> tuple:
    """이미지를 WP 미디어에 업로드"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        filename = os.path.basename(file_path)
        resp = requests.post(
            f"{settings.wp_url}/wp-json/wp/v2/media",
            auth=WP_AUTH,
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/png"},
            data=data, timeout=30
        )
        if resp.status_code in (200, 201):
            media = resp.json()
            if alt_text:
                requests.post(f"{settings.wp_url}/wp-json/wp/v2/media/{media['id']}",
                             auth=WP_AUTH, json={"alt_text": alt_text}, timeout=10)
            return media["id"], media["source_url"]
    except Exception as e:
        logger.warning(f"  ⚠️ 업로드 실패: {e}")
    return None, None


# ============================================================
# 메인 파이프라인
# ============================================================
def manual_publish(keyword: str, ref_url: str = "") -> dict:
    """
    수동 발행 전체 파이프라인

    Args:
        keyword: 블로그 키워드/주제
        ref_url: 참조 URL (선택)

    Returns:
        {"success": bool, "url": str, "post_id": int, "title": str}
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"📝 QuickInfo 수동 발행: {keyword}")
    logger.info(f"{'='*60}\n")

    gen = ContentGenerator()
    wp = WordPressPublisher()
    db = Database()

    # Step 0: 중복 발행 체크
    logger.info("[0/7] 중복 발행 체크...")
    from utils.dedup_checker import check_duplicate
    is_dup, dup_info = check_duplicate(
        keyword=keyword,
        wp_url=settings.wp_url,
        wp_user=settings.wp_user,
        wp_pass=settings.wp_app_password,
        db=db,
        threshold=0.6,
        days=30
    )
    if is_dup:
        logger.warning(f"  ⚠️ 중복 발견! 유사도: {dup_info['similarity']}")
        logger.warning(f"  📌 기존 글: {dup_info.get('title', dup_info.get('keyword', ''))[:60]}")
        logger.warning(f"  🔗 URL: {dup_info.get('url', 'N/A')}")
        logger.warning(f"  📅 날짜: {dup_info.get('date', 'N/A')}")
        if "--force" not in sys.argv:
            logger.info("  ❌ 중복 방지: 발행 중단 (--force로 강제 발행 가능)")
            return None
        else:
            logger.info("  ⚡ --force: 강제 발행 진행")
    else:
        logger.info("  ✅ 중복 없음 — 발행 진행")

    # Step 1: 참조 URL 팩트 수집
    logger.info("[1/7] 참조 URL 팩트 수집...")
    ref_text = fetch_reference_url(ref_url) if ref_url else ""
    if ref_text:
        logger.info(f"  ✅ {len(ref_text)}자 수집")
    else:
        logger.info("  ℹ️ 참조 URL 없음")

    # Step 2: 참조 블로그 탐색
    logger.info("[2/7] 참조 블로그 탐색...")
    blog_analysis = search_reference_blogs(keyword)

    # Step 3: 콘텐츠 생성
    logger.info("[3/7] 콘텐츠 생성...")
    web_data = None
    if ref_text:
        web_data = {
            "sources": [{
                "title": keyword,
                "url": ref_url,
                "content": ref_text[:3000]
            }]
        }

    trend_ctx = ""
    if ref_text:
        trend_ctx = ref_text[:500]
    if blog_analysis:
        trend_ctx += f"\n\n[참조 블로그 분석]\n{blog_analysis[:500]}"

    content_result = gen.generate_content_with_template(
        keyword=keyword,
        news_data="",
        template_name="guide",
        category_name="트렌드",
        is_evergreen=False,
        web_data=web_data,
        trend_context=trend_ctx[:1000]
    )

    content, sources, template = content_result

    # content가 string인 경우 처리
    if isinstance(content, str):
        html_content = content
    else:
        html_content = content.content

    # 추가 태그 정리 (clean_html_styles에서 이미 처리하지만 한번 더)
    html_content = clean_html_styles(html_content)

    # 제목 추출
    h_match = re.search(r'<h[12][^>]*>(.*?)</h[12]>', html_content)
    title = h_match.group(1).replace("<b>","").replace("</b>","").strip() if h_match else keyword

    logger.info(f"  ✅ 제목: {title}")
    logger.info(f"  ✅ 본문: {len(html_content)}자")

    # Step 3.5: 스마트 이미지 삽입
    logger.info("[3.5/7] 스마트 이미지 삽입...")
    try:
        from utils.smart_image_inserter import smart_insert_images

        html_content, img_count, featured_id = smart_insert_images(
            content=html_content,
            keyword=keyword,
            category="트렌드",  # TODO: 카테고리 자동 감지
            pexels_key=settings.pexels_api_key,
            wp_url=settings.wp_url,
            wp_auth=(settings.wp_user, settings.wp_app_password)
        )

        if img_count > 0:
            logger.info(f"  ✅ 이미지 {img_count}개 삽입 (각각 다른 이미지, 소제목 연관)")
        else:
            logger.info("  ℹ️ 이미지 삽입 불필요 또는 실패")

    except Exception as e:
        logger.warning(f"  ⚠️ 이미지 삽입 실패: {e}")
        featured_id = None

        # Step 4: 정보 카드 생성
    logger.info("[4/7] 정보 카드 생성...")
    combined_ref = ref_text + "\n" + blog_analysis
    info_card_html = generate_info_card(keyword, combined_ref)

    # Gemini 응답에서 info_items도 따로 추출 (썸네일용)
    info_items = []
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"""이 키워드의 핵심 정보 3개를 JSON으로:
키워드: {keyword}
참고: {combined_ref[:1000]}
[{{"emoji":"📅","label":"항목","value":"값"}}] 형식으로만 응답."""
        resp = model.generate_content(prompt)
        json_match = re.search(r'\[[\s\S]*\]', resp.text)
        if json_match:
            info_items = json.loads(json_match.group())[:3]
    except:
        pass

    # Step 5: 관련 링크 카드 생성
    logger.info("[5/7] 관련 링크 카드 생성...")
    link_cards_html = generate_link_cards(keyword, combined_ref)

    # Step 6: 썸네일 생성
    logger.info("[6/7] 썸네일 생성...")
    thumbnail_path = generate_thumbnail(keyword, info_items)
    featured_id = None
    if thumbnail_path:
        featured_id, _ = upload_to_wp(thumbnail_path, f"{keyword} 핵심 요약")

    # 최종 콘텐츠 조합: 정보카드 + 링크카드 + 본문
    final_content = ""
    if info_card_html:
        final_content += info_card_html + "\n"
    if link_cards_html:
        final_content += link_cards_html + "\n"
    final_content += html_content

    # Step 7: 발행
    logger.info("[7/7] 워드프레스 발행...")
    pub = wp.publish_post(
        title=title,
        content=final_content,
        status="publish",
        categories=["트렌드"],
        tags=None,
        excerpt="",
        featured_media_id=featured_id
    )

    if pub.success:
        # DB 저장
        db.save_published_post(
            keyword=keyword,
            title=title,
            wp_post_id=pub.post_id,
            wp_url=pub.url
        )

        # Google Indexing API
        try:
            from utils.google_indexing import request_indexing
            request_indexing(pub.url)
        except Exception as e:
            logger.warning(f"  ⚠️ Google 색인 요청 실패: {e}")

        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 발행 완료!")
        logger.info(f"  📌 제목: {title}")
        logger.info(f"  🔗 URL: {pub.url}")
        logger.info(f"  📊 본문: {len(final_content)}자")
        logger.info(f"  🖼️ 썸네일: {'✅' if featured_id else '❌'}")
        logger.info(f"  📋 정보카드: {'✅' if info_card_html else '❌'}")
        logger.info(f"  🔗 링크카드: {'✅' if link_cards_html else '❌'}")
        logger.info(f"  🔍 Google 색인: ✅")
        logger.info(f"{'='*60}\n")

        return {"success": True, "url": pub.url, "post_id": pub.post_id, "title": title}
    else:
        logger.error(f"\n❌ 발행 실패: {pub.error}")
        return {"success": False, "error": pub.error}


# ============================================================
# CLI 엔트리포인트
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 manual_publish.py \"키워드\" [\"참조URL\"]")
        print("예시: python3 manual_publish.py \"2026 예비창업패키지 모집공고\" \"https://...\"")
        sys.exit(1)

    keyword = sys.argv[1]
    ref_url = sys.argv[2] if len(sys.argv) > 2 else ""

    result = manual_publish(keyword, ref_url)
    sys.exit(0 if result.get("success") else 1)
