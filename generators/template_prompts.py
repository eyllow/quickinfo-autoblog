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

CONTENT_LENGTH_GUIDE = """
[분량 가이드 - 매우 중요!]

목표 분량: {min_words}자 ~ {max_words}자 (공백 포함)
실제 목표: 5000자 ~ 6000자

분량을 채우는 방법:
1. 각 섹션별로 충분한 설명과 구체적인 예시 포함
2. 독자가 궁금해할 추가 정보 제공
3. 실제 사례나 통계 데이터 인용
4. "왜?"와 "어떻게?"에 대한 깊이 있는 답변
5. 관련된 부가 정보나 꿀팁 추가
6. 각 항목마다 2~3문장 이상 상세 설명

❌ 하지 말 것:
- 같은 내용 반복하여 분량 늘리기
- 의미 없는 문장으로 채우기
- 핵심 없이 장황하게 쓰기

✅ 해야 할 것:
- 모든 섹션에 실질적인 정보 포함
- 독자에게 도움이 되는 구체적인 내용
- 전문가 수준의 깊이 있는 분석
- 실생활에 적용 가능한 팁 제공
"""


def generate_template_prompt(
    keyword: str,
    category: str,
    web_data: str = "",
    is_evergreen: bool = False
) -> tuple:
    """
    템플릿 기반 프롬프트 생성

    Args:
        keyword: 블로그 키워드
        category: 카테고리명
        web_data: 웹검색 데이터
        is_evergreen: 에버그린 콘텐츠 여부

    Returns:
        (프롬프트, 템플릿 키, 템플릿 설정, CTA 설정) 튜플
    """
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

[절대 금지]
- "첫째, 둘째, 셋째" 사용 금지 (→ "일단", "그리고", "또" 사용)
- "~하는 것이 중요합니다" 사용 금지 (→ "~하는 게 진짜 중요해요")
- "제공해주신", "작성하겠습니다" 등 메타 표현 금지
- 모든 문장이 비슷한 길이로 정렬됨 (문장 길이 다양하게)
- [IMAGE_1: 설명] 형식 사용 금지 (→ [IMAGE_1] 만 사용)

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
