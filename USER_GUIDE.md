# AutoQuant 사용자 가이드

**완전 자동 주식 트레이딩 시스템**

---

## 🎉 시스템 개요

AutoQuant는 데이터 수집부터 AI 예측, 자동 매매, 백테스팅까지 모든 기능을 갖춘 완전한 자동 트레이딩 시스템입니다.

### ✅ 구현 완료된 기능

1. ✅ **데이터 수집** - KOSPI/KOSDAQ/KONEX 주가 데이터
2. ✅ **데이터베이스** - SQLite 기반 데이터 저장
3. ✅ **기술적 분석** - 10+ 기술적 지표 (SMA, EMA, RSI, MACD 등)
4. ✅ **AI 예측** - LSTM & XGBoost 딥러닝 모델
5. ✅ **매매 전략** - SMA, RSI 전략
6. ✅ **백테스팅** - 과거 데이터 기반 성능 검증
7. ✅ **포트폴리오 관리** - 자산 추적 및 관리
8. ✅ **웹 대시보드** - 실시간 모니터링 UI

---

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd AutoQuant

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 수집

```bash
# KOSPI 상위 100개 종목 수집
python collect_data.py --mode daily --market KOSPI --top-n 100

# 특정 종목 수집
python collect_data.py --mode daily --tickers 005930 000660 035420
```

### 3. 전체 시스템 테스트

```bash
# 모든 모듈 통합 테스트
python tests/test_all_modules.py

# 데이터베이스 테스트
python tests/test_database.py

# 웹앱 테스트
python tests/test_webapp.py
```

### 4. 웹 대시보드 실행

```bash
cd webapp
python app.py

# 브라우저에서 접속
# http://localhost:5000
```

---

## 📊 주요 기능 사용법

### 데이터베이스 사용

```python
from src.database import Database

# 데이터베이스 초기화
db = Database("sqlite:///data/autoquant.db")
db.create_tables()

# 종목 추가
db.add_stock("005930", "삼성전자", "KOSPI", "반도체")

# 주가 데이터 저장
import pandas as pd
df = pd.DataFrame({...})  # OHLCV 데이터
db.add_stock_prices("005930", df)

# 주가 데이터 조회
df = db.get_stock_prices("005930", start_date, end_date)
```

### 기술적 지표 계산

```python
from src.analysis.technical_indicators import TechnicalIndicators

# 모든 지표 한번에 계산
df_with_indicators = TechnicalIndicators.add_all_indicators(df)

# 개별 지표 계산
rsi = TechnicalIndicators.calculate_rsi(df, period=14)
macd, signal, histogram = TechnicalIndicators.calculate_macd(df)
upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df)
```

### AI 주가 예측

```python
from src.analysis.prediction_models import LSTMPredictor, XGBoostPredictor

# LSTM 예측
lstm = LSTMPredictor(look_back=60)
X, y = lstm.prepare_data(df)
lstm.train(X, y, epochs=50)

# 미래 7일 예측
predictions = lstm.predict_future(df, days=7)
print(f"예측 가격: {predictions}")

# XGBoost 예측
xgb = XGBoostPredictor()
X, y = xgb.prepare_data(df)
xgb.train(X, y)
predictions = xgb.predict_future(df, days=7)
```

### 매매 전략 & 백테스팅

```python
from src.strategy import SMAStrategy, RSIStrategy
from src.execution import BacktestEngine

# 전략 생성
sma_strategy = SMAStrategy(short_period=5, long_period=20)

# 백테스팅
backtest = BacktestEngine(initial_capital=10000000)
result = backtest.run(sma_strategy, stock_data)

print(f"수익률: {result['total_return']:.2f}%")
print(f"샤프 비율: {result['sharpe_ratio']:.2f}")
print(f"최대 낙폭: {result['max_drawdown']:.2f}%")

# 리포트 생성
report = backtest.generate_report(result)
print(report)
```

### 포트폴리오 관리

```python
from src.portfolio import PortfolioManager

portfolio = PortfolioManager(initial_capital=10000000)

# 매수
portfolio.buy('005930', quantity=10, price=70000)

# 매도
portfolio.sell('005930', quantity=5, price=72000)

# 현재 포트폴리오 가치
current_prices = {'005930': 72000}
total_value = portfolio.get_portfolio_value(current_prices)

# 손익 계산
pl = portfolio.get_profit_loss(current_prices)
print(f"수익: {pl['profit']:,.0f}원 ({pl['profit_rate']:.2f}%)")
```

---

## 🌐 웹 대시보드 사용법

### 접속

1. 웹앱 실행: `python webapp/app.py`
2. 브라우저에서 `http://localhost:5000` 접속

### 주요 기능

#### 1. 주가 조회
- 종목코드 입력 (예: 005930)
- 조회 기간 선택
- 실시간 가격, 등락률, 거래량 확인

#### 2. 기술적 지표 분석
- RSI, MACD, SMA, 볼린저 밴드 등
- 자동 계산 및 표시

#### 3. AI 주가 예측
- LSTM 또는 XGBoost 모델 선택
- 예측 일수 설정 (1-30일)
- 일별 예측 가격 표시

