# AutoQuant - AI 기반 주식 분석 및 종목 선정 시스템

**한국 주식 시장을 위한 AI 기반 종목 선정 및 분석 시스템**

[![Status](https://img.shields.io/badge/status-in--development-yellow)]()
[![Python](https://img.shields.io/badge/python-3.12+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## ⚠️ 시스템 범위

**AutoQuant는 종목 선정 및 분석 도구입니다 (실제 매매는 별도 프로그램)**

✅ AI 기반 종목 스크리닝 (4,359개 → 30~40개)
✅ 기술적 분석 스크리닝 (30~40개 → 3~5개)
✅ AI 가격 예측 (LSTM & XGBoost)
✅ 매수/목표/손절가 계산
✅ 매매 신호 데이터베이스 저장
❌ 실제 매매 실행 (별도 프로그램이 TradingSignal 테이블 읽고 실행)

### 🔄 최신 업데이트: Phase 1-4 완료 (2025-10-26)
- ✅ **Phase 1**: 데이터베이스 스키마 확장 (TradingSignal, MarketSnapshot, AnalysisRun 등)
- ✅ **Phase 2**: 시장 분석 모듈 (5-factor 모멘텀, 4-signal 센티먼트)
- ✅ **Phase 3**: AI 스크리닝 (GPT-4/Claude/Gemini, 배치 쿼리 최적화, 한국명/섹터 정보 추가)
- ✅ **Phase 4**: 기술적 스크리닝 (5-factor 종합 점수, RSI/MACD/BB/Volume/Momentum)
- 🔄 **Phase 5**: 가격 계산 (진행중 - R/R 비율 개선 필요)
- ⏳ **Phase 6**: 일일 실행 스크립트 (대기중)
- [📖 시스템 설계 보기](SYSTEM_DESIGN.md)
- [📖 구현 계획 보기](IMPLEMENTATION_PLAN.md)

---

## 🚀 빠른 시작

```bash
# 1. 가상환경 활성화 (필수!)
source venv/bin/activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. PostgreSQL 연결 테스트 (KIS 데이터)
python tests/test_db_connection.py
# ✅ PostgreSQL 연결, KIS 4,359개 종목 확인

# 4. 일일 분석 실행 (Phase 1-4 실행)
python scripts/daily_analysis.py
# 자동으로 최신 영업일 기준 분석
# 결과: 3~5개 종목 선정 + DB 저장

# 5. 웹 대시보드 실행 (진행중)
cd webapp
python app.py
# 접속: http://localhost:5000
```

### 📝 설정 (PostgreSQL + AI API)
**.env 파일 필수 설정**:
- PostgreSQL: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- AI API: OPENAI_API_KEY, ANTHROPIC_API_KEY, 또는 GOOGLE_API_KEY
- 자세한 설정은 [DATABASE_SETUP.md](DATABASE_SETUP.md), [AI_INTEGRATION.md](AI_INTEGRATION.md) 참고

---

## 📊 시스템 구성 (8-Layer Architecture)

### Phase 1: 데이터베이스 스키마 ✅
- **TradingSignal**: 매매 신호 저장 (매수가, 목표가, 손절가, AI 신뢰도)
- **MarketSnapshot**: 시장 스냅샷 (KOSPI, 투자자별 매매, 섹터 성과, 센티먼트)
- **AnalysisRun**: 분석 실행 이력
- **AIScreeningResult, AICandidate**: AI 스크리닝 결과
- **TechnicalScreeningResult, TechnicalSelection**: 기술적 스크리닝 결과

### Phase 2: 시장 분석 (MarketAnalyzer) ✅
- **5-factor 모멘텀 분석**:
  1. 지수 추세 (KOSPI 5일/20일 SMA)
  2. 투자자별 매매 흐름 (개인/기관/외국인)
  3. 투자자 잔고 균형 (외국인 보유비율)
  4. 섹터 모멘텀 (강세/약세 섹터)
  5. 시장 폭 (상승/하락 종목 비율)
- **4-signal 센티먼트 판단**:
  1. 모멘텀 신호 (5-factor 종합)
  2. 투자자 흐름 신호 (순매수 패턴)
  3. 시장 추세 신호 (KOSPI 기술적 지표)
  4. 종합 센티먼트 (강세/중립/약세)

### Phase 3: AI 스크리닝 (AIScreener) ✅
- **외부 AI API 활용**: GPT-4, Claude, Gemini
- **입력**: 시장 분석 + 4,359개 전체 종목 (한국명, 섹터 포함)
- **출력**: 30~40개 AI 선정 종목 (의미론적/테마적 필터링)
- **최적화**: 배치 쿼리로 3-4분 → 1초 단축

### Phase 4: 기술적 스크리닝 (TechnicalScreener) ✅
- **5-factor 점수 시스템** (각 0~20점, 총 100점):
  1. RSI (과매도/과매수)
  2. MACD (모멘텀)
  3. Bollinger Bands (변동성)
  4. Volume (거래량)
  5. Price Momentum (가격 모멘텀)
- **입력**: AI 선정 30~40개 종목
- **출력**: 상위 3~5개 종목 (기술적 점수순)

### Phase 5: 가격 계산 (PriceCalculator) 🔄
- **AI 예측 가격**: LSTM/XGBoost 7일 예측
- **지지/저항 레벨**: 최근 고가/저가 분석
- **ATR 기반 손절가**: 변동성 고려
- **하이브리드 가격**: AI 예측 + 기술적 레벨 조합
- ⚠️ **현재 이슈**: R/R 비율 0.10 (목표: 2.0+)

### Phase 6: 일일 실행 스크립트 ⏳
- **실행 시간**: 장 마감 후 3:45 PM (KST)
- **실행 흐름**: Phase 1→2→3→4→5→DB 저장
- **결과**: 3~5개 종목의 매매 신호 DB 저장
- **외부 연동**: 별도 프로그램이 TradingSignal 읽고 실제 매매 실행

### 웹 대시보드 (Flask) ⏳
- AI 스크리닝 결과 페이지
- 기술적 분석 점수 표시
- 매매 신호 대시보드
- 섹터별/종목별 분석 결과

---

## 🧪 테스트 결과

### 데이터베이스 연결 테스트
```bash
python tests/test_db_connection.py
```
```
✓ PostgreSQL 연결 성공
✓ KIS daily_ohlcv: 4,359개 종목
✓ KIS stock_info: 2,684개 종목 정보
```

### 오케스트레이터 테스트 (Phase 1-4)
```bash
python tests/test_orchestrator.py
```
```
✓ Phase 1: 데이터베이스 스키마 생성
✓ Phase 2: 시장 분석 (5-factor, 4-signal)
✓ Phase 3: AI 스크리닝 (31개 선정, 1초 내 완료)
✓ Phase 4: 기술적 스크리닝 (3개 최종 선정)
✓ 결과 DB 저장 완료
```

### Phase별 개별 테스트
```bash
# Phase 2: 시장 분석
python tests/test_phase2_market_analyzer.py

# Phase 3: AI 스크리닝
python tests/user_tests/test_04_ai_screening.py

# Phase 4: 기술적 스크리닝
python tests/user_tests/test_04_technical_screening.py
```

---

## 💻 사용 예제

### 일일 분석 실행 (전체 플로우)
```bash
# 최신 영업일 기준 자동 분석
python scripts/daily_analysis.py

# 특정 날짜 분석
python scripts/daily_analysis.py --date 2025-10-24

# 출력 예시:
# Phase 1: 데이터베이스 스키마 확인
# Phase 2: 시장 분석 완료 (센티먼트: 강세)
# Phase 3: AI 스크리닝 완료 (31개 선정)
# Phase 4: 기술적 스크리닝 완료 (3개 최종 선정)
# Phase 5: 가격 계산 완료
# DB 저장 완료: analysis_runs.id=17
```

### AI 스크리닝 (개별 모듈)
```python
from src.analysis.ai_screener import AIScreener

screener = AIScreener()
result = screener.screen_stocks(
    market_data={'sentiment': '강세', 'trend': '상승'},
    stocks_data=[...],  # 4,359개 종목 데이터
    max_stocks=35
)
print(f"AI 선정: {len(result['selected_stocks'])}개")
```

### 기술적 스크리닝 (개별 모듈)
```python
from src.analysis.technical_screener import TechnicalScreener

screener = TechnicalScreener()
result = screener.screen(ai_candidates, analysis_date)
for stock in result['selected_stocks']:
    print(f"{stock['name']}: {stock['total_score']:.1f}점")
```

### 가격 계산 (개별 모듈)
```python
from src.analysis.price_calculator import PriceCalculator

calculator = PriceCalculator()
prices = calculator.calculate_trading_prices(
    stock_code='005930',
    current_price=75000,
    start_date='2025-09-24',
    end_date='2025-10-24'
)
print(f"매수가: {prices['buy_price']:,}원")
print(f"목표가: {prices['target_price']:,}원")
print(f"손절가: {prices['stop_loss_price']:,}원")
```

---

## 🌐 웹 대시보드 (진행중)

### 계획된 기능
1. **AI 스크리닝 결과**: 선정 이유, 섹터 정보, AI 분석 요약
2. **기술적 분석 점수**: 5-factor 상세 점수 및 차트
3. **매매 신호**: 매수가, 목표가, 손절가, 예상 수익률
4. **시장 분석**: 센티먼트, 모멘텀, 투자자 흐름
5. **분석 이력**: 과거 분석 결과 조회 및 비교

---

## 📁 프로젝트 구조

```
AutoQuant/
├── src/
│   ├── database/              # 데이터베이스 (ORM models, Database manager)
│   ├── analysis/              # 분석 모듈
│   │   ├── market_analyzer.py      # Phase 2: 시장 분석
│   │   ├── ai_screener.py          # Phase 3: AI 스크리닝
│   │   ├── technical_screener.py   # Phase 4: 기술적 스크리닝
│   │   └── price_calculator.py     # Phase 5: 가격 계산
│   ├── orchestration/         # 오케스트레이터
│   │   └── analysis_orchestrator.py  # Phase 1-5 통합 실행
│   └── utils/                 # 유틸리티
│       └── sector_mapper.py        # 섹터 코드 매핑
├── scripts/                   # 실행 스크립트
│   └── daily_analysis.py      # 일일 분석 실행
├── webapp/                    # 웹 대시보드 (진행중)
├── tests/                     # 테스트
│   ├── test_db_connection.py       # DB 연결 테스트
│   ├── test_orchestrator.py        # 오케스트레이터 테스트
│   ├── test_phase2_market_analyzer.py
│   └── user_tests/                 # Phase별 테스트
└── sector_codes.csv           # KIS 섹터 코드 (486개)
```

---

## 📚 주요 문서

- **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)**: 8-layer 시스템 아키텍처 상세 설명
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)**: Phase 1-6 구현 계획 및 진행 상황
- **[AI_INTEGRATION.md](AI_INTEGRATION.md)**: AI API 통합 가이드 (GPT-4/Claude/Gemini)
- **[DATABASE_SETUP.md](DATABASE_SETUP.md)**: PostgreSQL 설정 및 KIS 데이터 조회
- **[MOMENTUM_ANALYSIS_IMPROVEMENTS.md](MOMENTUM_ANALYSIS_IMPROVEMENTS.md)**: Phase 2 개선 내역
- **[CLAUDE.md](CLAUDE.md)**: Claude Code를 위한 프로젝트 가이드

---

## ⚠️ 중요 사항

### 시스템 범위
- ✅ **AutoQuant**: 종목 선정 및 분석 (AI 스크리닝 → 기술적 스크리닝 → 가격 계산 → DB 저장)
- ❌ **실제 매매**: 별도 프로그램이 `TradingSignal` 테이블을 읽고 KIS/Kiwoom API로 실행
- **이유**: 분석과 실행을 분리하여 안정성 및 유연성 확보

### 데이터 사용 원칙
- ❌ **절대 모의 데이터 사용 금지**: MockDataGenerator 사용 불가
- ✅ **실제 KIS DB만 사용**: `database.get_available_symbols_from_kis()` 필수
- ✅ **실제 주식 코드**: 005930(삼성전자), 000660(SK하이닉스) 등

### 비용 및 설정
- **AI API 비용**: 월 $0.03-0.90 (하루 1회 실행 기준)
- **필수 설정**: .env 파일에 PostgreSQL + AI API 키 설정
- **실행 주기**: 장 마감 후 3:45 PM (KST) 일 1회

### 책임 및 면책
- 이 시스템은 교육 및 연구 목적입니다
- 실제 투자는 자기 책임하에 진행하세요
- 과거 수익률 ≠ 미래 수익률
- 충분한 테스트 후 소액으로 시작 권장

---

## 🎯 개발 로드맵

- [x] **Phase 1**: 데이터베이스 스키마 확장
- [x] **Phase 2**: 시장 분석 (5-factor 모멘텀, 4-signal 센티먼트)
- [x] **Phase 3**: AI 스크리닝 (GPT-4/Claude/Gemini)
- [x] **Phase 4**: 기술적 스크리닝 (5-factor 점수)
- [ ] **Phase 5**: 가격 계산 완성 (R/R 비율 개선 중)
- [ ] **Phase 6**: 일일 실행 스크립트 자동화
- [ ] **웹 대시보드**: AI/기술적 분석 결과 시각화
- [ ] **백테스팅**: AI 예측 정확도 검증

---

## 📞 문의 및 기여

- **Issues**: GitHub Issues에 버그 리포트 또는 기능 요청
- **Pull Request**: 기여 환영합니다

---

**프로젝트 상태**: 🔄 개발 진행중 (Phase 1-4 완료, Phase 5 진행중)
**마지막 업데이트**: 2025-10-26 (Phase 3-4 최적화 완료)
**테스트 통과율**: Phase 1-4 100%
**데이터베이스**: PostgreSQL (KIS 시스템, 4,359개 종목)
**AI API**: OpenAI GPT-4/Anthropic Claude/Google Gemini
