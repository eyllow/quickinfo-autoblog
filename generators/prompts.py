"""카테고리별 프롬프트 템플릿 - 고품질 블로그 글 생성용 (AdSense 최적화)"""
import re
import random
from datetime import datetime

# =============================================================================
# Google AdSense 승인용 금지 표현 목록
# =============================================================================

BANNED_EXPRESSIONS = [
    # 과도한 감탄사/이모티콘
    "ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "ㅜㅜ", "헐", "대박",
    # 과도한 강조 표현
    "완전 핵심", "진짜 진짜", "완전 강추", "무조건",
    "꿀팁", "핵꿀팁", "알짜팁",
    # 클릭베이트 표현
    "충격", "경악", "미친", "역대급", "레전드",
    # AI 탐지 패턴
    "저도 솔직히", "솔직히 저도", "ㅋㅋㅋ 이거 진짜",
    "여기서 꿀팁 하나", "이건 진짜 꿀팁",
    # 과도한 구어체
    "~거든요", "~잖아요", "~다니까요",
]

# =============================================================================
# 전문가 페르소나 프롬프트 (AI 탐지 회피 + 전문성)
# =============================================================================

PROFESSIONAL_PERSONA = """
당신은 7년 경력의 금융/생활정보 전문 에디터입니다.
경제매체와 정부 기관 보도자료를 분석하여 정확한 정보를 전달합니다.

[글쓰기 원칙]
1. 사실 중심: 공식 출처와 통계 데이터 기반
2. 독자 가치: 실제 적용 가능한 구체적 정보 제공
3. 명확한 구조: 논리적 흐름과 단계별 안내
4. 객관적 톤: 균형 잡힌 분석과 다양한 관점 제시

[문체 규칙]
- 정중한 해요체 사용 ("~입니다" 아닌 "~해요")
- 전문 용어는 괄호 안에 쉬운 설명 추가
- 구체적인 수치와 예시로 설명
- 출처 명시 가능한 정보 우선

[절대 금지]
- 감탄사 남발 (ㅋㅋ, ㅎㅎ, 헐, 대박)
- 과장된 표현 (완전, 진짜진짜, 무조건)
- 클릭베이트 문구 (충격, 경악, 미친)
- 근거 없는 주장이나 추측
"""

# =============================================================================
# 제목-본문 일관성 규칙
# =============================================================================

CONTENT_CONSISTENCY_RULES = """
[제목-본문 일관성 규칙]

1. 제목에 숫자가 포함될 경우:
   - "5가지 방법" → 본문에 정확히 5개 항목
   - 각 항목은 번호 또는 소제목으로 명확히 구분

2. 제목 유형별 본문 구조:
   - "N가지 방법" → 번호 리스트 필수
   - "완벽 가이드" → 단계별 설명
   - "총정리" → 표 또는 요약 포함
   - "비교" → 비교 표 필수

3. 자연스러운 흐름:
   - 억지로 숫자 맞추지 않음
   - 내용이 부족하면 제목의 숫자 조정
"""

# =============================================================================
# 5가지 글 형식 (FORMAT) 정의
# =============================================================================

CONTENT_FORMATS = {
    "info_guide": {
        "name": "정보 가이드형",
        "description": "단계별 넘버링 + 체크리스트 박스 + 핵심 요약 카드",
        "structure_guide": """
[글 형식: 정보 가이드형]
- Step 1, Step 2... 단계별 넘버링으로 구성
- 각 단계마다 ✅ 체크리스트 박스 HTML 포함
- 섹션 끝마다 핵심 요약 카드(배경색 박스) 배치
- 마지막에 전체 요약 체크리스트 제공
""",
    },
    "news_analysis": {
        "name": "뉴스 분석형",
        "description": "리드 문단 + 5W1H 구조 + 타임라인 + 전문가 의견 인용",
        "structure_guide": """
[글 형식: 뉴스 분석형]
- 첫 문단에 핵심 한 줄 리드 (굵게 강조)
- 5W1H(누가, 언제, 어디서, 무엇을, 왜, 어떻게) 구조
- 시간순 타임라인 HTML 포함 (세로 점선 + 날짜/이벤트)
- "전문가는 ~라고 분석해요" 스타일 인용 박스 포함
- 배경 → 현황 → 전망 순서로 전개
""",
    },
    "comparison": {
        "name": "비교 분석형",
        "description": "VS 비교 표 + 장단점 카드 + 상황별 추천 + 별점",
        "structure_guide": """
[글 형식: 비교 분석형]
- 핵심 비교 항목을 HTML 테이블로 정리 (A vs B)
- 각 옵션별 장점(녹색)/단점(빨간색) 카드 박스 배치
- "이런 분에게 추천" 상황별 가이드
- ★ 별점 또는 점수 (예: 가성비 ★★★★☆)
- 최종 추천 요약 박스
""",
    },
    "experience": {
        "name": "실전 경험형",
        "description": "문제 상황 → 해결 과정 → 결과 공유 (스토리텔링)",
        "structure_guide": """
[글 형식: 실전 경험형]
- 도입: 구체적인 문제 상황 제시 ("이런 상황, 겪어보셨나요?")
- 중반: 해결 과정을 단계별 서술 (시행착오 포함)
- 후반: 결과 공유 + 배운 점 정리
- 핵심 포인트는 강조 박스로 분리
- 독자 공감을 유도하는 질문형 문장 활용
- 스토리텔링이지만 팩트 기반 (과장 금지)
""",
    },
    "qa_deep": {
        "name": "Q&A 심층형",
        "description": "핵심 질문 중심 구성, 각 질문에 깊이 있는 답변",
        "structure_guide": """
[글 형식: Q&A 심층형]
- 도입에서 "많은 분들이 궁금해하는 핵심 질문" 안내
- 각 Q는 <strong>Q. 질문</strong> 형식으로 소제목 대신 사용
- 각 A는 최소 300자 이상의 상세 답변
- 답변 안에 표, 리스트, 강조 박스 등 다양한 요소 혼합
- 최소 7개 이상의 Q&A로 구성
- 마지막에 "보너스 Q&A" 추가
""",
    },
}

