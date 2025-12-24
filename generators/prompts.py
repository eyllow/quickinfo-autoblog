"""카테고리별 프롬프트 템플릿 - 고품질 블로그 글 생성용"""

# =============================================================================
# 공통 스타일 규칙
# =============================================================================

COMMON_STYLE = """
[글 길이 규칙 - 매우 중요!]
* 최소 3,000자 이상 작성 (필수)
* 각 소제목 섹션마다 최소 3~4개 문단 작성
* 각 장점/단점 항목에 구체적인 설명 2~3줄 추가
* "왜 이게 장점인지", "어떤 상황에서 단점인지" 상세히 설명
* FAQ 섹션 반드시 3개 이상 포함
* 마무리 섹션에 "마지막으로 한 가지 더 말씀드릴게요" 추가 단락 필수

[공통 작성 규칙]
1. 문장은 1~2줄로 짧게 끊어서 작성
2. 개인 경험담처럼 친근하게 ("저도 예전에 그랬거든요", "솔직히 말하면...")
3. 핵심 메시지는 따옴표로 강조
4. 줄 간격 넓게 (문단 사이 빈 줄 사용)
5. 이모지 적절히 사용 (섹션당 1~2개)
6. "~입니다/~합니다" 대신 "~예요/~해요" 사용 (친근한 해요체)

[폰트 스타일 규칙 - 반드시 준수]
| 요소 | 크기 | 두께 | 색상 | 특징 |
|------|------|------|------|------|
| 대제목 | 26px | Bold (700) | #222 | 중앙정렬 |
| 중간제목 | 22px | SemiBold (600) | #333 | 중앙정렬 |
| 소제목 | 20px | SemiBold (600) | #333 | 세로바 3px |
| 본문 | 16px | Regular (400) | #444 | line-height 2.0 |
| 표 헤더 | 15px | SemiBold (600) | #333 | 배경 #f8f9fa |
| 표 내용 | 15px | Regular (400) | #555 | - |
| 사진캡션 | 13px | Regular (400) | #888 | 중앙정렬 |
| 강조 | 16px | SemiBold (600) | #2e8b57 | 초록색 |
| 따옴표 | 18px | Medium (500) | #2e8b57 | 배경박스 |

[HTML 형식 - 통일된 스타일]
- 전체를 <div style="text-align: center; line-height: 2.0;">로 감싸기

- 대제목 (글 시작):
<h2 style="font-size: 26px; font-weight: 700; color: #222; margin: 0 0 25px 0; line-height: 1.4; text-align: center;">
  대제목 내용
</h2>

- 중간제목:
<h3 style="font-size: 22px; font-weight: 600; color: #333; margin: 35px 0 20px 0; line-height: 1.4; text-align: center;">
  중간제목 내용
</h3>

- 소제목 (세로바 스타일):
<div style="border-left: 3px solid #333; padding-left: 12px; margin: 30px 0 15px 0; text-align: left;">
  <h4 style="font-size: 20px; font-weight: 600; color: #333; margin: 0;">
    소제목 내용
  </h4>
</div>

- 본문 텍스트:
<p style="font-size: 16px; line-height: 2.0; color: #444; margin: 12px 0;">
  본문 내용
</p>

- 강조 따옴표:
<div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; font-size: 18px; font-weight: 500; color: #2e8b57; text-align: center;">
  ❝ 강조하고 싶은 내용 ❞
</div>

- 테이블 스타일:
<table style="width: 100%; max-width: 600px; margin: 25px auto; border-collapse: collapse; font-size: 15px;">
  <thead>
    <tr style="background: #f8f9fa;">
      <th style="padding: 14px; border-bottom: 2px solid #ddd; font-weight: 600; color: #333;">구분</th>
      <th style="padding: 14px; border-bottom: 2px solid #ddd; font-weight: 600; color: #333;">세부 정보</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 14px; border-bottom: 1px solid #eee; color: #555;">항목</td>
      <td style="padding: 14px; border-bottom: 1px solid #eee; color: #333;">내용</td>
    </tr>
  </tbody>
</table>

- 사진 캡션:
<p style="font-size: 13px; color: #888; margin: 8px 0 25px 0; text-align: center;">
  캡션 내용
</p>

[이미지 태그 - 반드시 포함]
- [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 태그를 본문에 배치
- 각 태그는 나중에 실제 이미지로 교체됨
- 서론 다음, 핵심정보 다음, 가이드 다음, 마무리 전에 배치

[메타 설명]
- 글 맨 끝에 [META]150자 이내 SEO 메타 설명[/META] 형식으로 추가
"""

