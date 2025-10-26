# AutoQuant Web Application

모바일 및 데스크톱 반응형 웹 대시보드 - AI 주식 분석 결과 시각화

## 📱 주요 기능

### 반응형 디자인
- **모바일 최적화**: 터치 친화적 UI, 하단 네비게이션 바
- **데스크톱 지원**: 와이드 스크린 레이아웃, 상단 메뉴 바
- **Tailwind CSS**: 유틸리티 기반 반응형 스타일링
- **Alpine.js**: 경량 반응형 JavaScript 프레임워크

### 페이지 구성

#### 1. 대시보드 (/)
- 최신 분석 실행 요약
- KOSPI 지수 및 시장 센티먼트
- 분석 플로우 시각화 (4,359개 → 35개 → 5개 → 매매신호)
- 빠른 액션 버튼

#### 2. 매매신호 (/signals)
- 최종 매매신호 목록 (R/R 2.0 이상 보장)
- 종목별 카드:
  - 매수가 / 목표가 / 손절가
  - 기대수익 / 최대손실
  - R/R 비율, AI 신뢰도, 기술점수
  - 가격 구간 시각화 바

#### 3. AI 스크리닝 (/ai-screening)
- 35개 AI 선정 후보 목록
- 종목별 정보:
  - AI 점수 (0-100)
  - AI 선정 이유 (GPT-4/Claude/Gemini 분석)
  - 현재가 및 거래량
  - 섹터 분류

#### 4. 기술적 분석 (/technical)
- 5개 기술적 선정 종목
- 5-factor 점수 분해:
  - 이동평균 (SMA)
  - 상대강도 (RSI)
  - MACD
  - 볼린저밴드
  - 거래량
- 종합 기술점수 및 선정 이유

#### 5. 시장 분석 (/market)
- KOSPI 지수 및 변동률
- 시장 센티먼트 (BULLISH/NEUTRAL/BEARISH)
- 5-factor 모멘텀 점수
- 투자자별 순매수 (개인/외국인/기관)
- 시장 폭 (상승/하락/보합 종목 수)
- 섹터 분석 및 요약

#### 6. 분석 이력 (/history)
- 최근 30회 분석 실행 기록
- Run ID, 날짜, 상태, 신호 개수
- 클릭 시 상세 페이지 링크

## 🚀 실행 방법

### 사전 요구사항
```bash
# Flask 설치 (requirements.txt에 포함되어야 함)
pip install flask

# 또는 전체 의존성 설치
pip install -r requirements.txt
```

### 앱 실행
```bash
cd /opt/AutoQuant/webapp
python3 app_new.py
```

### 접속
- **로컬**: http://localhost:5000
- **네트워크**: http://<서버IP>:5000

## 📊 API 엔드포인트

### GET /api/dashboard
최신 분석 실행 요약 정보
```json
{
  "run_id": 1,
  "analysis_date": "2024-10-26",
  "target_date": "2024-10-27",
  "status": "completed",
  "stats": {
    "total_stocks": 4359,
    "ai_candidates": 35,
    "technical_picks": 5,
    "final_signals": 3
  },
  "market": {
    "sentiment": "BULLISH",
    "trend": "UPTREND",
    "kospi": 2550.5,
    "change_pct": 1.23
  }
}
```

### GET /api/signals
최신 매매신호 목록
```json
{
  "signals": [
    {
      "code": "019170",
      "name": "신풍제약",
      "buy": 50000,
      "target": 60000,
      "stop": 45000,
      "profit_amt": 10000,
      "loss_amt": 5000,
      "return_pct": 20.0,
      "rr_ratio": 2.0,
      "ai_conf": 85.5,
      "status": "pending",
      "tech_score": 78.3,
      "sector": "의약품"
    }
  ],
  "run_id": 1
}
```

### GET /api/ai-candidates/<run_id>
AI 스크리닝 후보 목록
```json
{
  "candidates": [
    {
      "code": "019170",
      "name": "신풍제약",
      "ai_score": 85.5,
      "reason": "강력한 매출 성장과 신약 파이프라인 확보",
      "sector": "의약품",
      "price": 50000,
      "volume": 123456,
      "rank": 1
    }
  ]
}
```