# 카테고리별 추천 형식 매핑
CATEGORY_FORMAT_MAP = {
    "finance": ["info_guide", "qa_deep", "news_analysis"],
    "product": ["comparison", "experience", "info_guide"],
    "celebrity": ["news_analysis", "qa_deep", "experience"],
    "health": ["info_guide", "qa_deep", "experience"],
    "lifestyle": ["info_guide", "experience", "qa_deep"],
    "education": ["info_guide", "qa_deep", "comparison"],
    "trend": ["news_analysis", "qa_deep", "comparison"],
}

def select_content_format(category_template: str = "trend") -> dict:
    """카테고리에 맞는 글 형식 랜덤 선택"""
    preferred = CATEGORY_FORMAT_MAP.get(category_template, list(CONTENT_FORMATS.keys()))
    format_key = random.choice(preferred)
    return {**CONTENT_FORMATS[format_key], "key": format_key}


# =============================================================================
# 5가지 소제목 HTML 스타일
# =============================================================================

HEADING_STYLES = {
    "gradient_bar": {
        "name": "배경색 그라디언트 바",
        "html": '''<div style="background: linear-gradient(135deg, {color1}, {color2}); padding: 12px 18px; border-radius: 6px; margin: 30px 0 15px 0;">
  <h4 style="font-size: 20px; font-weight: 600; color: #fff; margin: 0;">{title}</h4>
</div>''',
        "colors": [
            ("#2563eb", "#1d4ed8"),
            ("#059669", "#047857"),
            ("#7c3aed", "#6d28d9"),
            ("#dc2626", "#b91c1c"),
            ("#d97706", "#b45309"),
        ]
    },
    "icon_text": {
        "name": "좌측 아이콘 + 텍스트",
        "html": '''<div style="display: flex; align-items: center; gap: 10px; margin: 30px 0 15px 0;">
  <span style="font-size: 24px;">{icon}</span>
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">{title}</h4>
</div>''',
        "icons": ["📌", "💡", "📋", "🔍", "📊", "🎯", "⚡", "🔑", "📝", "🏷️"]
    },
    "underline": {
        "name": "밑줄 강조",
        "html": '''<h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 30px 0 15px 0; padding-bottom: 8px; border-bottom: 3px solid {color};">{title}</h4>''',
        "colors": ["#2563eb", "#059669", "#7c3aed", "#dc2626", "#d97706"]
    },
    "number_badge": {
        "name": "번호 원형 배지",
        "html": '''<div style="display: flex; align-items: center; gap: 12px; margin: 30px 0 15px 0;">
  <span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: {color}; color: #fff; border-radius: 50%; font-weight: 700; font-size: 15px;">{number}</span>
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">{title}</h4>
</div>''',
        "colors": ["#2563eb", "#059669", "#7c3aed", "#dc2626", "#d97706"]
    },
    "card_box": {
        "name": "카드형 박스 소제목",
        "html": '''<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin: 30px 0 15px 0;">
  <h4 style="font-size: 20px; font-weight: 600; color: #1e293b; margin: 0;">{title}</h4>
</div>''',
    },
}

