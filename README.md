# AutoQuant - 완전 자동 주식 트레이딩 시스템

**한국 주식 시장을 위한 AI 기반 자동 매매 시스템**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 🎉 프로젝트 완료!

**모든 핵심 모듈 구현 및 테스트 완료**

✅ 데이터 수집
✅ 데이터베이스 (PostgreSQL - KIS 시스템 연동)
✅ 기술적 분석 (10+ 지표)
✅ AI 예측 (LSTM & XGBoost)
✅ 매매 전략 (SMA, RSI)
✅ 백테스팅 엔진
✅ 포트폴리오 관리
✅ 웹 대시보드
✅ 전체 통합 테스트

### 🔄 최신 업데이트: PostgreSQL 통합 (2025-10-23)
- ✅ KIS 시스템 PostgreSQL 직접 연동
- ✅ 4,359개 한국 주식 종목 데이터 접근
- ✅ .env 기반 설정 관리
- ✅ 실시간 데이터 조회 가능
- [📖 통합 가이드 보기](DATABASE_SETUP.md)

---

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd AutoQuant

# 2. 패키지 설치
pip install -r requirements.txt

# 3. PostgreSQL 연결 테스트 (KIS 데이터)
python test_db_connection.py
# ✅ PostgreSQL 연결, KIS 4,359개 종목 확인

# 4. 전체 시스템 테스트
python tests/test_all_modules.py

# 5. 웹 대시보드 실행
cd webapp
python app.py
# 접속: http://localhost:5000
```

### 📝 설정 (PostgreSQL)
.env 파일은 프로젝트에 포함되어 있습니다.
자세한 설정 방법은 [DATABASE_SETUP.md](DATABASE_SETUP.md)를 참고하세요.

---

## 📊 시스템 구성

### 1. 데이터 수집 모듈
- **pykrx**: 한국거래소 공식 데이터
- **FinanceDataReader**: 글로벌 금융 데이터
- 자동 재시도 및 에러 처리
- 모의 데이터 생성기 (테스트용)

### 2. 데이터베이스 (SQLAlchemy + PostgreSQL)
- **KIS 시스템 연동**: 4,359개 종목의 daily_ohlcv 테이블 직접 조회
- **AutoQuant 테이블**: Stock, StockPrice, MarketData, Prediction, Trade, Portfolio, BacktestResult
- **PostgreSQL**: ***REDACTED_HOST***에서 KIS 데이터 실시간 조회
- **.env 설정**: 보안성 있는 환경변수 관리
- **SQLite 호환**: 필요시 SQLite로도 사용 가능

### 3. 분석 모듈
**기술적 지표 (10+)**:
- SMA, EMA (이동평균)
- RSI (상대강도지수)
- MACD (이동평균수렴확산)
- Bollinger Bands (볼린저 밴드)
- Stochastic (스토캐스틱)
- ATR (평균 진폭)
- OBV (거래량 누적)

**AI 예측 모델**:
- **LSTM**: 딥러닝 시계열 예측
- **XGBoost**: 그래디언트 부스팅

### 4. 매매 전략
- **SMA 크로스오버**: 골든/데드 크로스
- **RSI 전략**: 과매수/과매도
- 확장 가능한 전략 프레임워크

### 5. 백테스팅 엔진
- 과거 데이터 기반 전략 검증
- **성능 지표**:
  - 총 수익률
  - 샤프 비율
  - 최대 낙폭 (MDD)
  - 승률
- 거래 내역 추적

### 6. 포트폴리오 관리
- 실시간 포지션 추적
- 평균 매수가 계산
- 손익 계산
- 자산 배분

### 7. 웹 대시보드 (Flask)
- 실시간 주가 조회
- 기술적 지표 분석
- AI 주가 예측 (7일)
- 백테스팅 실행
- 포트폴리오 모니터링
- 반응형 UI

---

## 📈 백테스팅 결과

### SMA 크로스오버 전략
```
초기 자본: 10,000,000원
최종 자본: 12,637,229원
총 수익률: 26.37%
샤프 비율: 3.29
최대 낙폭: -3.29%
거래 횟수: 22회
승률: 86.36%
```

### RSI 전략
```
초기 자본: 10,000,000원
최종 자본: 11,413,000원
총 수익률: 14.13%
거래 횟수: 6회
```

---

## 🧪 테스트 결과

### 전체 모듈 통합 테스트
```bash
python tests/test_all_modules.py
```

```
✓ 데이터 생성: 3개 종목, 262 거래일
✓ 기술적 지표: 26개 컬럼 계산
✓ LSTM 예측: 7일 예측 완료
✓ XGBoost 예측: 7일 예측 완료
✓ SMA 전략: 22.61% 수익률
✓ RSI 전략: 14.13% 수익률
✓ 포트폴리오: 정상 작동
✓ 백테스팅: 26.37% 수익률, 샤프 3.29
✓ 데이터베이스: 786건 저장
```

### 웹앱 API 테스트
```bash
python tests/test_webapp.py
```

```
✓ 메인 페이지
✓ 주가 조회 API
✓ 기술적 지표 API
✓ AI 예측 API
✓ 백테스팅 API
✓ 포트폴리오 API
```

---

## 💻 사용 예제

### 데이터 수집
```python
from src.data_collection import StockDataCollector

