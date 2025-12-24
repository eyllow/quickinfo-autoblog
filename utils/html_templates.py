"""HTML 템플릿 함수 - 일관된 스타일 적용"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.styles import FONT_STYLES


def h1(text: str) -> str:
    """대제목 (글 시작) - 26px Bold"""
    s = FONT_STYLES["title_h1"]
    return f'''<h2 style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin: {s['margin']};
               line-height: {s['line_height']}; text-align: center;">{text}</h2>'''


def h2(text: str) -> str:
    """중간제목 - 22px SemiBold"""
    s = FONT_STYLES["title_h2"]
    return f'''<h3 style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin: {s['margin']};
               line-height: {s['line_height']}; text-align: center;">{text}</h3>'''


def h3(text: str) -> str:
    """소제목 (세로바 스타일) - 20px SemiBold"""
    s = FONT_STYLES["title_h3"]
    return f'''<div style="border-left: {s['border_left']}; padding-left: {s['padding_left']};
               margin: {s['margin']}; text-align: left;">
               <h4 style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin: 0;">{text}</h4></div>'''


def paragraph(text: str) -> str:
    """본문 텍스트 - 16px Regular"""
    s = FONT_STYLES["body"]
    return f'''<p style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin: {s['margin']};
               line-height: {s['line_height']};">{text}</p>'''


def image_caption(text: str) -> str:
    """사진 캡션 - 13px"""
    s = FONT_STYLES["image_caption"]
    return f'''<p style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin: {s['margin']}; text-align: center;">{text}</p>'''


def quote_box(text: str) -> str:
    """따옴표 강조 박스 - 18px 초록색"""
    s = FONT_STYLES["quote_box"]
    return f'''<div style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; background: {s['background']};
               padding: {s['padding']}; border-radius: {s['border_radius']};
               margin: {s['margin']}; text-align: center;">
               ❝ {text} ❞</div>'''


def highlight(text: str) -> str:
    """강조 텍스트 - 16px SemiBold 초록색"""
    s = FONT_STYLES["highlight"]
    return f'''<span style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']};">{text}</span>'''


def category_badge(category: str) -> str:
    """카테고리 뱃지"""
    s = FONT_STYLES["category_badge"]
    return f'''<div style="text-align: center; margin-bottom: 20px;">
               <span style="background: {s['background']}; color: {s['color']};
               padding: {s['padding']}; border-radius: {s['border_radius']};
               font-size: {s['size']}; font-weight: {s['weight']};">
               {category}</span></div>'''


def affiliate_notice() -> str:
    """파트너스 문구 - 11px 회색"""
    s = FONT_STYLES["affiliate_notice"]
    return f'''<p style="font-size: {s['size']}; font-weight: {s['weight']};
               color: {s['color']}; margin-top: {s['margin_top']}; text-align: center;">
               이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>'''


def coupang_button(url: str, text: str) -> str:
    """쿠팡 버튼"""
    s = FONT_STYLES["coupang_button"]
    return f'''<div style="text-align: center; margin: 30px 0;">
               <a href="{url}" target="_blank" rel="noopener noreferrer"
                  style="display: inline-block; background-color: {s['background']};
                  color: {s['color']}; padding: {s['padding']}; text-decoration: none;
                  border-radius: {s['border_radius']}; font-weight: {s['weight']};
                  font-size: {s['size']};">{text}</a></div>'''


def official_button(url: str, name: str) -> str:
    """공식 사이트 버튼"""
    s = FONT_STYLES["official_button"]
    return f'''<div style="text-align: center; margin: 30px 0;">
               <a href="{url}" target="_blank" rel="noopener"
                  style="display: inline-block; background-color: {s['background']};
                  color: {s['color']}; padding: {s['padding']}; text-decoration: none;
                  border-radius: {s['border_radius']}; font-weight: {s['weight']};
                  font-size: {s['size']};">{name} 바로가기</a></div>'''


def health_disclaimer() -> str:
    """건강 면책문구"""
    s = FONT_STYLES["health_disclaimer"]
    return f'''<div style="margin: 30px 0; padding: {s['padding']};
               background: {s['background']}; border-radius: {s['border_radius']};
               font-size: {s['size']}; text-align: left;">
               ⚠️ <strong>안내:</strong> 이 글은 정보 제공 목적이며, 의료적 조언이 아닙니다.
               증상이 심하거나 지속되면 반드시 전문의와 상담하세요.</div>'''


def table_start() -> str:
    """테이블 시작"""
    return '''<table style="width: 100%; max-width: 600px; margin: 25px auto;
               border-collapse: collapse; font-size: 15px;">'''


def table_header(*columns) -> str:
    """테이블 헤더"""
    s = FONT_STYLES["table_header"]
    cells = "".join([
        f'<th style="padding: {s["padding"]}; border-bottom: 2px solid #ddd; '
        f'font-weight: {s["weight"]}; color: {s["color"]}; '
        f'background: {s["background"]};">{col}</th>'
        for col in columns
    ])
    return f'<thead><tr style="background: {s["background"]};">{cells}</tr></thead><tbody>'


def table_row(*cells_data) -> str:
    """테이블 행"""
    s = FONT_STYLES["table_cell"]
    cells = "".join([
        f'<td style="padding: {s["padding"]}; border-bottom: 1px solid #eee; '
        f'color: {s["color"]};">{cell}</td>'
        for cell in cells_data
    ])
    return f'<tr>{cells}</tr>'


def table_end() -> str:
    """테이블 종료"""
    return '</tbody></table>'