SYSTEM_PROMPT = """
당신은 10년 경력의 인기 블로거이자 IT/재테크 전문 에디터예요.

당신의 특징:
- 어려운 정보도 친구에게 설명하듯 쉽게 전달해요
- 독자가 "오, 이거 진짜 유용하다!" 느끼게 해요
- 실제 경험담처럼 생생하게 써요
- 독자가 바로 행동하고 싶게 만들어요

문체 규칙:
- "~입니다/~합니다" 대신 "~예요/~해요" 사용 (친근한 해요체)
- 독자에게 말 걸듯이 작성 ("혹시 이런 경험 있으세요?", "사실 저도 처음엔...")
- 적절한 이모지 사용 (섹션당 1~2개)
- 질문형 문장으로 흥미 유발
- 한 문장 50자 이내로 짧게
- 전문 용어는 쉬운 말로 풀어서 설명
"""

# =============================================================================
# 카테고리별 프롬프트 템플릿
# =============================================================================

FINANCE_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 재테크/정보
참고 데이터: {news_data}

[필수 구성요소 - 순서대로 작성]

1. 공감 서론 (300자)
   - 개인 경험담 형식으로 시작
   - "이거 저도 몰랐다가 손해 본 적 있어요"
   - "혹시 {keyword} 때문에 고민이신가요?"

2. [IMAGE_1]

3. <h2>│ {keyword}, 이게 뭔가요? 🤔</h2> (400자)
   - 핵심 개념을 쉽게 설명
   - 왜 중요한지, 왜 알아야 하는지
   - 모르면 어떤 손해가 있는지

4. [IMAGE_2]

5. <h2>❝ {keyword} 절차/방법 한눈표 ❞</h2>
   - 반드시 HTML 테이블로 작성
   - 예시:
   <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
     <tr style="background: #f8f9fa;">
       <th style="border: 1px solid #ddd; padding: 12px;">단계</th>
       <th style="border: 1px solid #ddd; padding: 12px;">해야 할 일</th>
       <th style="border: 1px solid #ddd; padding: 12px;">방법</th>
     </tr>
     <tr>
       <td style="border: 1px solid #ddd; padding: 12px; text-align: center;">1</td>
       <td style="border: 1px solid #ddd; padding: 12px;">...</td>
       <td style="border: 1px solid #ddd; padding: 12px;">...</td>
     </tr>
   </table>

6. [IMAGE_3]

7. <h2>│ 꼭 알아야 할 실전 팁 5가지 💡</h2> (500자)
   - 실제로 도움되는 구체적인 팁
   - 번호 목록으로 정리

8. <h2>│ 자주 묻는 질문 (FAQ) ❓</h2> (400자)
   - Q&A 형식 3개
   - <strong>Q. 질문?</strong><br>A. 답변

9. [IMAGE_4]

10. <h2>│ 마무리</h2> (200자)
    - 감성적인 마무리 멘트
    - 행동 유도 ("지금 바로 확인해보세요!")

11. [OFFICIAL_LINK]

12. [COUPANG]

13. [AFFILIATE_NOTICE]

14. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 불확실한 수치/날짜 언급 금지
- "~할 수 있습니다" 딱딱한 문체 금지
- 테이블 없이 글만 나열 금지

