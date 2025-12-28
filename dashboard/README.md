# QuickInfo Dashboard

반자동/자동 통합 발행 대시보드

## 구조

```
dashboard/
├── backend/           # FastAPI 백엔드 (포트 8003)
│   ├── main.py
│   ├── requirements.txt
│   └── routers/
│       ├── keywords.py   # 키워드 관리
│       ├── articles.py   # 글 생성/편집
│       ├── images.py     # 이미지 관리
│       ├── publish.py    # 발행 관리
│       └── settings.py   # 설정 관리
│
└── frontend/          # Next.js 프론트엔드 (포트 3003)
    ├── app/
    ├── components/
    └── lib/
```

## 실행 방법

### 백엔드

```bash
cd dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

### 프론트엔드

```bash
cd dashboard/frontend
npm install
npm run dev
```

## 기능

- **반자동 모드**: 키워드 선택 → 글 생성 → 섹션별 편집 → 수동 발행
- **자동 모드**: 스케줄에 따라 자동으로 키워드 선택, 글 생성, 발행

## API 엔드포인트

- `GET /api/keywords/trending` - 트렌드 키워드
- `GET /api/keywords/evergreen` - 에버그린 키워드
- `POST /api/articles/generate` - 글 생성
- `POST /api/articles/{id}/edit-section` - 섹션 편집
- `POST /api/images/search/pexels` - Pexels 이미지 검색
- `POST /api/publish/` - WordPress 발행
- `GET /api/settings/` - 설정 조회