def get_heading_style_instruction() -> tuple:
    """랜덤 소제목 스타일 선택 후 (style_key, 프롬프트 지시) 반환"""
    style_key = random.choice(list(HEADING_STYLES.keys()))
    style = HEADING_STYLES[style_key]

    if style_key == "gradient_bar":
        c1, c2 = random.choice(style["colors"])
        instruction = f"""소제목 HTML은 배경 그라디언트 바 스타일을 사용하세요:
<div style="background: linear-gradient(135deg, {c1}, {c2}); padding: 12px 18px; border-radius: 6px; margin: 30px 0 15px 0;">
  <h4 style="font-size: 20px; font-weight: 600; color: #fff; margin: 0;">소제목 텍스트</h4>
</div>"""
    elif style_key == "icon_text":
        instruction = f"""소제목 HTML은 좌측 아이콘 + 텍스트 스타일을 사용하세요. 아이콘은 {', '.join(style['icons'][:5])} 중 적절한 것을 선택:
<div style="display: flex; align-items: center; gap: 10px; margin: 30px 0 15px 0;">
  <span style="font-size: 24px;">📌</span>
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">소제목 텍스트</h4>
</div>"""
    elif style_key == "underline":
        color = random.choice(style["colors"])
        instruction = f"""소제목 HTML은 밑줄 강조 스타일을 사용하세요:
<h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 30px 0 15px 0; padding-bottom: 8px; border-bottom: 3px solid {color};">소제목 텍스트</h4>"""
    elif style_key == "number_badge":
        color = random.choice(style["colors"])
        instruction = f"""소제목 HTML은 번호 원형 배지 스타일을 사용하세요 (번호를 1, 2, 3... 순서대로):
<div style="display: flex; align-items: center; gap: 12px; margin: 30px 0 15px 0;">
  <span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: {color}; color: #fff; border-radius: 50%; font-weight: 700; font-size: 15px;">1</span>
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">소제목 텍스트</h4>
</div>"""
    else:  # card_box
        instruction = """소제목 HTML은 카드형 박스 스타일을 사용하세요:
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; margin: 30px 0 15px 0;">
  <h4 style="font-size: 20px; font-weight: 600; color: #1e293b; margin: 0;">소제목 텍스트</h4>
</div>"""

    return style_key, instruction


# =============================================================================
# 강조 박스 4종
# =============================================================================

HIGHLIGHT_BOXES = {
    "info": '''<div style="margin: 20px 0; padding: 18px; background: #eff6ff; border-left: 4px solid #2563eb; border-radius: 6px;">
  <p style="margin: 0; color: #1e40af; font-size: 15px;"><strong>ℹ️ 참고</strong></p>
  <p style="margin: 8px 0 0 0; color: #1e3a5f; font-size: 15px; line-height: 1.7;">{content}</p>
</div>''',
    "warning": '''<div style="margin: 20px 0; padding: 18px; background: #fffbeb; border-left: 4px solid #d97706; border-radius: 6px;">
  <p style="margin: 0; color: #92400e; font-size: 15px;"><strong>⚠️ 주의</strong></p>
  <p style="margin: 8px 0 0 0; color: #78350f; font-size: 15px; line-height: 1.7;">{content}</p>
</div>''',
    "success": '''<div style="margin: 20px 0; padding: 18px; background: #ecfdf5; border-left: 4px solid #059669; border-radius: 6px;">
  <p style="margin: 0; color: #065f46; font-size: 15px;"><strong>💡 팁</strong></p>
  <p style="margin: 8px 0 0 0; color: #064e3b; font-size: 15px; line-height: 1.7;">{content}</p>
</div>''',
    "quote": '''<div style="margin: 20px 0; padding: 18px; background: #f9fafb; border-left: 4px solid #6b7280; border-radius: 6px;">
  <p style="margin: 0; color: #374151; font-size: 15px; font-style: italic; line-height: 1.7;">"{content}"</p>
</div>''',
}

HIGHLIGHT_BOX_INSTRUCTION = """
[강조 박스 사용법 - 4가지 종류를 골고루 사용하세요]

1. 정보 박스 (파란색):
<div style="margin: 20px 0; padding: 18px; background: #eff6ff; border-left: 4px solid #2563eb; border-radius: 6px;">
  <p style="margin: 0; color: #1e40af; font-size: 15px;"><strong>ℹ️ 참고</strong></p>
  <p style="margin: 8px 0 0 0; color: #1e3a5f; font-size: 15px; line-height: 1.7;">내용</p>
</div>

2. 주의 박스 (노란색):
<div style="margin: 20px 0; padding: 18px; background: #fffbeb; border-left: 4px solid #d97706; border-radius: 6px;">
  <p style="margin: 0; color: #92400e; font-size: 15px;"><strong>⚠️ 주의</strong></p>
  <p style="margin: 8px 0 0 0; color: #78350f; font-size: 15px; line-height: 1.7;">내용</p>
</div>

3. 팁 박스 (녹색):
<div style="margin: 20px 0; padding: 18px; background: #ecfdf5; border-left: 4px solid #059669; border-radius: 6px;">
  <p style="margin: 0; color: #065f46; font-size: 15px;"><strong>💡 팁</strong></p>
  <p style="margin: 8px 0 0 0; color: #064e3b; font-size: 15px; line-height: 1.7;">내용</p>
</div>

4. 인용 박스 (회색):
<div style="margin: 20px 0; padding: 18px; background: #f9fafb; border-left: 4px solid #6b7280; border-radius: 6px;">
  <p style="margin: 0; color: #374151; font-size: 15px; font-style: italic; line-height: 1.7;">"인용 내용"</p>
</div>
"""


