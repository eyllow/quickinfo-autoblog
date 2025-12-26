# QuickInfo AutoBlog

워드프레스 자동 블로그 발행 시스템

## 주요 기능

- Google Trends 기반 트렌드 키워드 자동 수집
- Claude AI를 활용한 고품질 블로그 글 생성
- 5가지 템플릿 (문제해결형, 스토리텔링, 리스트형, 비교분석형, Q&A형)
- AI 탐지 우회를 위한 휴머나이징 처리
- Pexels API 이미지 자동 삽입
- 워드프레스 REST API 자동 발행
- 쿠팡 파트너스 배너 조건부 삽입
- SQLite 기반 발행 이력 관리
- APScheduler 기반 자동 스케줄링

## 설치

```bash
# 저장소 클론
git clone https://github.com/asouthpawdev/quickinfo-autoblog.git
cd quickinfo-autoblog

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

## 환경 변수 설정

`.env` 파일에 다음 정보를 입력하세요:

```env
# WordPress
WP_URL=https://your-site.com
WP_USER=your_username
WP_APP_PASSWORD=your_app_password

# Claude API
ANTHROPIC_API_KEY=your_anthropic_key

# Pexels (이미지)
PEXELS_API_KEY=your_pexels_key

# Google Custom Search (선택)
GOOGLE_API_KEY=your_google_key
GOOGLE_CSE_ID=your_cse_id

# Coupang Partners (선택)
COUPANG_PARTNER_ID=your_partner_id
```

## 사용법

### CLI 명령어

```bash
# 트렌드 키워드로 자동 발행
python main.py

# 특정 키워드로 발행
python main.py --keyword "아이폰16"

# 임시 저장으로 발행
python main.py --draft

# 에버그린 키워드로 발행
python main.py --evergreen

# 3개 글 연속 발행
python main.py --batch 3

# 발행 통계 보기
python main.py --stats

# 최근 발행 글 보기
python main.py --recent

# 연결 테스트
python main.py --test
```

### 스케줄러 실행

```bash
# 스케줄러 시작 (백그라운드 권장)
python scheduler.py

# 즉시 발행 테스트
python scheduler.py --now

# 에버그린으로 즉시 발행
python scheduler.py --now --evergreen
```

### 발행 스케줄

- 07:00 - 트렌드 키워드
- 15:00 - 트렌드 키워드
- 18:00 - 에버그린 키워드

각 발행은 0~30분 랜덤 딜레이가 적용됩니다.

## 프로젝트 구조

```
quickinfo-autoblog/
├── config/
│   ├── settings.py          # 환경 설정
│   ├── categories.py         # 카테고리 매핑
│   └── evergreen_keywords.json
├── crawlers/
│   ├── google_trends.py      # 트렌드 키워드 수집
│   └── web_search.py         # 웹 검색 컨텍스트
├── generators/
│   ├── prompts.py            # 프롬프트 템플릿
│   ├── humanizer.py          # AI 탐지 우회
│   └── content_generator.py  # 콘텐츠 생성
├── media/
│   ├── image_fetcher.py      # Pexels 이미지
│   └── screenshot.py         # 스크린샷 (선택)
├── publishers/
│   ├── wordpress.py          # 워드프레스 발행
│   └── coupang.py            # 쿠팡 배너
├── database/
│   └── db_manager.py         # SQLite 관리
├── main.py                   # 메인 실행
├── scheduler.py              # 자동 스케줄러
├── requirements.txt
└── .env.example
```

## 템플릿 종류

1. **문제해결형** - 독자의 문제를 정의하고 해결책 제시
2. **스토리텔링** - 사례와 경험 중심의 서술
3. **리스트형** - 핵심 포인트를 목록으로 정리
4. **비교분석형** - 장단점 비교 분석
5. **Q&A형** - 질문과 답변 형식

## 카테고리

| 카테고리 | 쿠팡 배너 |
|----------|-----------|
| 트렌드 | ❌ |
| 재테크 | ✅ |
| IT/가전 | ✅ |
| 생활정보 | ✅ |
| 건강 | ✅ |
| 자동차 | ✅ |
| 정치 | ❌ |
| 사회 | ❌ |
| 연예 | ❌ |
| 사건사고 | ❌ |

## 서버 배포 (systemd)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/autoblog.service
```

```ini
[Unit]
Description=QuickInfo AutoBlog Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/quickinfo-autoblog
ExecStart=/home/ubuntu/quickinfo-autoblog/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable autoblog
sudo systemctl start autoblog

# 상태 확인
sudo systemctl status autoblog
```

## 라이선스

MIT License
