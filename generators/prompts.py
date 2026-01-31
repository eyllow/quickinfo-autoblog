"""카테고리별 프롬프트 템플릿 - 고품질 블로그 글 생성용 (AdSense 최적화)"""
import re
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
# 공통 스타일 규칙 (AdSense 최적화)
# =============================================================================

COMMON_STYLE = """
[메타 언급 절대 금지]
* "제공해주신", "가이드라인", "작성하겠습니다" 등 금지
* AI가 작성했다는 것을 암시하는 문구 금지
* 프롬프트 지시사항에 대한 응답 금지
* 오직 블로그 본문 내용만 출력

[AdSense 승인을 위한 필수 규칙]

1. 콘텐츠 품질
   - 최소 3,000자 이상의 상세한 정보
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

[정렬 규칙]
* 중앙 정렬: 대제목, 카테고리 뱃지, 강조 박스, 이미지 캡션
* 왼쪽 정렬: 소제목, 본문, 리스트, 표, FAQ

[HTML 형식]
- 전체를 <div style="max-width: 700px; margin: 0 auto; font-size: 16px; line-height: 1.9; color: #333;">로 감싸기

- 대제목 (중앙 정렬):
<h2 style="font-size: 26px; font-weight: 700; color: #222; margin: 0 0 25px 0; line-height: 1.4; text-align: center;">
  대제목 내용
</h2>

- 소제목 (세로바 스타일, 왼쪽 정렬):
<div style="border-left: 3px solid #333; padding-left: 12px; margin: 30px 0 15px 0; text-align: left;">
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">
    소제목 내용
  </h4>
</div>

- 본문 텍스트 (왼쪽 정렬):
<p style="font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0; text-align: left;">
  본문 내용
</p>

- 리스트 (왼쪽 정렬):
<ul style="text-align: left; padding-left: 20px; margin: 15px 0;">
  <li style="margin: 8px 0;">항목 1</li>
  <li style="margin: 8px 0;">항목 2</li>
</ul>

- 강조 박스 (중앙 정렬):
<div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; font-size: 18px; font-weight: 500; color: #2e8b57; text-align: center;">
  핵심 내용 강조
</div>

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

- FAQ:
<div style="text-align: left; margin: 20px 0;">
  <p><strong>Q. 질문?</strong></p>
  <p>A. 답변</p>
</div>

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
    """
    AI 생성 콘텐츠에서 금지 표현 제거

    Args:
        content: 원본 콘텐츠

    Returns:
        정제된 콘텐츠
    """
    result = content

    # 금지 표현 제거/대체
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

    # 연속된 느낌표/물음표 정리
    result = re.sub(r'!{2,}', '!', result)
    result = re.sub(r'\?{2,}', '?', result)

    # 연속된 공백 정리
    result = re.sub(r' {2,}', ' ', result)

    return result


def limit_emojis(content: str, max_emojis: int = 2) -> str:
    """
    이모지 개수 제한

    Args:
        content: 원본 콘텐츠
        max_emojis: 최대 이모지 개수 (기본 2개)

    Returns:
        이모지가 제한된 콘텐츠
    """
    # 이모지 패턴 (유니코드 이모지 범위)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 이모티콘
        "\U0001F300-\U0001F5FF"  # 기호 및 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 및 지도 기호
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U00002702-\U000027B0"  # 딩뱃
        "\U0001F900-\U0001F9FF"  # 보충 기호
        "\U0001FA00-\U0001FA6F"  # 체스 기호
        "\U0001FA70-\U0001FAFF"  # 확장 기호
        "\U00002600-\U000026FF"  # 기타 기호
        "\U00002700-\U000027BF"  # 딩뱃 기호
        "]+",
        flags=re.UNICODE
    )

    # 모든 이모지 찾기
    emojis = emoji_pattern.findall(content)

    if len(emojis) <= max_emojis:
        return content

    # max_emojis 이후의 이모지 제거
    result = content
    emoji_count = 0

    for match in emoji_pattern.finditer(content):
        emoji_count += 1
        if emoji_count > max_emojis:
            result = result.replace(match.group(), '', 1)

    return result


def post_process_content(content: str) -> str:
    """
    콘텐츠 후처리 통합 함수

    Args:
        content: 원본 콘텐츠

    Returns:
        AdSense 최적화된 콘텐츠
    """
    result = clean_ai_content(content)
    result = limit_emojis(result, max_emojis=2)
    return result


# =============================================================================
# 카테고리별 프롬프트 템플릿 (AdSense 최적화)
# =============================================================================

FINANCE_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 재테크/정보
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 해당 주제의 중요성 설명
   - 현재 상황이나 관련 통계 제시
   - 이 글에서 다룰 내용 안내

2. [IMAGE_1]

3. <h2>│ {keyword}란? 📋</h2> (400자)
   - 핵심 개념 정의
   - 왜 알아야 하는지 이유 설명
   - 관련 제도나 정책 배경

4. [IMAGE_2]

5. <h2>│ 주요 절차 및 방법</h2>
   - HTML 테이블로 단계별 정리
   - 필요 서류, 조건, 기한 명시
   - 주의사항 포함

6. [IMAGE_3]

7. <h2>│ 알아두면 좋은 정보 💡</h2> (500자)
   - 실제 적용 시 유용한 정보 5가지
   - 번호 목록으로 명확하게 정리

8. <h2>│ 자주 묻는 질문</h2> (400자)
   - Q&A 형식 3-5개
   - 실제 많이 검색되는 질문 중심

9. [IMAGE_4]

10. <h2>│ 마무리</h2> (200자)
    - 핵심 내용 요약
    - 다음 단계 안내

11. [OFFICIAL_LINK]
12. [COUPANG]
13. [AFFILIATE_NOTICE]
14. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 불확실한 수치/날짜 언급 금지
- 과장된 표현 금지
- 감탄사(ㅋㅋ, ㅎㅎ) 사용 금지

결과는 순수 HTML만 출력하세요.
"""

