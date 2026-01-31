"""템플릿 기반 프롬프트 생성기 - 저품질 방지 시스템"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.templates import (
    get_random_template,
    get_intro_pattern,
    get_outro_pattern,
    get_cta_config
)
from generators.prompts import CONTENT_CONSISTENCY_RULES


# =============================================================================
# 분량 가이드 (5000~6000자 목표)
# =============================================================================

# =============================================================================
# 인물 키워드 전용 프롬프트 (뉴스 팩트 중심)
# =============================================================================

PERSON_TITLE_PROMPT = """
아래 뉴스 정보를 바탕으로 블로그 제목을 작성하세요.

## 키워드: {keyword}
## 뉴스 요약: {news_summary}

## 제목 작성 규칙:
1. 형식: "[인물명], [핵심 뉴스 내용]"
2. 뉴스에서 확인된 팩트만 반영
3. 길이: 15~30자
4. 연도 불필요 (2026년 등 제외)

## 금지 표현:
- "꿀팁", "N가지", "완벽 정리", "총정리"
- "대세 트렌드", "핵심 전략", "비법"
- "돈 되는", "놓치면 후회"
- "알아야 할", "몰랐던", "충격"

## 좋은 예시:
- "이학재, 인천공항 AI 혁신 및 안전운영 박차"
- "고승범, 서울FC 떠나 북부리그 이적 예고"
- "손흥민, 토트넘 재계약 협상 본격화"
- "김연아, 빙상연맹 부회장 취임"
- "박보검, 새 드라마 '빛과 그림자' 주연 확정"

## 출력:
제목만 출력 (따옴표, 설명 없이)
"""


PERSON_NEWS_PROMPT = """
당신은 뉴스 팩트 정리 전문가입니다. 인물 키워드에 대해 객관적이고 팩트 기반의 글을 작성합니다.

## 키워드: {keyword}
## 카테고리: {category}

## 최신 정보:
{web_data}

## 작성 규칙:

### 1. 서론 (300~400자)
- 왜 지금 이 인물이 화제인지 1-2문장으로 설명
- 핵심 뉴스 요약
- [IMAGE_1]

### 2. 본문 구성 (2500~3500자)

소제목은 내용 기반으로 구체적으로 작성:
- ❌ 금지: "핵심 뉴스 내용", "인물 배경", "향후 전망", "기본 정보", "관련 배경"
- ✅ 내용 요약형: "인천공항, AI 전환 선언"
- ✅ 질문형: "왜 북부리그로 이적하나?"
- ✅ 인용형: "'안전이 최우선 가치'"
- ✅ 구체적 팩트: "9만 4천 직원에게 감사 인사"

#### 섹션별 가이드:
1. 첫 번째 섹션: 무슨 일이 있었는지 팩트 중심 설명
   - "~라고 알려졌다", "~로 전해졌다" 등 출처 명시 표현 사용

2. 두 번째 섹션: 인물 직책, 소속, 주요 경력 (확인된 사실만)
   - [IMAGE_2]

3. 세 번째 섹션: 뉴스에서 언급된 맥락/배경

### 3. 마무리 (200~300자)
- 뉴스 언급 내용 기반 마무리
- 추측성 전망 금지

## 소제목 예시:
❌ "핵심 뉴스 내용" → ✅ "AI 전환으로 국민 공항 도약 선언"
❌ "인물 배경" → ✅ "인천공항공사 이끄는 이학재 사장은 누구?"
❌ "향후 전망" → ✅ "2026년 공항 운영, 어디로 가나"
❌ "관련 배경" → ✅ "토트넘 재계약, 왜 지금인가"

## 절대 금지 사항:
1. "성공하는 N가지 비법" 류의 제목/소제목 금지
2. 확인되지 않은 정보 작성 금지
3. 과장/미화/비하 표현 금지
4. 개인 의견이나 추측 금지
5. "~일 것으로 예상된다" (근거 없는 추측) 금지
6. 나무위키, 위키피디아 등 검증 안 된 출처 인용 금지
7. 딱딱한 일반명사 소제목 ("핵심 내용", "기본 정보" 등) 금지