### GET /api/technical/<run_id>
기술적 분석 선정 종목
```json
{
  "selections": [
    {
      "code": "019170",
      "name": "신풍제약",
      "price": 50000,
      "scores": {
        "sma": 85.0,
        "rsi": 75.0,
        "macd": 80.0,
        "bb": 70.0,
        "volume": 82.0,
        "total": 78.4
      },
      "reason": "강력한 상승 추세 및 거래량 증가",
      "rank": 1
    }
  ]
}
```

### GET /api/market/<run_id>
시장 분석 데이터
```json
{
  "date": "2024-10-26",
  "kospi": {
    "close": 2550.5,
    "change_pct": 1.23
  },
  "sentiment": "BULLISH",
  "trend": "UPTREND",
  "momentum": 75.5,
  "investors": {
    "individual": -50000000000,
    "foreigner": 30000000000,
    "institution": 20000000000
  },
  "market_breadth": {
    "advancing": 1500,
    "declining": 800,
    "unchanged": 200
  },
  "sector_analysis": "반도체, IT 강세...",
  "summary": "외국인 및 기관 매수세..."
}
```

### GET /api/history
분석 실행 이력
```json
{
  "history": [
    {
      "run_id": 1,
      "date": "2024-10-26",
      "target_date": "2024-10-27",
      "status": "completed",
      "signals": 3,
      "sentiment": "BULLISH",
      "kospi": 2550.5
    }
  ]
}
```

## 🎨 디자인 시스템

### 색상 팔레트
- **Primary**: Blue (#3B82F6) - 신뢰, 안정성
- **Secondary**: Purple (#A855F7) - AI, 혁신
- **Success**: Green (#10B981) - 수익, 긍정
- **Warning**: Yellow (#F59E0B) - 주의
- **Danger**: Red (#EF4444) - 손실, 위험
- **Neutral**: Gray (#6B7280) - 중립, 보합

### 타이포그래피
- **제목**: 2xl-3xl, 굵게
- **본문**: sm-base, 일반
- **레이블**: xs, 회색
- **숫자**: 굵게, 색상 강조

### 컴포넌트
- **Glass Morphism**: 반투명 배경, 블러 효과
- **Card Hover**: 호버 시 그림자 증가, 2px 상승
- **Loading Spinner**: 회전 애니메이션
- **Progress Bar**: 색상별 진행률 표시
- **Badge**: 둥근 태그, 색상별 상태 표시

## 📱 반응형 브레이크포인트

- **Mobile**: < 1024px (lg)
  - 하단 네비게이션 바
  - 1-2 컬럼 그리드
  - 터치 최적화

- **Desktop**: >= 1024px (lg:)
  - 상단 메뉴 바
  - 3-4 컬럼 그리드
  - 마우스 호버 효과

## 🔧 커스터마이징

### 색상 변경
`base.html`의 Tailwind 클래스 수정:
```html
<!-- 예: Primary 색상 변경 -->
<div class="bg-blue-600">  <!-- blue → purple -->
```

### 페이지 추가
1. `app_new.py`에 라우트 추가:
```python
@app.route('/new-page')
def new_page():
    return render_template('new_page.html')
```

2. `templates/new_page.html` 생성:
```html
{% extends "base.html" %}
{% block title %}새 페이지{% endblock %}
{% block content %}
<!-- 내용 -->
{% endblock %}
```

3. `base.html`에 네비게이션 링크 추가

### API 엔드포인트 추가
`app_new.py`에 추가:
```python
@app.route('/api/custom')
def get_custom_data():
    session = db.get_session()
    try:
        # 쿼리 로직
        result = session.execute(text("SELECT ..."))
        return jsonify({'data': result})
    finally:
        session.close()
```

## 🐛 트러블슈팅

### Flask 실행 안됨
```bash
# Flask 설치 확인
pip list | grep -i flask

# 포트 이미 사용중
lsof -i :5000
kill -9 <PID>
```

### 데이터 없음 (404 에러)
- 분석 실행 완료 확인: `analysis_runs` 테이블에 `status='completed'` 레코드 존재 확인
- PostgreSQL 연결 확인: `.env` 파일의 DB 설정 확인

### 한글 깨짐
- `app.config['JSON_AS_ASCII'] = False` 설정 확인
- PostgreSQL 인코딩: UTF-8 확인

### 반응형 안됨
- 브라우저 캐시 클리어
- Tailwind CDN 로드 확인 (네트워크 탭)

## 📄 라이센스
AutoQuant 프로젝트의 일부로 동일한 라이센스 적용