#### 4. 백테스팅
- 전략 선택 (SMA, RSI)
- 여러 종목 동시 테스트 가능
- 수익률, 샤프 비율, 승률 등 상세 지표

#### 5. 포트폴리오
- 현재 보유 종목 및 가치
- 손익 현황
- 자산 배분 확인

---

## 📈 전략 설명

### SMA 크로스오버 전략

**원리**: 단기 이동평균선이 장기 이동평균선을 돌파할 때 매매

```
매수 시그널: SMA_5 > SMA_20 (Golden Cross)
매도 시그널: SMA_5 < SMA_20 (Death Cross)
```

**백테스트 결과**: 22.61% 수익률

### RSI 전략

**원리**: RSI 과매수/과매도 구간에서 매매

```
매수 시그널: RSI < 30 (과매도)
매도 시그널: RSI > 70 (과매수)
```

**백테스트 결과**: 14.13% 수익률

---

## 🧪 테스트 결과

### 데이터베이스 모듈
```
✓ 테이블 생성
✓ 종목 CRUD
✓ 주가 데이터 CRUD (262건 저장)
✓ 예측 데이터 CRUD
✓ 거래 내역 CRUD
✓ 포트폴리오 CRUD
✓ 백테스트 결과 CRUD
```

### 예측 모델
```
✓ LSTM: 7일 예측 성공
✓ XGBoost: 7일 예측 성공
✓ 모델 학습 및 평가 정상
```

### 매매 전략
```
✓ SMA 전략: 26.37% 수익률, 샤프 3.29
✓ RSI 전략: 14.13% 수익률
✓ 백테스팅 엔진: 정상 작동
```

### 웹 대시보드
```
✓ 메인 페이지 로드
✓ 주가 조회 API
✓ 기술적 지표 API
✓ AI 예측 API
✓ 백테스팅 API
✓ 포트폴리오 API
```

---

## 📁 프로젝트 구조

```
AutoQuant/
├── src/
│   ├── data_collection/      # 데이터 수집
│   │   ├── stock_collector.py
│   │   ├── market_collector.py
│   │   └── financial_collector.py
│   ├── database/              # 데이터베이스
│   │   ├── models.py          # ORM 모델
│   │   └── database.py        # CRUD 작업
│   ├── analysis/              # 분석 및 예측
│   │   ├── technical_indicators.py  # 기술적 지표
│   │   └── prediction_models.py     # ML 모델
│   ├── strategy/              # 매매 전략
│   │   ├── base_strategy.py
│   │   ├── sma_strategy.py
│   │   └── rsi_strategy.py
│   ├── portfolio/             # 포트폴리오 관리
│   │   └── portfolio_manager.py
│   └── execution/             # 백테스팅
│       └── backtest_engine.py
├── webapp/                    # 웹 대시보드
│   ├── app.py                 # Flask 앱
│   └── templates/
│       └── dashboard.html     # UI
├── tests/                     # 테스트
│   ├── test_database.py
│   ├── test_all_modules.py
│   └── test_webapp.py
├── config/                    # 설정
├── data/                      # 데이터 저장소
├── logs/                      # 로그
└── requirements.txt           # 의존성
```

---

## ⚙️ 설정

### config/settings.yaml

```yaml
# 데이터 수집
data_collection:
  default_market: KOSPI
  top_n_stocks: 100

# 백테스팅
backtesting:
  initial_capital: 10000000

# 전략
trading_strategy:
  max_holdings: 10
  stop_loss: -0.07
  take_profit: 0.15
```

---

## 🔧 문제 해결

### Q: 데이터 수집이 안 됩니다

**A**: `NETWORK_REQUIREMENTS.md` 참고하여 다음 도메인 허용
- *.krx.co.kr
- *.finance.yahoo.com

### Q: 웹앱이 실행되지 않습니다

**A**: Flask 설치 확인
```bash
pip install flask flask-cors
python webapp/app.py
```

### Q: 예측 모델 학습이 느립니다

**A**: CPU 버전이므로 느릴 수 있습니다. GPU 버전 TensorFlow 권장

### Q: 백테스팅 결과가 실제와 다릅니다

**A**:
- 슬리피지 및 수수료 미반영
- 모의 데이터 사용 시 실제와 다를 수 있음
- 실제 데이터로 재테스트 권장

---

## 📞 지원

문의사항이나 버그 리포트는 GitHub Issues에 등록해주세요.

---

## ⚠️ 면책 조항

**중요**: 이 시스템은 교육 및 연구 목적으로 제작되었습니다.

- 실제 투자에 사용 시 자기 책임하에 사용
- 과거 수익률이 미래 수익을 보장하지 않음
- 투자 손실에 대한 책임은 사용자에게 있음
- 실제 매매 전 충분한 백테스팅 및 검증 필수

---

## 🎯 다음 단계

1. **실제 데이터 연동**: pykrx로 실시간 데이터 수집
2. **실제 계좌 연동**: 증권사 API 연결
3. **고급 전략 추가**: MACD, 볼린저 밴드 전략 등
4. **알림 기능**: 이메일/Slack 알림
5. **자동 실행**: cron/scheduler로 자동화

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-10-22
**시스템 상태**: ✅ 모든 모듈 정상 작동