## HTML 스타일:
- 전체: <div style="max-width: 700px; margin: 0 auto; font-size: 16px; line-height: 1.9; color: #333;">
- 대제목: <h2 style="font-size: 24px; font-weight: 700; color: #222;">
- 소제목: <h3 style="font-size: 20px; font-weight: 600; color: #333; margin-top: 30px;">
- 본문: <p style="font-size: 16px; line-height: 2.0; color: #444;">

## 이미지 태그:
- [IMAGE_1], [IMAGE_2] 형식으로만 작성 (2개)
- 콜론(:)이나 설명 추가 금지

## 필수 태그:
- [META]SEO 메타 설명 150자 이내[/META]: 글 맨 끝

결과는 순수 HTML만 출력하세요 (```html 코드 블록 없이).
"""


CONTENT_LENGTH_GUIDE = """
[분량 가이드 - 매우 중요!]

목표 분량: {min_words}자 ~ {max_words}자 (공백 포함)
실제 목표: 5000자 ~ 6000자

분량을 채우는 방법:
1. 각 섹션별로 충분한 설명과 구체적인 예시 포함
2. 독자가 궁금해할 추가 정보 제공
3. 실제 사례나 통계 데이터 인용
4. "왜?"와 "어떻게?"에 대한 깊이 있는 답변
5. 관련된 실용적인 정보 추가
6. 각 항목마다 2~3문장 이상 상세 설명

❌ 하지 말 것:
- 같은 내용 반복하여 분량 늘리기
- 의미 없는 문장으로 채우기
- 핵심 없이 장황하게 쓰기

✅ 해야 할 것:
- 모든 섹션에 실질적인 정보 포함
- 독자에게 도움이 되는 구체적인 내용
- 전문가 수준의 깊이 있는 분석
- 실생활에 적용 가능한 방법 제공

[AdSense 승인을 위한 금지 표현]
- 감탄사: ㅋㅋ, ㅎㅎ, ㅠㅠ, 헐, 대박
- 과장 표현: 완전, 진짜진짜, 무조건, 핵심 중의 핵심
- 클릭베이트: 충격, 경악, 미친, 역대급
- 꿀팁, 핵꿀팁, 알짜팁 → "효과적인 방법", "유용한 정보"로 대체
- 이모지: 전체 글에서 최대 2개만 (소제목에만 사용)
"""


def generate_person_prompt(
    keyword: str,
    category: str,
    web_data: str = ""
) -> tuple:
    """
    인물 키워드 전용 프롬프트 생성 (뉴스 팩트 중심)

    Args:
        keyword: 인물 키워드
        category: 카테고리명
        web_data: 웹검색 데이터 (뉴스 정보)

    Returns:
        (프롬프트, 템플릿 키, 템플릿 설정, CTA 설정) 튜플
    """
    prompt = PERSON_NEWS_PROMPT.format(
        keyword=keyword,
        category=category,
        web_data=web_data[:4000] if web_data else "최신 뉴스 정보를 바탕으로 작성해주세요."
    )

    # 인물 전용 템플릿 정보
    template_info = {
        "name": "인물 뉴스 팩트",
        "description": "뉴스 팩트 기반 인물 소개",
        "selected_word_count": 3500,
        "selected_image_count": 2,
        "sections": []
    }

    cta_config = {"position": "bottom"}

    return prompt, "person_news", template_info, cta_config


def generate_template_prompt(
    keyword: str,
    category: str,
    web_data: str = "",
    is_evergreen: bool = False,
    is_person: bool = False
) -> tuple:
    """
    템플릿 기반 프롬프트 생성

    Args:
        keyword: 블로그 키워드
        category: 카테고리명
        web_data: 웹검색 데이터
        is_evergreen: 에버그린 콘텐츠 여부
        is_person: 인물 키워드 여부

    Returns:
        (프롬프트, 템플릿 키, 템플릿 설정, CTA 설정) 튜플
    """
    # 인물 키워드는 전용 프롬프트 사용
    if is_person:
        return generate_person_prompt(keyword, category, web_data)

    # 1. 랜덤 템플릿 선택
    template_key, template = get_random_template()

    # 2. 서론 스타일 결정
    intro_section = next((s for s in template["sections"] if s["type"] == "intro"), None)
    intro_style = intro_section.get("style", "hook") if intro_section else "hook"
    intro_pattern = get_intro_pattern(intro_style, keyword)

    # 3. 마무리 패턴
    outro_pattern = get_outro_pattern(keyword)

    # 4. CTA 설정
    cta_config = get_cta_config()

    # 5. 프롬프트 구성
    prompt = f"""
주제: '{keyword}'
카테고리: {category}
템플릿: {template['name']} ({template['description']})
목표 글자수: 약 {template['selected_word_count']}자 (공백 포함)
이미지 개수: {template['selected_image_count']}개

[HTML 스타일 가이드]
- 전체를 <div style="max-width: 700px; margin: 0 auto; font-size: 16px; line-height: 1.9; color: #333;">로 감싸기
- 대제목: <h2 style="font-size: 26px; font-weight: 700; color: #222; text-align: center;">
- 소제목: <div style="border-left: 3px solid #333; padding-left: 12px;"><h4>│ 제목</h4></div>
- 본문: <p style="font-size: 16px; line-height: 2.0; color: #444; text-align: left;">
- 리스트: <ul style="padding-left: 20px;"><li style="margin: 8px 0;">
- 표: <table style="width: 100%; border-collapse: collapse; margin: 25px 0;">

[서론 시작 문장 - 반드시 이 문장으로 시작하세요]
"{intro_pattern}"

[글 구조 - 반드시 이 순서대로 작성]
"""

    # 섹션별 지시 추가
    img_counter = 1
    section_num = 1

    for section in template["sections"]:
        if section["type"] == "intro":
            prompt += f"""
{section_num}. 서론 ({section['min_words']}~{section['max_words']}자)
   - 위의 시작 문장으로 시작
   - 독자 공감 유도
   <!-- IMG_CONTEXT: {keyword} introduction visual -->
   [IMAGE_1]
"""
            img_counter = 2
            section_num += 1

        elif section["type"] == "heading":
            title = section["title"].format(
                keyword=keyword,
                count=section.get("selected_items", 5)
            )
            prompt += f"""
{section_num}. │ {title}
"""
            section_num += 1

        elif section["type"] == "content":
            prompt += f"""   - 본문 작성 ({section['min_words']}~{section['max_words']}자)
   - 구체적인 정보와 예시 포함
"""
            if img_counter <= template["selected_image_count"]:
                prompt += f"""   <!-- IMG_CONTEXT: {keyword} detailed explanation -->
   [IMAGE_{img_counter}]
"""
                img_counter += 1

        elif section["type"] in ["list_content", "numbered_list"]:
            items = section.get("selected_items", 5)
            prompt += f"""   - {items}개 항목 나열
   - 각 항목당 {section['min_words_per_item']}자 이상 상세 설명
   - 이모지 활용 (각 항목 앞에)
"""

        elif section["type"] == "qa_list":
            items = section.get("selected_items", 5)
            prompt += f"""   - Q&A 형식으로 {items}개 작성
   - 각 Q&A당 {section['min_words_per_item']}자 이상
   - 형식: <p><strong>Q. 질문?</strong></p><p>A. 답변...</p>
"""

        elif section["type"] == "table":
            rows = section.get("selected_rows", 4)
            prompt += f"""   - HTML 테이블로 {rows}행 작성
   - 비교/정리 목적
   - <table> 태그 사용, 헤더 배경색 #f8f9fa
"""

        elif section["type"] == "outro":
            prompt += f"""
{section_num}. 마무리 ({section['min_words']}~{section['max_words']}자)
   - 핵심 요약
   - 마무리 예시: "{outro_pattern[:60]}..."
"""
            if img_counter <= template["selected_image_count"]:
                prompt += f"""   <!-- IMG_CONTEXT: {keyword} conclusion summary -->
   [IMAGE_{img_counter}]
"""
            section_num += 1

    # 웹 데이터 참조
    if web_data:
        prompt += f"""

[참고 자료 - 최신 정보 반영 필수]
{web_data[:3000]}

[중요] 위 참고 자료의 수치, 날짜, 금액을 정확히 반영하세요.
"""

    # 에버그린 콘텐츠 추가 지시
    if is_evergreen:
        from datetime import datetime
        current_year = datetime.now().year
        prompt += f"""

[에버그린 콘텐츠 규칙]
- 반드시 {current_year}년 기준으로 작성
- 2024년이 아닌 {current_year}년 데이터 사용
- "최신", "현재 기준" 표현 권장
"""

    # CTA 및 태그 안내
    prompt += f"""

[필수 태그]
- [OFFICIAL_LINK]: 공식 사이트 버튼 위치 (해당되는 경우)
- [COUPANG]: 쿠팡 상품 위치 (CTA 위치: {cta_config['position']})
- [AFFILIATE_NOTICE]: 파트너스 문구 위치 (태그만 작성, 문구는 시스템이 자동 삽입)
- [META]SEO 메타 설명 150자 이내[/META]: 글 맨 끝

[파트너스 문구 - 매우 중요!]
- [AFFILIATE_NOTICE] 태그만 표시하세요
- 파트너스/제휴/광고 관련 문구를 직접 작성하지 마세요
- "이 포스팅은 파트너십..." 같은 문구를 본문에 직접 쓰지 마세요
- 시스템이 필요할 때만 자동으로 문구를 삽입합니다

[이미지 태그 형식 - 매우 중요!]
- 반드시 [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 형식으로만 작성
- 콜론(:)이나 설명 추가 금지 (예: [IMAGE_1: 설명] ← 이렇게 하지 마세요)
- <!-- IMG_CONTEXT --> 주석은 그대로 유지

[절대 금지 - AdSense 승인 필수]
- 감탄사: ㅋㅋ, ㅎㅎ, ㅠㅠ, 헐, 대박
- 과장 표현: 완전, 진짜진짜, 무조건, 핵심 중의 핵심
- 클릭베이트: 충격, 경악, 미친, 역대급
- 꿀팁, 핵꿀팁, 알짜팁 → "효과적인 방법", "유용한 정보"로 대체
- 이모지: 전체 글에서 최대 2개만 (소제목에만 사용)
- "첫째, 둘째, 셋째" 사용 금지 (→ "먼저", "다음으로", "마지막으로" 사용)
- "~하는 것이 중요합니다" 사용 금지 (→ "~하는 게 중요해요")
- "제공해주신", "작성하겠습니다" 등 메타 표현 금지
- 모든 문장이 비슷한 길이로 정렬됨 (문장 길이 다양하게)
- [IMAGE_1: 설명] 형식 사용 금지 (→ [IMAGE_1] 만 사용)

[문체 규칙]
- 정중한 해요체 사용 ("~해요", "~예요")
- 전문적이면서 친근한 톤
- 짧고 명확한 문장 (40자 이내)
- 객관적 사실 중심 서술

결과는 순수 HTML만 출력하세요 (```html 코드 블록 없이).
"""

    # 제목-본문 일관성 규칙 추가
    prompt += CONTENT_CONSISTENCY_RULES

    # 분량 가이드 추가
    length_guide = CONTENT_LENGTH_GUIDE.format(
        min_words=template['selected_word_count'],
        max_words=template['selected_word_count'] + 1500
    )
    prompt += length_guide

    return prompt, template_key, template, cta_config


def get_template_info_log(template_key: str, template: dict, cta_config: dict) -> str:
    """
    템플릿 정보 로그 문자열 생성

    Args:
        template_key: 템플릿 키
        template: 템플릿 설정
        cta_config: CTA 설정

    Returns:
        로그 문자열
    """
    return f"""
  📝 선택된 템플릿: {template['name']} ({template_key})
  📊 목표 글자수: {template['selected_word_count']}자
  🖼️ 이미지 개수: {template['selected_image_count']}개
  🔘 CTA 위치: {cta_config['position']}
"""


if __name__ == "__main__":
    # 테스트
    print("=== 템플릿 프롬프트 생성 테스트 ===\n")

    for i in range(3):
        prompt, key, template, cta = generate_template_prompt(
            keyword="연말정산",
            category="재테크",
            web_data="2025년 연말정산 관련 최신 정보..."
        )

        print(f"테스트 {i+1}:")
        print(get_template_info_log(key, template, cta))
        print(f"  프롬프트 길이: {len(prompt)}자")
        print("-" * 50)
