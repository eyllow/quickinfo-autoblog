"""블로그 폰트 스타일 가이드 - 전체 폰트 체계 통일"""

FONT_STYLES = {
    "title_h1": {
        "size": "26px",
        "weight": "700",
        "color": "#222",
        "margin": "0 0 25px 0",
        "line_height": "1.4"
    },
    "title_h2": {
        "size": "22px",
        "weight": "600",
        "color": "#333",
        "margin": "35px 0 20px 0",
        "line_height": "1.4"
    },
    "title_h3": {
        "size": "20px",
        "weight": "600",
        "color": "#333",
        "margin": "30px 0 15px 0",
        "border_left": "3px solid #333",
        "padding_left": "12px"
    },
    "body": {
        "size": "16px",
        "weight": "400",
        "color": "#444",
        "margin": "12px 0",
        "line_height": "2.0"
    },
    "table_header": {
        "size": "15px",
        "weight": "600",
        "color": "#333",
        "background": "#f8f9fa",
        "padding": "14px"
    },
    "table_cell": {
        "size": "15px",
        "weight": "400",
        "color": "#555",
        "padding": "14px"
    },
    "image_caption": {
        "size": "13px",
        "weight": "400",
        "color": "#888",
        "margin": "8px 0 25px 0"
    },
    "highlight": {
        "size": "16px",
        "weight": "600",
        "color": "#2e8b57"
    },
    "quote_box": {
        "size": "18px",
        "weight": "500",
        "color": "#2e8b57",
        "background": "#f8f9fa",
        "padding": "20px",
        "border_radius": "8px",
        "margin": "30px 0"
    },
    "affiliate_notice": {
        "size": "11px",
        "weight": "400",
        "color": "#999",
        "margin_top": "50px"
    },
    "category_badge": {
        "size": "13px",
        "weight": "500",
        "color": "#1a73e8",
        "background": "#e8f4f8",
        "padding": "5px 12px",
        "border_radius": "15px"
    },
    "coupang_button": {
        "size": "16px",
        "weight": "600",
        "color": "white",
        "background": "#ff6b35",
        "padding": "16px 40px",
        "border_radius": "8px"
    },
    "official_button": {
        "size": "16px",
        "weight": "600",
        "color": "white",
        "background": "#3182f6",
        "padding": "16px 40px",
        "border_radius": "8px"
    },
    "health_disclaimer": {
        "size": "13px",
        "weight": "400",
        "color": "#856404",
        "background": "#fff3cd",
        "padding": "15px",
        "border_radius": "8px"
    }
}


def get_style_string(style_name: str) -> str:
    """스타일을 inline CSS 문자열로 변환"""
    if style_name not in FONT_STYLES:
        return ""

    style = FONT_STYLES[style_name]
    parts = []

    if "size" in style:
        parts.append(f"font-size: {style['size']}")
    if "weight" in style:
        parts.append(f"font-weight: {style['weight']}")
    if "color" in style:
        parts.append(f"color: {style['color']}")
    if "background" in style:
        parts.append(f"background: {style['background']}")
    if "margin" in style:
        parts.append(f"margin: {style['margin']}")
    if "padding" in style:
        parts.append(f"padding: {style['padding']}")
    if "line_height" in style:
        parts.append(f"line-height: {style['line_height']}")
    if "border_radius" in style:
        parts.append(f"border-radius: {style['border_radius']}")
    if "border_left" in style:
        parts.append(f"border-left: {style['border_left']}")
    if "padding_left" in style:
        parts.append(f"padding-left: {style['padding_left']}")
    if "margin_top" in style:
        parts.append(f"margin-top: {style['margin_top']}")

    return "; ".join(parts)