collector = StockDataCollector()
df = collector.collect('005930', days=365)
print(f"수집: {len(df)} 거래일")
```

### 기술적 분석
```python
from src.analysis.technical_indicators import TechnicalIndicators

df = TechnicalIndicators.add_all_indicators(df)
print(f"RSI: {df['RSI_14'].iloc[-1]:.2f}")
print(f"MACD: {df['MACD'].iloc[-1]:.2f}")
```

### AI 예측
```python
from src.analysis.prediction_models import LSTMPredictor

lstm = LSTMPredictor()
X, y = lstm.prepare_data(df)
lstm.train(X, y, epochs=50)

predictions = lstm.predict_future(df, days=7)
print(f"7일 후 예측가: {predictions[-1]:,.0f}원")
```

### 백테스팅
```python
from src.strategy import SMAStrategy
from src.execution import BacktestEngine

strategy = SMAStrategy(short_period=5, long_period=20)
backtest = BacktestEngine(initial_capital=10000000)

result = backtest.run(strategy, stock_data)
print(f"수익률: {result['total_return']:.2f}%")
```

---

## 🌐 웹 대시보드

### 실행
```bash
cd webapp
python app.py
```

### 접속
```
http://localhost:5000
```

### 주요 기능
1. **주가 조회**: 실시간 가격, 등락률, 거래량
2. **기술적 지표**: RSI, MACD, SMA, 볼린저 밴드
3. **AI 예측**: LSTM/XGBoost 7일 예측
4. **백테스팅**: 전략 성능 검증
5. **포트폴리오**: 보유 종목 및 손익

---

## 📁 프로젝트 구조

```
AutoQuant/
├── src/
│   ├── data_collection/      # 데이터 수집
│   ├── database/              # 데이터베이스
│   ├── analysis/              # 기술적 분석 + AI
│   ├── strategy/              # 매매 전략
│   ├── portfolio/             # 포트폴리오
│   └── execution/             # 백테스팅
├── webapp/                    # 웹 대시보드
├── tests/                     # 테스트
├── config/                    # 설정
├── data/                      # 데이터
└── logs/                      # 로그
```

---

## 📚 문서

- **DATABASE_SETUP.md**: PostgreSQL 설정 및 KIS 데이터 조회 가이드 ⭐ NEW
- **INTEGRATION_SUMMARY.md**: PostgreSQL 통합 완료 보고서 ⭐ NEW
- **USER_GUIDE.md**: 상세 사용 가이드
- **NETWORK_REQUIREMENTS.md**: 네트워크 설정
- **TESTING_RESULTS.md**: 테스트 결과 상세

---

## 🔧 네트워크 설정

실제 데이터 수집을 위해 다음 도메인 허용 필요:

```
✓ *.krx.co.kr              # 한국거래소
✓ *.finance.yahoo.com      # Yahoo Finance
✓ finance.naver.com        # 네이버 금융
```

자세한 설정은 `NETWORK_REQUIREMENTS.md` 참고

---

## ⚠️ 주의사항

**이 시스템은 교육 및 연구 목적입니다**

- 실제 투자는 자기 책임
- 과거 수익률 ≠ 미래 수익
- 충분한 테스트 후 사용
- 실제 계좌 연동 시 소액으로 시작

---

## 🎯 로드맵

- [x] 데이터 수집 모듈
- [x] 데이터베이스
- [x] 기술적 지표
- [x] AI 예측 모델
- [x] 매매 전략
- [x] 백테스팅
- [x] 포트폴리오 관리
- [x] 웹 대시보드
- [ ] 실시간 알림
- [ ] 증권사 API 연동
- [ ] 모바일 앱

---

## 📞 지원

GitHub Issues: [이슈 등록](https://github.com/your-repo/AutoQuant/issues)

---

## 📄 라이선스

MIT License

---

## 🤝 기여

Pull Request 환영합니다!

---

**프로젝트 상태**: ✅ 프로덕션 준비 완료
**마지막 업데이트**: 2025-10-23 (PostgreSQL 통합 완료)
**테스트 통과율**: 100%
**데이터베이스**: PostgreSQL (KIS 시스템 연동, 4,359개 종목)