# =============================================================================
# 공통 스타일 규칙 (AdSense 최적화) - 개선
# =============================================================================

COMMON_STYLE = """
[메타 언급 절대 금지]
* "제공해주신", "가이드라인", "작성하겠습니다" 등 금지
* AI가 작성했다는 것을 암시하는 문구 금지
* 프롬프트 지시사항에 대한 응답 금지
* 오직 블로그 본문 내용만 출력

[AdSense 승인을 위한 필수 규칙]

1. 콘텐츠 품질
   - 최소 5,000자 이상의 상세한 정보 (약 2,000단어)
   - 각 섹션별 최소 400자 이상
   - 독창적인 분석과 통찰 포함
   - 독자에게 실질적인 가치 제공
   - 정확한 정보와 신뢰할 수 있는 출처

2. 금지 표현 (사용 시 승인 거부)
   - 감탄사: ㅋㅋ, ㅎㅎ, ㅠㅠ, 헐, 대박
   - 과장 표현: 완전, 진짜진짜, 무조건, 핵심 중의 핵심
   - 클릭베이트: 충격, 경악, 미친, 역대급
   - 꿀팁, 핵꿀팁, 알짜팁 (대신 "실용적인 방법", "효과적인 팁" 사용)

3. 이모지 사용 규칙
   - 전체 글에서 최대 2개만 사용
   - 소제목에만 1개씩 배치
   - 본문에는 이모지 사용 금지

4. 문체 규칙
   - 정중한 해요체 ("~해요", "~예요")
   - 전문적이면서 친근한 톤
   - 짧고 명확한 문장 (40자 이내)
   - 객관적 사실 중심 서술

5. SEO 규칙
   - 키워드를 제목, 첫 문단, 소제목(2개 이상), 본문에 자연스럽게 분산
   - 첫 100자 안에 핵심 키워드 필수 포함
   - 관련 LSI 키워드(유의어, 관련어) 자연스럽게 포함
   - FAQ 섹션은 구조화 데이터 대비: <div class="faq-item"><strong>Q. 질문</strong><p>답변</p></div>

{heading_style_instruction}

{highlight_box_instruction}

[정렬 규칙]
* 중앙 정렬: 대제목, 카테고리 뱃지, 이미지 캡션
* 왼쪽 정렬: 소제목, 본문, 리스트, 표, FAQ

[HTML 형식]
- 전체를 <div style="max-width: 700px; margin: 0 auto; font-size: 16px; line-height: 1.9; color: #333;">로 감싸기

- 대제목 (중앙 정렬):
<h2 style="font-size: 26px; font-weight: 700; color: #222; margin: 0 0 25px 0; line-height: 1.4; text-align: center;">
  대제목 내용
</h2>

- 본문 텍스트 (왼쪽 정렬):
<p style="font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;">
  본문 내용
</p>

- 리스트 (왼쪽 정렬):
<ul style="text-align: left; padding-left: 20px; margin: 15px 0;">
  <li style="margin: 8px 0;">항목 1</li>
  <li style="margin: 8px 0;">항목 2</li>
</ul>

- 테이블 스타일:
<table style="width: 100%; max-width: 600px; margin: 25px 0; border-collapse: collapse; font-size: 15px; text-align: left;">
  <thead>
    <tr style="background: #f8f9fa;">
      <th style="padding: 14px; border-bottom: 2px solid #ddd; font-weight: 600; color: #333;">구분</th>
      <th style="padding: 14px; border-bottom: 2px solid #ddd; font-weight: 600; color: #333;">내용</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 14px; border-bottom: 1px solid #eee; color: #555;">항목</td>
      <td style="padding: 14px; border-bottom: 1px solid #eee; color: #333;">설명</td>
    </tr>
  </tbody>
</table>

- 사진 캡션 (중앙 정렬):
<p style="font-size: 13px; color: #888; margin: 8px 0 25px 0; text-align: center;">
  캡션 내용
</p>

[이미지 태그]
- [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 태그 배치
- 각 이미지 태그 위에 영문 키워드 주석 추가
- 형식: <!-- IMG_CONTEXT: 영문 키워드 2~4개 -->

[메타 설명]
- 글 끝에 [META]150자 이내 SEO 메타 설명[/META] 형식으로 추가
"""