PRODUCT_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: IT/제품
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 제품 출시 배경이나 시장 상황
   - 주요 특징 간략 소개

2. [IMAGE_1]

3. <h2>│ 기본 정보 📱</h2> (300자)
   - 출시일, 가격, 주요 사양
   - 간단한 테이블로 정리

4. <h2>│ 상세 스펙 비교</h2>
   - HTML 테이블로 경쟁 제품과 비교
   - 객관적인 수치 중심

5. [IMAGE_2]

6. <h2>│ 장점</h2> (400자)
   - 구체적인 장점 3-5개
   - 실사용 관점에서 설명

7. <h2>│ 단점 및 아쉬운 점</h2> (300자)
   - 객관적인 단점 2-3개
   - 균형 잡힌 분석

8. [IMAGE_3]

9. <h2>│ 추천 대상</h2> (300자)
   - 타겟 사용자 유형 3가지
   - 어떤 용도에 적합한지

10. <h2>│ 구매 전 확인사항</h2> (300자)
    - 구매 시 고려할 점
    - 구매처 및 가격 정보

11. [IMAGE_4]

12. <h2>│ 마무리</h2> (200자)
    - 종합 평가

13. [COUPANG]
14. [AFFILIATE_NOTICE]
15. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 확인되지 않은 스펙 금지
- 과장된 표현 금지

결과는 순수 HTML만 출력하세요.
"""

CELEBRITY_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 연예/인물
참고 데이터: {news_data}

[중요 안내]
- 인물 사진 사용 불가 (저작권/초상권)
- 무대, 콘서트, 이벤트 분위기 이미지만 사용
- 외모 묘사 최소화

[필수 구성요소]

1. 서론 (300자)
   - 현재 화제가 된 이유
   - 주요 활동 분야 소개

2. [IMAGE_1] (무대/콘서트 분위기)

3. <h2>│ 기본 프로필 📋</h2> (300자)
   - 본명, 생년월일, 소속사, 데뷔
   - 간단한 테이블로 정리

4. <h2>│ 주요 활동</h2> (400자)
   - 대표작/대표곡
   - 수상 이력
   - 주요 활동 연혁

5. [IMAGE_2] (시상식/이벤트 분위기)

6. <h2>│ 최근 소식</h2> (500자)
   - 최근 활동 내용
   - 관련 뉴스 요약

7. <h2>│ 향후 활동 전망</h2> (300자)
   - 예정된 활동
   - 기대되는 점

8. [IMAGE_3] (공연/이벤트 분위기)

9. <h2>│ 마무리</h2> (200자)
    - 요약 정리

10. [IMAGE_4]
11. [AFFILIATE_NOTICE]
12. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 인물 사진 사용 금지
- 루머/확인되지 않은 정보 금지
- 사생활 관련 내용 금지
- 외모 상세 묘사 금지

결과는 순수 HTML만 출력하세요.
"""

HEALTH_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 건강/생활
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 해당 건강 주제의 중요성
   - 많은 분들이 관심 갖는 이유

2. [IMAGE_1]

3. <h2>│ 원인과 배경</h2> (400자)
   - 주요 원인 3-5가지
   - 전문 용어는 쉽게 풀어서 설명

4. <h2>│ 개선 방법 가이드</h2>
   - 테이블 또는 번호 목록으로 정리
   - 단계별 실천 방법

5. [IMAGE_2]

6. <h2>│ 효과적인 방법 💡</h2> (400자)
   - 실제 도움이 되는 방법들
   - 구체적인 실천 팁

7. <h2>│ 주의사항</h2> (300자)
   - 피해야 할 것들
   - 흔한 실수

8. [IMAGE_3]