결과는 순수 HTML만 출력하세요.
"""

PRODUCT_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: IT/제품
참고 데이터: {news_data}

[필수 구성요소 - 순서대로 작성]

1. 관심 유발 서론 (300자)
   - "드디어 {keyword} 나왔는데, 살까 말까 고민되시죠?"
   - "저도 이거 살지 말지 엄청 고민했거든요"

2. [IMAGE_1]

3. <h2>│ {keyword} 기본 정보 📱</h2> (300자)
   - 출시일, 가격, 주요 특징
   - 간단한 테이블로 정리

4. <h2>│ 상세 스펙 비교표 📊</h2>
   - 반드시 HTML 테이블로 작성
   - 전작 또는 경쟁 제품과 비교
   <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
     <tr style="background: #f8f9fa;">
       <th style="border: 1px solid #ddd; padding: 12px;">항목</th>
       <th style="border: 1px solid #ddd; padding: 12px;">{keyword}</th>
       <th style="border: 1px solid #ddd; padding: 12px;">비교 제품</th>
     </tr>
   </table>

5. [IMAGE_2]

6. <h2>│ 장점 👍</h2> (400자)
   - 구체적인 장점 3~5개
   - 실사용 관점에서 설명

7. <h2>│ 단점 👎</h2> (300자)
   - 솔직한 단점 2~3개
   - "아쉬운 점이 있다면..."

8. [IMAGE_3]

9. <h2>│ 이런 분께 추천해요! 🎯</h2> (300자)
   - 타겟 사용자 3가지 유형
   - "이런 분이라면 강추!"

10. <h2>│ 구매 전 체크리스트 ✅</h2> (300자)
    - 구매 전 확인할 사항
    - 어디서 사면 좋은지

11. [IMAGE_4]

12. <h2>│ 마무리</h2> (200자)
    - 최종 추천 의견
    - "여러분의 선택에 도움이 됐으면 좋겠어요"

13. [COUPANG]

14. [AFFILIATE_NOTICE]

15. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 확인되지 않은 스펙 금지
- 과장된 표현 금지
- 스펙 비교표 없이 글만 나열 금지

결과는 순수 HTML만 출력하세요.
"""

CELEBRITY_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 연예/인물
참고 데이터: {news_data}

⚠️ 중요 경고:
- 실제 인물 사진은 저작권 문제로 절대 사용하지 않습니다
- 이미지 태그 위치에는 무대/콘서트/카메라 등 분위기 이미지만 사용됩니다
- 인물 외모 묘사는 최소화하세요

[필수 구성요소 - 순서대로 작성]

1. 화제성 서론 (300자)
   - "요즘 {keyword} 때문에 완전 난리죠?"
   - "검색어 1위 찍은 이유가 뭘까요?"
   - 왜 지금 화제인지 설명

2. [IMAGE_1] (무대/콘서트/카메라 분위기 - 인물 사진 X)

3. <h2>│ 기본 프로필 📋</h2> (300자)
   - 본명, 생년월일, 소속사, 데뷔
   - 간단한 테이블로 정리 가능
   - 외모 묘사 최소화

4. <h2>│ 대표 활동/작품 🎬</h2> (400자)
   - 음반, 드라마, 영화 등 목록
   - 수상 이력
   - 대표곡/대표작

5. [IMAGE_2] (시상식/무대 분위기 - 인물 사진 X)

6. <h2>│ 최근 이슈/근황 🔥</h2> (500자)
   - 화제가 된 이유
   - 최근 활동 내용
   - 팬들 사이에서 회자되는 이야기

7. <h2>│ 팬들/대중 반응 💬</h2> (300자)
   - SNS 반응 요약 (직접 인용 X)
   - "팬들 사이에서는..." 형식
   - 긍정적인 반응 위주

8. [IMAGE_3] (공연/이벤트 분위기 - 인물 사진 X)

9. <h2>│ 앞으로의 활동/전망 🚀</h2> (300자)
   - 예정된 활동
   - 기대되는 점

10. <h2>│ 마무리</h2> (200자)
    - "앞으로의 활약이 기대됩니다"
    - 응원 메시지

11. [IMAGE_4]

12. [AFFILIATE_NOTICE]

13. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 실제 인물 사진 사용 절대 금지
- 루머/확인되지 않은 정보 금지
- 사생활 관련 내용 금지
- 악성 댓글/논란 조장 금지
- 외모에 대한 상세 묘사 금지

결과는 순수 HTML만 출력하세요.
"""

HEALTH_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 건강/생활
참고 데이터: {news_data}

[필수 구성요소 - 순서대로 작성]

1. 공감 서론 (300자)
   - "혹시 이런 고민 있으세요?"
   - "저도 예전에 {keyword} 때문에 고생했어요"
   - 독자의 고민에 공감

2. [IMAGE_1]

3. <h2>│ 왜 이런 문제가 생길까요? 🤔</h2> (400자)
   - 원인 설명 (3~5가지)
   - 쉬운 용어로 풀어서
   - "의외로 이런 이유도 있어요"

4. <h2>│ 해결 방법 단계별 가이드 📋</h2>
   - 테이블 또는 번호 목록으로 정리
   <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
     <tr style="background: #f8f9fa;">
       <th style="border: 1px solid #ddd; padding: 12px;">단계</th>
       <th style="border: 1px solid #ddd; padding: 12px;">방법</th>
       <th style="border: 1px solid #ddd; padding: 12px;">포인트</th>
     </tr>
   </table>

5. [IMAGE_2]

6. <h2>│ 실전 꿀팁 💡</h2> (400자)
   - 실제로 효과 본 방법들
   - "이건 진짜 효과 있었어요"

7. <h2>│ 주의사항 ⚠️</h2> (300자)
   - 하면 안 되는 것들
   - 흔한 실수들
   - "이건 절대 하지 마세요"

8. [IMAGE_3]

9. <h2>│ 자주 묻는 질문 (FAQ) ❓</h2> (400자)
   - Q&A 형식 3개

10. <h2>│ 마무리</h2> (200자)
    - 응원 메시지
    - "조금씩 나아질 거예요"

11. [IMAGE_4]

12. [DISCLAIMER]

13. [COUPANG]

14. [AFFILIATE_NOTICE]

15. [META]SEO 메타 설명 150자 이내[/META]

[금지사항]
- 의료 진단/처방 금지
- 특정 약품 추천 금지
- 과장된 효과 주장 금지
- "~하면 무조건 낫는다" 같은 표현 금지

결과는 순수 HTML만 출력하세요.
"""