SYSTEM_PROMPT = """
당신은 7년 경력의 전문 에디터입니다.

핵심 역할:
- 정확하고 유용한 정보를 명확하게 전달
- 독자가 실제로 활용할 수 있는 구체적인 가이드 제공
- 신뢰할 수 있는 출처 기반의 객관적 서술

문체 원칙:
- 정중한 해요체 사용
- 전문적이면서 이해하기 쉬운 설명
- 구체적인 수치와 예시 활용
- 짧고 명확한 문장

금지 사항:
- 감탄사/이모티콘 남발 (ㅋㅋ, ㅎㅎ, 헐)
- 과장 표현 (대박, 완전, 무조건)
- 클릭베이트 문구 (충격, 경악)
- 꿀팁, 핵꿀팁 (대신 "효과적인 방법" 사용)
"""

# =============================================================================
# 콘텐츠 후처리 함수 (AdSense 최적화)
# =============================================================================

def clean_ai_content(content: str) -> str:
    """AI 생성 콘텐츠에서 금지 표현 제거"""
    result = content

    replacements = {
        "ㅋㅋㅋ": "",
        "ㅋㅋ": "",
        "ㅎㅎㅎ": "",
        "ㅎㅎ": "",
        "ㅠㅠ": "",
        "ㅜㅜ": "",
        "헐": "",
        "대박": "주목할 만한",
        "완전 핵심": "핵심",
        "진짜 진짜": "정말",
        "진짜진짜": "정말",
        "무조건": "반드시",
        "꿀팁": "유용한 팁",
        "핵꿀팁": "효과적인 방법",
        "알짜팁": "실용적인 팁",
        "충격": "주목할",
        "경악": "놀라운",
        "미친": "인상적인",
        "역대급": "주목할 만한",
        "레전드": "인상적인",
        "완전 강추": "추천",
        "강추": "추천",
        "저도 솔직히": "사실",
        "솔직히 저도": "사실",
        "여기서 꿀팁 하나!": "추가로 알아두면 좋은 점이 있어요.",
        "이건 진짜 꿀팁이에요": "이것은 효과적인 방법이에요",
    }

    for old, new in replacements.items():
        result = result.replace(old, new)

    result = re.sub(r'!{2,}', '!', result)
    result = re.sub(r'\?{2,}', '?', result)
    result = re.sub(r' {2,}', ' ', result)

    return result


def limit_emojis(content: str, max_emojis: int = 2) -> str:
    """이모지 개수 제한"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )

    emojis = emoji_pattern.findall(content)
    if len(emojis) <= max_emojis:
        return content

    result = content
    emoji_count = 0
    for match in emoji_pattern.finditer(content):
        emoji_count += 1
        if emoji_count > max_emojis:
            result = result.replace(match.group(), '', 1)

    return result


def post_process_content(content: str) -> str:
    """콘텐츠 후처리 통합 함수"""
    result = clean_ai_content(content)
    result = limit_emojis(result, max_emojis=2)
    return result


# =============================================================================
# 카테고리별 프롬프트 템플릿 (개선 - 형식 다양화 포함)
# =============================================================================

def _build_common_style():
    """소제목 스타일, 강조 박스 지시를 포함한 COMMON_STYLE 생성"""
    _, heading_instruction = get_heading_style_instruction()
    return COMMON_STYLE.format(
        heading_style_instruction=heading_instruction,
        highlight_box_instruction=HIGHLIGHT_BOX_INSTRUCTION,
    )


def _build_category_prompt(keyword: str, news_data: str, category: str, extra_sections: str, format_info: dict) -> str:
    """카테고리 공통 프롬프트 빌더"""
    common = _build_common_style()

    return f"""{common}

{format_info['structure_guide']}

주제: '{keyword}'
카테고리: {category}
참고 데이터: {news_data}

[분량 기준]
- 전체 최소 5,000자 (약 2,000단어)
- 서론: 최소 400자
- 각 본문 섹션: 최소 400자
- FAQ: 최소 500자 (5개 이상)
- 마무리: 최소 200자

{extra_sections}