9. <h2>│ 자주 묻는 질문</h2> (400자)
   - Q&A 형식 3-5개

10. <h2>│ 마무리</h2> (200자)
    - 핵심 요약

11. [IMAGE_4]
12. [DISCLAIMER]
13. [COUPANG]
14. [AFFILIATE_NOTICE]
15. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 의료 진단/처방 금지
- 특정 약품 추천 금지
- 과장된 효과 주장 금지

결과는 순수 HTML만 출력하세요.
"""

LIFESTYLE_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 생활정보
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 해당 주제가 중요한 이유
   - 일상에서의 관련성

2. [IMAGE_1]

3. <h2>│ {keyword}의 중요성</h2> (300자)
   - 왜 알아야 하는지
   - 모르면 생기는 불편함

4. <h2>│ 실천 방법</h2> (500자)
   - 바로 따라할 수 있는 방법
   - 단계별 설명

5. [IMAGE_2]

6. <h2>│ 유용한 정보 💡</h2> (400자)
   - 알아두면 좋은 팁 5가지
   - 번호 목록으로 정리

7. [IMAGE_3]

8. <h2>│ 주의사항</h2> (300자)
   - 피해야 할 실수들

9. <h2>│ 자주 묻는 질문</h2> (300자)
   - Q&A 3-5개

10. <h2>│ 마무리</h2> (200자)
    - 요약 정리

11. [IMAGE_4]
12. [COUPANG]
13. [AFFILIATE_NOTICE]
14. [META]SEO 메타 설명 150자 이내[/META]

결과는 순수 HTML만 출력하세요.
"""

EDUCATION_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 취업/교육
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 해당 주제의 중요성
   - 현재 취업/교육 시장 상황

2. [IMAGE_1]

3. <h2>│ 기본 정보 📋</h2> (400자)
   - 핵심 개념 설명
   - 관련 제도나 자격 안내

4. <h2>│ 준비 방법 체크리스트</h2>
   - 테이블로 단계별 정리
   - 필요한 준비물, 기한 명시

5. [IMAGE_2]

6. <h2>│ 합격/성공을 위한 조언 💡</h2> (500자)
   - 효과적인 준비 방법
   - 경험자들의 조언

7. <h2>│ 흔한 실수와 주의사항</h2> (300자)
   - 피해야 할 것들

8. [IMAGE_3]

9. <h2>│ 자주 묻는 질문</h2> (400자)
   - Q&A 3-5개

10. <h2>│ 마무리</h2> (200자)
    - 핵심 요약

11. [IMAGE_4]
12. [OFFICIAL_LINK]
13. [AFFILIATE_NOTICE]
14. [META]SEO 메타 설명 150자 이내[/META]

결과는 순수 HTML만 출력하세요.
"""

TREND_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 트렌드/일반
참고 데이터: {news_data}

[필수 구성요소]

1. 서론 (300자)
   - 현재 화제가 된 배경
   - 왜 주목받고 있는지

2. [IMAGE_1]

3. <h2>│ {keyword}란?</h2> (400자)
   - 핵심 내용 설명
   - 배경 정보

4. <h2>│ 주목받는 이유</h2> (400자)
   - 화제가 된 이유 분석
   - 관련 이슈들

5. [IMAGE_2]

6. <h2>│ 핵심 포인트 정리 📌</h2> (400자)
   - 알아야 할 것들
   - 번호 목록으로 정리

7. [IMAGE_3]

8. <h2>│ 다양한 반응</h2> (300자)
   - 여론/반응 정리
   - 다양한 관점

9. <h2>│ 향후 전망</h2> (300자)
   - 예측과 분석
   - 기대되는 점

10. <h2>│ 마무리</h2> (200자)
    - 요약 정리

11. [IMAGE_4]
12. [COUPANG]
13. [AFFILIATE_NOTICE]
14. [META]SEO 메타 설명 150자 이내[/META]

결과는 순수 HTML만 출력하세요.
"""

# =============================================================================
# 에버그린 콘텐츠 전용 템플릿 (AdSense 최적화)
# =============================================================================