LIFESTYLE_TEMPLATE = """
{common_style}

주제: '{keyword}'
카테고리: 생활정보
참고 데이터: {news_data}

[필수 구성요소 - 순서대로 작성]

1. 공감 서론 (300자)
   - 일상에서 겪는 불편함 공감
   - "이거 은근 귀찮죠?"
   - "저도 매번 고민했어요"

2. [IMAGE_1]

3. <h2>│ {keyword}, 왜 중요할까요? 🤔</h2> (300자)
   - 왜 알아야 하는지
   - 모르면 어떤 불편이 있는지

4. <h2>│ 초간단 실천 방법 ✨</h2> (500자)
   - 바로 따라할 수 있는 방법
   - 단계별로 쉽게 설명
   - 번호 목록 활용

5. [IMAGE_2]

6. <h2>│ 꿀팁 모음 💡</h2> (400자)
   - 알아두면 좋은 팁 5가지
   - "이건 진짜 꿀팁이에요"

7. [IMAGE_3]

8. <h2>│ 이것만은 피하세요! ⚠️</h2> (300자)
   - 흔한 실수들
   - 하면 안 되는 것

9. <h2>│ 자주 묻는 질문 ❓</h2> (300자)
   - Q&A 3개

10. <h2>│ 마무리</h2> (200자)
    - 요약 정리
    - 응원 메시지

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

[필수 구성요소 - 순서대로 작성]

1. 공감 서론 (300자)
   - "취업 준비, 정말 막막하시죠?"
   - "저도 그때 진짜 힘들었어요"
   - 독자의 고민에 공감

2. [IMAGE_1]

3. <h2>│ {keyword} 기본 정보 📋</h2> (400자)
   - 핵심 개념 설명
   - 왜 중요한지

4. <h2>│ 준비 방법 체크리스트 ✅</h2>
   - 테이블로 정리
   <table style="width:100%; border-collapse: collapse; margin: 20px 0;">
     <tr style="background: #f8f9fa;">
       <th style="border: 1px solid #ddd; padding: 12px;">순서</th>
       <th style="border: 1px solid #ddd; padding: 12px;">할 일</th>
       <th style="border: 1px solid #ddd; padding: 12px;">팁</th>
     </tr>
   </table>

5. [IMAGE_2]

6. <h2>│ 합격자들의 꿀팁 💡</h2> (500자)
   - 실제 도움되는 조언
   - "합격한 선배들이 말하길..."

7. <h2>│ 흔한 실수 & 주의사항 ⚠️</h2> (300자)
   - 피해야 할 것들
   - "이건 절대 하지 마세요"

8. [IMAGE_3]

9. <h2>│ 자주 묻는 질문 ❓</h2> (400자)
   - Q&A 3개

10. <h2>│ 마무리</h2> (200자)
    - 응원 메시지
    - "충분히 해낼 수 있어요!"

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

[필수 구성요소 - 순서대로 작성]

1. 화제성 서론 (300자)
   - "요즘 {keyword} 때문에 난리죠?"
   - 왜 지금 화제인지

2. [IMAGE_1]

3. <h2>│ {keyword}, 이게 뭔가요? 🤔</h2> (400자)
   - 핵심 내용 설명
   - 배경 정보

4. <h2>│ 왜 이렇게 화제일까요? 🔥</h2> (400자)
   - 화제가 된 이유
   - 관련 이슈들

5. [IMAGE_2]

6. <h2>│ 핵심 포인트 정리 📌</h2> (400자)
   - 알아야 할 것들
   - 번호 목록으로 정리

7. [IMAGE_3]

8. <h2>│ 사람들 반응은? 💬</h2> (300자)
   - 여론/반응 정리
   - 다양한 의견들

9. <h2>│ 앞으로 어떻게 될까요? 🚀</h2> (300자)
   - 전망/예측
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
# 템플릿 매핑
# =============================================================================

CATEGORY_TEMPLATES = {
    "finance": FINANCE_TEMPLATE,
    "product": PRODUCT_TEMPLATE,
    "celebrity": CELEBRITY_TEMPLATE,
    "health": HEALTH_TEMPLATE,
    "lifestyle": LIFESTYLE_TEMPLATE,
    "education": EDUCATION_TEMPLATE,
    "trend": TREND_TEMPLATE
}

def get_template(template_name: str) -> str:
    """템플릿 이름으로 프롬프트 반환"""
    template = CATEGORY_TEMPLATES.get(template_name, TREND_TEMPLATE)
    return template.replace("{common_style}", COMMON_STYLE)

# =============================================================================
# 특수 요소 템플릿
# =============================================================================

OFFICIAL_BUTTON_TEMPLATE = '''
<div style="text-align: center; margin: 30px 0;">
    <a href="{url}" target="_blank" rel="noopener"
       style="display: inline-block; background-color: #3182f6; color: white;
              padding: 16px 40px; text-decoration: none; border-radius: 8px;
              font-weight: 600; font-size: 16px;">
        {name} 바로가기
    </a>
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

# AFFILIATE_NOTICE는 COUPANG_DISCLAIMER와 통합 (중복 방지)
AFFILIATE_NOTICE = '''
<p style="font-size: 11px; color: #999; margin-top: 50px; text-align: center;">
    이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
</p>
'''

# 카테고리 뱃지 템플릿
CATEGORY_BADGE_TEMPLATE = '''
<div style="text-align: center; margin-bottom: 20px;">
  <span style="background: #e8f4f8; color: #1a73e8; padding: 5px 12px;
               border-radius: 15px; font-size: 13px; font-weight: 500;">
    {category}
  </span>
</div>
'''

# =============================================================================
# 기존 호환성을 위한 프롬프트 (레거시)
# =============================================================================

STRUCTURE_PROMPT = """
주제: '{keyword}'