[필수 태그]
- [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 배치
- [OFFICIAL_LINK]: 공식 사이트 위치
- [COUPANG]: 쿠팡 상품 위치
- [AFFILIATE_NOTICE]: 제휴 안내
- [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 불확실한 수치/날짜 언급 금지
- 과장된 표현 금지
- 감탄사(ㅋㅋ, ㅎㅎ) 사용 금지
- border-left 세로바 소제목 사용 금지 (위에 지정된 소제목 스타일만 사용)

결과는 순수 HTML만 출력하세요.
"""


FINANCE_EXTRA = """
[재테크/정보 카테고리 특화]
- 핵심 개념 정의 + 왜 알아야 하는지
- 주요 절차/방법을 테이블로 정리
- 필요 서류, 조건, 기한 명시
- 실전 적용 시 유용한 정보 5가지 이상
- FAQ 5개 이상 (실제 많이 검색되는 질문)
"""

PRODUCT_EXTRA = """
[IT/제품 카테고리 특화]
- 출시일, 가격, 주요 사양 테이블
- 경쟁 제품과 상세 스펙 비교 테이블
- 장점 3-5개 (실사용 관점)
- 단점 2-3개 (객관적 분석)
- 추천 대상 유형 3가지
- 구매 전 확인사항
"""

CELEBRITY_EXTRA = """
[연예/인물 카테고리 특화]
- 인물 사진 사용 불가 (저작권/초상권) → 무대, 콘서트, 이벤트 분위기 이미지만
- 외모 묘사 최소화
- 기본 프로필 (본명, 생년월일, 소속사, 데뷔) 테이블
- 대표작/수상 이력
- 최근 소식 (뉴스 기반)
- 향후 활동 전망
- 루머/사생활 금지
"""

HEALTH_EXTRA = """
[건강/생활 카테고리 특화]
- 원인과 배경 (전문 용어 쉽게 풀어서)
- 단계별 개선 방법 가이드
- 실제 도움이 되는 실천 팁
- 주의사항/흔한 실수
- FAQ 5개 이상
- [DISCLAIMER] 건강 면책문구 포함
- 의료 진단/처방/특정 약품 추천 금지
"""

LIFESTYLE_EXTRA = """
[생활정보 카테고리 특화]
- 해당 주제의 중요성과 일상 관련성
- 바로 따라할 수 있는 실천 방법
- 유용한 정보 5가지 이상
- 피해야 할 실수들
- FAQ 5개 이상
"""

EDUCATION_EXTRA = """
[취업/교육 카테고리 특화]
- 핵심 개념 + 관련 제도/자격 안내
- 준비 방법 체크리스트 (테이블)
- 합격/성공 조언
- 흔한 실수와 주의사항
- FAQ 5개 이상
"""

TREND_EXTRA = """
[트렌드/일반 카테고리 특화]
- 현재 화제가 된 배경과 이유
- 핵심 포인트 정리
- 다양한 반응/여론
- 향후 전망과 분석
"""

CATEGORY_EXTRA_MAP = {
    "finance": ("재테크/정보", FINANCE_EXTRA),
    "product": ("IT/제품", PRODUCT_EXTRA),
    "celebrity": ("연예/인물", CELEBRITY_EXTRA),
    "health": ("건강/생활", HEALTH_EXTRA),
    "lifestyle": ("생활정보", LIFESTYLE_EXTRA),
    "education": ("취업/교육", EDUCATION_EXTRA),
    "trend": ("트렌드/일반", TREND_EXTRA),
}


# 레거시 호환용 변수들
FINANCE_TEMPLATE = "legacy"
PRODUCT_TEMPLATE = "legacy"
CELEBRITY_TEMPLATE = "legacy"
HEALTH_TEMPLATE = "legacy"
LIFESTYLE_TEMPLATE = "legacy"
EDUCATION_TEMPLATE = "legacy"
TREND_TEMPLATE = "legacy"


# =============================================================================
# 에버그린 콘텐츠 전용 템플릿 (AdSense 최적화)
# =============================================================================

def get_evergreen_template():
    """현재 날짜를 포함한 에버그린 템플릿 반환"""
    current_year = datetime.now().year
    current_month = datetime.now().month
    common = _build_common_style()
    format_info = select_content_format("lifestyle")

    return f"""{common}

{format_info['structure_guide']}

당신은 7년 경력의 전문 에디터입니다.
독자가 실제로 도움받을 수 있는 상세하고 정확한 정보를 제공하세요.

[현재 시점]: {current_year}년 {current_month}월 기준

[핵심 원칙]
1. 정확한 정보: 공식 출처와 통계 데이터 기반
2. 실용적 가치: 독자가 바로 적용할 수 있는 구체적 방법
3. 명확한 구조: 논리적 흐름과 단계별 안내
4. 객관적 서술: 과장 없이 사실 중심으로 작성

[분량 기준]
- 전체 최소 6,000자 (약 2,500단어)
- 각 섹션 최소 500자
- FAQ 최소 600자 (5개 이상, 각 답변 100자 이상)

[품질 기준]

1. 도입부
   - 해당 주제의 중요성과 현황
   - 최신 통계/수치 포함 (예: "{current_year}년 기준 약 OO만 명...")
   - 이 글에서 다룰 내용 안내

2. 본문 구조 (주제에 맞게 구성)
   - "방법" 주제 → 단계별 가이드
   - "비교" 주제 → 장단점 분석 표
   - "신청/절차" 주제 → 순서도 + 필요 서류
   - 각 섹션별 강조 박스(정보/주의/팁/인용) 최소 1개 포함

3. 실용적 정보
   - 표(테이블)로 정리할 수 있는 정보는 반드시 표로
   - 구체적인 금액, 기한, 조건 명시
   - 공식 사이트/기관 안내

4. FAQ (5~7개)
   - 실제로 많이 검색하는 질문
   - 상세한 답변 (각 100자 이상)
   - <div class="faq-item"> 래핑

5. 마무리
   - 핵심 요약 2~3줄
   - 다음 단계 안내

주제: '{{keyword}}'
카테고리: 에버그린 정보성 콘텐츠
참고 데이터: {{news_data}}

[연도 표기 규칙]
- 현재 연도: {current_year}년
- 과거 연도 언급 금지
- "현재 기준", "최신 기준" 등 상대적 표현 권장

[이미지 태그 배치]
- [IMAGE_1]: 도입부 다음
- [IMAGE_2]: 핵심 정보 섹션 중간
- [IMAGE_3]: 실전 팁/주의사항 다음
- [IMAGE_4]: 마무리 전

[필수 태그]
- [OFFICIAL_LINK], [COUPANG], [AFFILIATE_NOTICE]
- [META]SEO 메타 설명 150자[/META]

[금지 표현]
- 감탄사, 과장, 클릭베이트
- 꿀팁 → "효과적인 방법"
- 메타 표현: "제공해주신", "작성하겠습니다"
- border-left 세로바 소제목 사용 금지

결과는 순수 HTML만 출력하세요.
"""

# 레거시 호환용 변수
EVERGREEN_STYLE = ""
EVERGREEN_TEMPLATE = None
HUMAN_PERSONA_PROMPT = ""

# =============================================================================
# 템플릿 매핑 (레거시 호환)
# =============================================================================

CATEGORY_TEMPLATES = {
    "finance": FINANCE_TEMPLATE,
    "product": PRODUCT_TEMPLATE,
    "celebrity": CELEBRITY_TEMPLATE,
    "health": HEALTH_TEMPLATE,
    "lifestyle": LIFESTYLE_TEMPLATE,
    "education": EDUCATION_TEMPLATE,
    "trend": TREND_TEMPLATE,
}

def get_template(template_name: str, is_evergreen: bool = False, keyword: str = "", news_data: str = "") -> str:
    """
    템플릿 이름으로 프롬프트 반환 (개선 버전 - 형식 다양화 + 소제목 스타일 다양화)
    """
    if is_evergreen:
        template = get_evergreen_template()
        return template

    # 카테고리별 형식 선택
    format_info = select_content_format(template_name)
    cat_label, extra = CATEGORY_EXTRA_MAP.get(template_name, ("트렌드/일반", TREND_EXTRA))

    return _build_category_prompt(
        keyword=keyword or "{keyword}",
        news_data=news_data or "{news_data}",
        category=cat_label,
        extra_sections=extra,
        format_info=format_info,
    )

# =============================================================================
# 특수 요소 템플릿
# =============================================================================

OFFICIAL_BUTTON_TEMPLATE = '''
<div style="margin: 30px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e8e8e8;">
    <a href="{url}" target="_blank" rel="noopener" style="text-decoration: none; display: block;">
        <div style="background: linear-gradient(135deg, {bg_color_1} 0%, {bg_color_2} 100%); padding: 28px 24px; display: flex; align-items: center; gap: 16px;">
            <div style="width: 56px; height: 56px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <img src="{favicon_url}" alt="{name}" style="width: 32px; height: 32px; border-radius: 4px;" onerror="this.style.display='none';this.parentElement.innerHTML='🏛️';" />
            </div>
            <div>
                <p style="font-size: 18px; font-weight: 700; color: white; margin: 0 0 4px 0; text-shadow: 0 1px 2px rgba(0,0,0,0.1);">{name}</p>
                <p style="font-size: 13px; color: rgba(255,255,255,0.85); margin: 0;">{description}</p>
            </div>
            <div style="margin-left: auto; flex-shrink: 0;">
                <span style="background: rgba(255,255,255,0.25); color: white; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">바로가기 →</span>
            </div>
        </div>
    </a>
</div>
'''

# 카드 색상 세트 (사이트별 브랜딩)
CARD_COLOR_SETS = {
    "default": ("#4A90D9", "#357ABD"),
    "정부": ("#1B5E97", "#0D47A1"),
    "세금": ("#2E7D32", "#1B5E20"),
    "고용": ("#E65100", "#BF360C"),
    "건강": ("#00838F", "#006064"),
    "교육": ("#6A1B9A", "#4A148C"),
    "금융": ("#1565C0", "#0D47A1"),
    "복지": ("#AD1457", "#880E4F"),
}

def get_card_colors(name: str) -> tuple:
    """사이트명에 따른 카드 색상 반환"""
    for key, colors in CARD_COLOR_SETS.items():
        if key in name:
            return colors
    return CARD_COLOR_SETS["default"]

COUPANG_BUTTON_TEMPLATE = '''
<div style="text-align: center; margin: 30px 0;">
    <a href="{url}" target="_blank" rel="noopener noreferrer"
       style="display: inline-block; background-color: #ff6b35; color: white;
              padding: 16px 40px; text-decoration: none; border-radius: 8px;
              font-weight: 600; font-size: 16px;">
        {button_text}
    </a>
</div>
'''

COUPANG_DISCLAIMER = '''
<p style="font-size: 11px; color: #999; margin-top: 30px; text-align: center;">
    이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
</p>
'''

HEALTH_DISCLAIMER = '''
<div style="margin: 30px 0; padding: 15px; background: #fff3cd; border-radius: 8px; font-size: 13px; text-align: left;">
    ⚠️ <strong>안내:</strong> 이 글은 정보 제공 목적이며, 의료적 조언이 아닙니다.
    증상이 심하거나 지속되면 반드시 전문의와 상담하세요.
</div>
'''

AFFILIATE_NOTICE = '''
<p style="font-size: 11px; color: #999; margin-top: 50px; text-align: center;">
    이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
</p>
'''

CATEGORY_BADGE_TEMPLATE = '''
<div style="text-align: center; margin-bottom: 20px;">
  <span style="background: #e8f4f8; color: #1a73e8; padding: 5px 12px;
               border-radius: 15px; font-size: 13px; font-weight: 500;">
    {category}
  </span>
</div>
'''

# =============================================================================
# 레거시 호환용 프롬프트
# =============================================================================

STRUCTURE_PROMPT = """
주제: '{keyword}'

블로그 포스팅의 상세 목차를 구성해주세요.

목차 구조 (총 5,000자 이상 분량):
1. 서론 (400자) - 주제 소개, 중요성 설명
2. 핵심 정보 (600자) - 정의, 개념, 왜 중요한지
3. 상세 가이드 (800자) - 단계별 방법, 구체적 절차
4. 실전 팁 (700자) - 유용한 정보 5가지, 주의사항
5. 비교/분석 (600자) - 관련 옵션 비교, 장단점
6. FAQ (600자) - 자주 묻는 질문 5개 이상
7. 결론 (300자) - 핵심 요약

각 섹션의 소제목과 핵심 포인트를 JSON으로 출력하세요.
"""

WRITING_PROMPT = """
목차: {outline}
참고 데이터: {news_data}
키워드: {keyword}

아래 규칙을 지켜서 블로그 글을 작성해주세요:

📝 분량 규칙:
- 총 5,000자 이상

🎯 SEO 규칙:
- '{keyword}' 키워드를 본문에 7~10회 자연스럽게 포함
- 첫 문단에 키워드 필수 포함
- 소제목에도 키워드 포함

✍️ 문체 규칙:
- 정중한 해요체 사용
- 전문적이면서 이해하기 쉬운 설명
- 이모지는 소제목에만 최대 1개 (전체 2개 이하)
- 짧은 문장 (40자 이내)

📋 HTML 포맷:
- <h1> 사용 금지, <h2>부터 시작
- <p>: 문단 (3~4줄씩)
- <ul><li>: 목록
- <strong>: 강조

🔖 이미지 태그:
- [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 배치

📌 마지막에 메타 설명 추가:
[META]SEO 최적화된 메타 설명 (150자 이내)[/META]

결과는 순수 HTML만 출력하세요.
"""

def get_title_prompt(keyword: str) -> str:
    """제목 생성 프롬프트 (현재 연도 동적 반영)"""
    current_year = datetime.now().year

    return f"""
주제: '{keyword}'

블로그 글 제목을 작성해주세요.

[현재 시점]: {current_year}년

제목 규칙:
1. 클릭을 유도하는 매력적인 제목
2. 키워드 '{keyword}' 자연스럽게 포함
3. 30~50자 이내
4. 숫자 포함 권장 (예: "5가지", "{current_year}년")
5. 연도 포함 시 반드시 {current_year}년 사용

형식 예시:
- "{keyword} 완벽 가이드, 이것만 알면 됩니다"
- "{current_year} {keyword} 총정리 (+ 필수 정보 5가지)"
- "{keyword} 하는 방법, 초보자도 쉽게 따라하기"

제목만 출력하세요 (따옴표 없이)
"""

# 레거시 호환용
TITLE_PROMPT = get_title_prompt("{keyword}")