def get_evergreen_template():
    """현재 날짜를 포함한 에버그린 템플릿 반환"""
    current_year = datetime.now().year
    current_month = datetime.now().month

    return f"""
{{common_style}}

당신은 7년 경력의 전문 에디터입니다.
독자가 실제로 도움받을 수 있는 상세하고 정확한 정보를 제공하세요.

[현재 시점]: {current_year}년 {current_month}월 기준

[핵심 원칙]
1. 정확한 정보: 공식 출처와 통계 데이터 기반
2. 실용적 가치: 독자가 바로 적용할 수 있는 구체적 방법
3. 명확한 구조: 논리적 흐름과 단계별 안내
4. 객관적 서술: 과장 없이 사실 중심으로 작성

[품질 기준]

1. 도입부
   - 해당 주제의 중요성과 현황
   - 최신 통계/수치 포함 (예: "{current_year}년 기준 약 OO만 명...")
   - 이 글에서 다룰 내용 안내

2. 본문 구조 (주제에 맞게 구성)
   - "방법" 주제 → 단계별 가이드
   - "비교" 주제 → 장단점 분석 표
   - "신청/절차" 주제 → 순서도 + 필요 서류
   - 각 섹션은 소제목(세로바 │) + 상세 설명

3. 실용적 정보
   - 표(테이블)로 정리할 수 있는 정보는 반드시 표로
   - 구체적인 금액, 기한, 조건 명시
   - 공식 사이트/기관 안내

4. FAQ (3~5개)
   - 실제로 많이 검색하는 질문
   - 상세한 답변

5. 마무리
   - 핵심 요약 2~3줄
   - 다음 단계 안내

주제: '{{keyword}}'
카테고리: 에버그린 정보성 콘텐츠
참고 데이터: {{news_data}}

[작성 규칙]
- 최소 4,000자 이상
- {current_year}년 기준으로 작성
- 소제목은 세로바(│) 스타일
- 이모지는 소제목에 최대 1개씩만 (전체 2개 이하)
- 본문에 이모지 사용 금지
- 구체적인 수치/비율/예시 필수

[연도 표기 규칙]
- 현재 연도: {current_year}년
- 과거 연도 언급 금지 (2024년, 2023년 등)
- "현재 기준", "최신 기준" 등 상대적 표현 권장

[이미지 태그 배치]
- [IMAGE_1]: 도입부 다음
- [IMAGE_2]: 핵심 정보 섹션 중간
- [IMAGE_3]: 실전 팁/주의사항 다음
- [IMAGE_4]: 마무리 전

[필수 태그]
- [OFFICIAL_LINK]: 공식 사이트 버튼 위치
- [COUPANG]: 쿠팡 상품 위치 (필요시)
- [AFFILIATE_NOTICE]: 제휴 안내 (필요시)
- [META]SEO 메타 설명 150자[/META]: 글 맨 끝

[금지 표현]
- 감탄사: ㅋㅋ, ㅎㅎ, 헐, 대박
- 과장: 완전, 진짜진짜, 무조건, 핵심 중의 핵심
- 클릭베이트: 충격, 경악, 미친
- 꿀팁, 핵꿀팁 → "효과적인 방법", "유용한 정보"로 대체
- 메타 표현: "제공해주신", "작성하겠습니다"

결과는 순수 HTML만 출력하세요.
"""

# 레거시 호환용 변수
EVERGREEN_STYLE = ""
EVERGREEN_TEMPLATE = None
HUMAN_PERSONA_PROMPT = ""  # 더 이상 사용하지 않음 (레거시 호환)

# =============================================================================
# 템플릿 매핑
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

def get_template(template_name: str, is_evergreen: bool = False) -> str:
    """
    템플릿 이름으로 프롬프트 반환

    Args:
        template_name: 템플릿 이름
        is_evergreen: 에버그린 콘텐츠 여부

    Returns:
        완성된 프롬프트 템플릿
    """
    if is_evergreen:
        template = get_evergreen_template()
        template = template.replace("{common_style}", COMMON_STYLE)
        return template

    template = CATEGORY_TEMPLATES.get(template_name, TREND_TEMPLATE)
    return template.replace("{common_style}", COMMON_STYLE)

# =============================================================================
# 특수 요소 템플릿
# =============================================================================

OFFICIAL_BUTTON_TEMPLATE = '''
<div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: left;">
    <p style="font-size: 15px; font-weight: 600; color: #333; margin: 0 0 10px 0;">📌 공식 사이트 안내</p>
    <p style="font-size: 14px; color: #555; margin: 0;">
        👉 <a href="{url}" target="_blank" rel="noopener" style="color: #1a73e8; text-decoration: none; font-weight: 500;">{name} 공식 홈페이지</a>
    </p>
</div>
'''

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

목차 구조 (총 2,500자 이상 분량):
1. 서론 (300자) - 주제 소개, 중요성 설명
2. 핵심 정보 (500자) - 정의, 개념, 왜 중요한지
3. 상세 가이드 (600자) - 단계별 방법, 구체적 절차
4. 실전 팁 (500자) - 유용한 정보 5가지, 주의사항
5. FAQ (400자) - 자주 묻는 질문 3개
6. 결론 (200자) - 핵심 요약

각 섹션의 소제목과 핵심 포인트를 JSON으로 출력하세요.
"""

WRITING_PROMPT = """
목차: {outline}
참고 데이터: {news_data}
키워드: {keyword}

아래 규칙을 지켜서 블로그 글을 작성해주세요:

📝 분량 규칙:
- 총 2,500자 이상

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
