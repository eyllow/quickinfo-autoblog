"""키워드 기반 정보 카드 스타일 썸네일 생성"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
img = Image.new('RGB', (W, H))
draw = ImageDraw.Draw(img)

# 그라데이션 배경 (짙은 블루)
for y in range(H):
    r = int(20 + (y/H) * 15)
    g = int(30 + (y/H) * 20)
    b = int(80 + (y/H) * 40)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# 상단 빨간 악센트 바
draw.rectangle([(0, 0), (W, 5)], fill='#e94560')

# 폰트
font_paths = [
    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    '/Library/Fonts/AppleSDGothicNeo.ttc',
]
title_font = sub_font = badge_font = small_font = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            title_font = ImageFont.truetype(fp, 52)
            sub_font = ImageFont.truetype(fp, 36)
            badge_font = ImageFont.truetype(fp, 28)
            small_font = ImageFont.truetype(fp, 22)
            break
        except:
            continue

if not title_font:
    title_font = ImageFont.load_default()
    sub_font = title_font
    badge_font = title_font
    small_font = title_font

# 뱃지 (중소벤처기업부)
badge_text = "중소벤처기업부 공고"
draw.rounded_rectangle([(80, 60), (370, 105)], radius=8, fill='#e94560')
draw.text((225, 82), badge_text, fill='white', font=small_font, anchor='mm')

# 메인 타이틀
draw.text((W//2, 190), "2026 예비창업패키지", fill='#ffffff', font=title_font, anchor='mm')
draw.text((W//2, 255), "예비창업자 모집공고", fill='#e94560', font=sub_font, anchor='mm')

# 핵심 정보 카드들
card_y = 330
cards = [
    ("📅 신청기간", "2026.03.06 ~ 03.24"),
    ("💰 지원금액", "평균 4,000만원"),
    ("👤 신청대상", "사업자등록증 미보유 예비창업자"),
]

for i, (label, value) in enumerate(cards):
    y = card_y + i * 65
    # 카드 배경
    draw.rounded_rectangle([(100, y), (1100, y+52)], radius=8, fill=(255,255,255,30))
    draw.rounded_rectangle([(100, y), (1100, y+52)], radius=8, outline=(255,255,255,60), width=1)
    # 라벨
    draw.text((130, y+26), label, fill='#a0b0d0', font=small_font, anchor='lm')
    # 값
    draw.text((450, y+26), value, fill='#ffffff', font=badge_font, anchor='lm')

# 하단 QuickInfo 로고
draw.text((W//2, 580), "QuickInfo", fill=(120,140,180), font=small_font, anchor='mm')

# 장식 점
for x in range(100, 1100, 40):
    draw.ellipse([(x, 545), (x+3, 548)], fill='#e94560')

out = '/Users/younghyunjung/.openclaw/workspace/quickinfo-thumbnail-startup.png'
img.save(out, 'PNG', quality=95)
print(f"Saved: {out}")
