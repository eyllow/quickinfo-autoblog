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
    │   └── page.tsx         # 메인 대시보드
    └── components/
        ├── ModeToggle.tsx       # 반자동/완전자동 모드 전환
        ├── KeywordSelector.tsx  # 키워드 선택
        ├── ArticleEditor.tsx    # 글 편집기
        ├── SectionEditor.tsx    # 섹션별 편집
        ├── ImageManager.tsx     # 이미지 관리
        └── PublishStats.tsx     # 발행 통계
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

## 서버 배포

### 최초 설치 (서버에서 한 번만)

```bash
cd ~/quickinfo-autoblog/dashboard/deploy
./install_services.sh
```

### 업데이트 배포

```bash
cd ~/quickinfo-autoblog/dashboard/deploy
./deploy_dashboard.sh
```

### 서비스 관리

```bash
# 상태 확인
sudo systemctl status quickinfo-dashboard-api
sudo systemctl status quickinfo-dashboard-web

# 재시작
sudo systemctl restart quickinfo-dashboard-api
sudo systemctl restart quickinfo-dashboard-web

# 로그 확인
sudo journalctl -u quickinfo-dashboard-api -f
sudo journalctl -u quickinfo-dashboard-web -f
```

### 접속 URL

- API: http://43.202.224.41:8003
- Web: http://43.202.224.41:3003

## 확인사항

- [ ] 반자동/완전자동 모드 토글 작동
- [ ] 키워드 추천 목록 표시
- [ ] 글 생성 후 섹션별 미리보기
- [ ] 섹션 수정 요청 -> AI 재작성
- [ ] 이미지 교체 (Pexels/스크린샷/삭제)
- [ ] 글 길이 조절
- [ ] 발행 버튼 -> WordPress 발행
- [ ] 발행 통계 표시