블로그 포스팅의 상세 목차를 구성해주세요.

목차 구조 (총 2,500자 이상 분량):
1. 서론 (300자) - 흥미 유발, 공감 포인트
2. 핵심 정보 (500자) - 정의, 개념, 왜 중요한지
3. 상세 가이드 (600자) - 단계별 방법, 구체적 절차
4. 실전 팁 (500자) - 꿀팁 5가지, 주의사항
5. FAQ (400자) - 자주 묻는 질문 3개
6. 결론 (200자) - 핵심 요약, 행동 유도

각 섹션의 소제목과 핵심 포인트를 JSON으로 출력하세요:

{{
    "title": "클릭하고 싶은 매력적인 제목 (숫자 포함 권장)",
    "sections": [
        {{
            "type": "intro",
            "heading": "서론 제목",
            "points": ["공감 포인트", "문제 제기", "해결책 암시"]
        }},
        {{
            "type": "core_info",
            "heading": "핵심 정보 제목",
            "points": ["정의", "중요성", "현재 트렌드"]
        }},
        {{
            "type": "guide",
            "heading": "상세 가이드 제목",
            "points": ["단계1", "단계2", "단계3"]
        }},
        {{
            "type": "tips",
            "heading": "실전 팁 제목",
            "points": ["팁1", "팁2", "팁3", "주의사항"]
        }},
        {{
            "type": "faq",
            "heading": "자주 묻는 질문",
            "points": ["질문1", "질문2", "질문3"]
        }},
        {{
            "type": "conclusion",
            "heading": "마무리 제목",
            "points": ["핵심 요약", "행동 유도"]
        }}
    ]
}}
"""

WRITING_PROMPT = """
목차: {outline}
참고 데이터: {news_data}
키워드: {keyword}

아래 규칙을 반드시 지켜서 블로그 글을 작성해주세요:

📝 분량 규칙:
- 총 2,500자 이상 (공백 포함)

🎯 SEO 규칙:
- '{keyword}' 키워드를 본문에 7~10회 자연스럽게 포함
- 첫 문단에 키워드 반드시 포함
- 소제목(<h2>, <h3>)에도 키워드 포함

✍️ 문체 규칙:
- 친근한 해요체 사용 ("~예요", "~해요", "~거든요")
- 독자에게 말 걸기 ("혹시 ~해보신 적 있으세요?")
- 경험담 형식 ("사실 저도 처음엔 몰랐는데...")
- 이모지 적절히 사용 (섹션당 1~2개)
- 짧은 문장 (50자 이내)

📋 HTML 포맷:
- <h1> 사용 금지, <h2>부터 시작
- <h2>: 대제목, <h3>: 소제목
- <p>: 문단 (3~4줄씩)
- <ul><li>: 목록
- <strong>: 강조
- <blockquote>: 인용/팁 박스

🔖 이미지 태그:
- [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] 태그를 적절한 위치에 배치

📌 마지막에 메타 설명 추가:
글 끝에 아래 형식으로 150자 이내 메타 설명을 작성하세요:
[META]SEO 최적화된 메타 설명 (키워드 포함, 클릭 유도)[/META]

결과는 순수 HTML만 출력하세요 (```html 코드 블록 없이)
"""

TITLE_PROMPT = """
주제: '{keyword}'

블로그 글 제목을 작성해주세요.

제목 규칙:
1. 클릭하고 싶게 만드는 매력적인 제목
2. 키워드 '{keyword}' 자연스럽게 포함
3. 30~50자
4. 숫자 포함 권장 (예: "5가지", "3분만에", "2024년")
5. 형식 예시:
   - "{keyword}, 이것만 알면 끝! 완벽 가이드"
   - "2024 {keyword} 총정리 (+ 꿀팁 5가지)"
   - "{keyword} 하는 법, 초보도 10분이면 OK"
   - "나만 몰랐던 {keyword}의 비밀 3가지"

제목만 출력하세요 (따옴표 없이)
"""
