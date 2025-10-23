# 👥 AutoQuant 사용자 테스트 체크리스트

## 📋 개요

이 문서는 AutoQuant의 모든 기능을 체계적으로 테스트하기 위한 사용자 테스트 가이드입니다.
각 섹션별로 순서대로 진행하면서 기능이 정상 작동하는지 확인하세요.

**테스트 예상 시간**: 약 2-3시간
**필요한 환경**: Python 3.8+, PostgreSQL 연결, 가상환경

---

## ⚠️ 중요: 테스트 진행 규칙

**각 테스트 완료 후 반드시 이 문서를 업데이트하세요!**

1. **테스트 시작 전**: 해당 섹션의 체크박스를 확인
2. **테스트 완료 후**:
   - 체크박스를 `[x]`로 업데이트
   - 하단 "📝 테스트 결과 기록" 섹션에 결과 기록
   - 발견된 이슈가 있으면 "발견된 이슈" 섹션에 추가
3. **다음 테스트로 진행**: 순서대로 다음 섹션 테스트

**예시**:
```
### 1.1 PostgreSQL 데이터 조회 (KIS 시스템)
**테스트 항목**:
- [x] PostgreSQL 연결 성공          ← 완료된 항목
- [x] 4,359개 종목 조회 성공
- [ ] 각 종목의 최신 업데이트 날짜 확인  ← 미완료 항목
```

---

## 🔧 사전 준비

### 1. 환경 설정 확인
- [ ] 가상환경 활성화
  ```bash
  source venv/bin/activate
  ```
- [ ] 모든 패키지 설치 확인
  ```bash
  pip list | grep -E "sqlalchemy|pandas|scikit-learn|xgboost|tensorflow"
  ```
- [ ] PostgreSQL 연결 확인
  ```bash
  python test_db_connection.py
  ```

### 2. 디렉토리 구조 확인
- [ ] 프로젝트 루트에 `.env` 파일 있음
- [ ] `src/` 디렉토리 구조 정상
- [ ] `data/` 디렉토리 생성 가능
- [ ] `logs/` 디렉토리 생성 가능

---

## 1️⃣ 데이터 수집 모듈 테스트

### 1.1 PostgreSQL 데이터 조회 (KIS 시스템)

**테스트 파일**: `tests/user_tests/test_01_kis_data_collection.py` ✅ 작성 완료

```python
# tests/user_tests/test_01_kis_data_collection.py
from src.database.database import Database
from datetime import datetime, timedelta

db = Database()

# 1. 사용 가능한 종목 조회
symbols_df = db.get_available_symbols_from_kis()
print(f"총 종목 수: {len(symbols_df)}")
print(symbols_df.head(10))
```

**테스트 항목**:
- [x] PostgreSQL 연결 성공
- [x] 4,359개 종목 조회 성공
- [x] 각 종목의 최신 업데이트 날짜 확인
- [x] 데이터 카운트 확인

**예상 결과**:
```
총 종목 수: 4359
symbol_code  last_trade_date  data_count
000020       2025-10-22       66
000040       2025-10-22       117
...
```

### 1.2 특정 종목 일봉 데이터 조회

**테스트 파일**: `tests/user_tests/test_02_daily_ohlcv.py` ✅ 작성 완료

```python
# tests/user_tests/test_02_daily_ohlcv.py
from src.database.database import Database
from datetime import datetime, timedelta

db = Database()

# 삼성전자(005930) 최근 100일 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=100)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

print(f"종목: {symbol}")
print(f"데이터 건수: {len(ohlcv_df)}")
print(f"기간: {ohlcv_df.index.min()} ~ {ohlcv_df.index.max()}")
print(ohlcv_df.tail(5))
```

**테스트 항목**:
- [x] 종목코드로 데이터 조회 성공
- [x] 지정된 기간의 데이터 조회 성공
- [x] OHLCV 컬럼 모두 존재
- [x] 거래량, 거래대금 데이터 확인
- [x] 데이터 정렬 순서 확인 (오래된 → 최신)

**예상 결과**:
```
종목: 005930
데이터 건수: 73
기간: 2025-07-15 ~ 2025-10-22
            open     high      low    close    volume        amount
2025-10-22  ...      ...      ...    ...    ...            ...
```

### 1.3 pykrx 데이터 수집

**테스트 파일**: `collect_data.py` 실행

```bash
python collect_data.py
```

**테스트 항목**:
- [ ] pykrx에서 데이터 조회 성공
- [ ] 한국거래소 종목 데이터 수집 성공
- [ ] 오류 처리 및 재시도 정상 작동
- [ ] 수집 완료 후 파일 저장 확인

---

## 2️⃣ 기술적 지표 계산 테스트

### 2.1 모든 지표 계산

**테스트 파일**: `tests/user_tests/test_03_technical_indicators.py` ✅ 작성 완료

```python
# tests/user_tests/test_03_technical_indicators.py
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# 모든 기술적 지표 계산
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

print(f"추가된 컬럼: {len(df_with_indicators.columns) - len(ohlcv_df.columns)}")
print(f"총 컬럼: {len(df_with_indicators.columns)}")
print(df_with_indicators.columns.tolist())
print(df_with_indicators.tail())
```

**테스트 항목**:
- [x] SMA 계산 (단기, 중기, 장기)
- [x] EMA 계산
- [x] RSI 계산
- [x] MACD 계산
- [x] Bollinger Bands 계산
- [x] Stochastic 계산 ✅ **수정 완료** (Decimal → Float 변환 추가)
- [x] ATR 계산 ✅ **수정 완료** (Decimal → Float 변환 추가)
- [x] OBV 계산 ✅ **수정 완료** (Decimal → Float 변환 추가)
- [x] 계산 오류 없음 (모든 지표)
- [x] NaN 값 처리 적절

**예상 결과**:
```
추가된 컬럼: 16
총 컬럼: 22
['SMA_5', 'SMA_20', 'SMA_60', 'EMA_12', 'EMA_26', 'RSI_14',
 'MACD', 'MACD_Signal', 'MACD_Histogram', 'BB_Upper', 'BB_Middle', 'BB_Lower',
 'Stoch_K', 'Stoch_D', 'ATR', 'OBV']
```

**실제 결과** (2025-10-23 테스트):
```
✅ 추가된 컬럼: 16개
✅ 총 컬럼: 22개
✅ 모든 지표 정상 작동 (11개 지표, 100% 성공)
```

### 2.2 개별 지표 검증

**테스트 파일**: `tests/user_tests/test_04_single_indicators.py` ✅ 작성 완료

```python
# tests/user_tests/test_04_single_indicators.py

# RSI 검증 (14일 기준)
rsi = df_with_indicators['RSI_14'].tail(1).values[0]
print(f"현재 RSI: {rsi:.2f}")
assert 0 <= rsi <= 100, "RSI는 0-100 범위여야 합니다"
print("✓ RSI 유효성 확인")

# MACD 검증
macd = df_with_indicators['MACD'].tail(1).values[0]
signal = df_with_indicators['MACD_Signal'].tail(1).values[0]
print(f"현재 MACD: {macd:.4f}, Signal: {signal:.4f}")
print("✓ MACD 계산 확인")

# Bollinger Bands 검증
upper = df_with_indicators['BB_Upper'].tail(1).values[0]
lower = df_with_indicators['BB_Lower'].tail(1).values[0]
close = df_with_indicators['close'].tail(1).values[0]
assert lower < close < upper, "가격이 밴드 범위 내에 있어야 합니다"
print(f"✓ Bollinger Bands 유효성 확인 (Lower: {lower:.0f}, Close: {close:.0f}, Upper: {upper:.0f})")
```

**테스트 항목**:
- [x] RSI: 0-100 범위 확인 ✅
- [x] MACD: 신호선과의 관계 확인 ✅
- [x] Bollinger Bands: 상단 > 중단 > 하단 확인 ✅
- [x] Stochastic: 0-100 범위 확인 ✅
- [x] ATR: 양수 확인 ✅
- [x] OBV: 추세 계산 확인 ✅
- [x] 이동평균선: 정렬 순서 확인 ✅
- [x] 각 지표의 계산 정확도 (7/7 통과, 100%)

**실제 결과** (2025-10-23 테스트):
```
✅ 검증 결과: 성공 7개, 실패 0개
✅ 모든 지표 검증 통과 (100%)
```

### 2.3 매매 신호 생성

**테스트 파일**: `tests/user_tests/test_05_trading_signals.py` ✅ 작성 완료

```python
# tests/user_tests/test_05_trading_signals.py
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회 및 지표 계산
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

# 매매 신호 생성
df_with_signals = TechnicalIndicators.get_trading_signals(df_with_indicators)

print(f"추가된 신호 컬럼: {len(df_with_signals.columns) - len(df_with_indicators.columns)}")
```

**테스트 항목**:
- [x] Golden Cross 신호 생성 ✅
- [x] Death Cross 신호 생성 ✅
- [x] RSI 과매수/과매도 신호 ✅
- [x] MACD 크로스 신호 ✅
- [x] Bollinger Bands 돌파 신호 ✅
- [x] 신호 조합 분석 가능 ✅

**예상 결과**:
```
추가된 신호 컬럼: 8
신호 목록: Golden_Cross, Death_Cross, RSI_Oversold, RSI_Overbought,
          MACD_Cross_Up, MACD_Cross_Down, BB_Break_Upper, BB_Break_Lower
```

**실제 결과** (2025-10-23 테스트):
```
✅ 추가된 신호 컬럼: 8개
✅ 검증 결과: 5/5 (100% 통과)
✅ Golden Cross: 2회, Death Cross: 1회
✅ RSI 과매수: 30회 (현재 74.51, 과매수 상태)
✅ MACD 크로스: 상승 4회, 하락 4회
✅ BB 돌파: 상단 18회, 하단 1회
✅ 최근 10일 신호 분석 완료
```

---

## 3️⃣ AI 예측 모델 테스트

### 3.1 LSTM 모델 테스트

```python
# test_05_lstm_prediction.py
from src.analysis.prediction_models import LSTMPredictor
from src.database.database import Database
from datetime import datetime, timedelta

db = Database()

# 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# LSTM 모델 생성 및 훈련
lstm = LSTMPredictor()
X, y = lstm.prepare_data(ohlcv_df['close'].values)
print(f"훈련 데이터 크기: X={X.shape}, y={y.shape}")

# 모델 훈련
history = lstm.train(X, y, epochs=50, verbose=0)
print(f"훈련 완료: 최종 손실 = {history.history['loss'][-1]:.6f}")

# 미래 예측
predictions = lstm.predict_future(ohlcv_df, days=7)
print(f"7일 예측 가격: {predictions}")
print(f"예측 가격 변화 범위: {predictions.min():.0f} ~ {predictions.max():.0f}")

# 결과 저장
db.add_prediction(symbol, datetime.now().date() + timedelta(days=7),
                 "LSTM", predictions[-1])
```

**테스트 항목**:
- [ ] 데이터 전처리 성공
- [ ] 모델 생성 성공
- [ ] 훈련 완료 (손실 감소 확인)
- [ ] 7일 예측 완료
- [ ] 예측값이 합리적 범위 내
- [ ] DB에 저장 성공

**예상 결과**:
```
훈련 데이터 크기: X=(168, 30), y=(168,)
훈련 완료: 최종 손실 = 0.001234
7일 예측 가격: [70500. 70800. 71200. 71500. 72000. 72300. 72600.]
```

### 3.2 XGBoost 모델 테스트

```python
# test_06_xgboost_prediction.py
from src.analysis.prediction_models import XGBoostPredictor
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# 기술적 지표 추가
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

# XGBoost 모델 생성 및 훈련
xgb = XGBoostPredictor()
X, y = xgb.prepare_data(df_with_indicators)
print(f"훈련 데이터 크기: X={X.shape}, y={y.shape}")

# 모델 훈련
xgb.train(X, y)
print("✓ XGBoost 모델 훈련 완료")

# 미래 예측
predictions = xgb.predict_future(df_with_indicators, days=7)
print(f"7일 예측 가격: {predictions}")

# 결과 저장
db.add_prediction(symbol, datetime.now().date() + timedelta(days=7),
                 "XGBoost", predictions[-1])
```

**테스트 항목**:
- [ ] 기술적 지표 포함 데이터 생성 성공
- [ ] 모델 훈련 성공
- [ ] 7일 예측 완료
- [ ] LSTM과 XGBoost 결과 비교 가능
- [ ] DB에 저장 성공

### 3.3 예측 결과 조회

```python
# test_07_prediction_retrieval.py
predictions = db.get_predictions("005930", model_name="LSTM")
print(f"저장된 LSTM 예측: {len(predictions)}건")
for pred in predictions[:3]:
    print(f"  - {pred.prediction_date}: {pred.predicted_price:.0f}원 (신뢰도: {pred.confidence}%)")
```

**테스트 항목**:
- [ ] 저장된 예측 조회 성공
- [ ] 모델별 필터링 작동
- [ ] 시간순 정렬 확인

---

## 4️⃣ 매매 전략 테스트

### 4.1 SMA 크로스오버 전략

```python
# test_08_sma_strategy.py
from src.strategy import SMAStrategy
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# 기술적 지표 추가
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

# SMA 전략 실행
strategy = SMAStrategy(short_period=5, long_period=20)
signals = strategy.generate_signals(df_with_indicators)

print(f"생성된 신호: {len(signals)}")
print(f"매수 신호: {(signals == 1).sum()}")
print(f"매도 신호: {(signals == -1).sum()}")
print(f"최근 신호: {signals.iloc[-1]}")
```

**테스트 항목**:
- [ ] SMA 계산 정상
- [ ] 신호 생성 성공 (1: 매수, -1: 매도, 0: 유지)
- [ ] 신호 수 합리적
- [ ] 신호 타이밍 검증

### 4.2 RSI 과매수/과매도 전략

```python
# test_09_rsi_strategy.py
from src.strategy import RSIStrategy
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# 기술적 지표 추가
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

# RSI 전략 실행
strategy = RSIStrategy(rsi_period=14, oversold=30, overbought=70)
signals = strategy.generate_signals(df_with_indicators)

print(f"생성된 신호: {len(signals)}")
print(f"매수 신호 (과매도): {(signals == 1).sum()}")
print(f"매도 신호 (과매수): {(signals == -1).sum()}")
current_rsi = df_with_indicators['RSI_14'].iloc[-1]
print(f"현재 RSI: {current_rsi:.2f} -> 신호: {signals.iloc[-1]}")
```

**테스트 항목**:
- [ ] RSI 기반 신호 생성 성공
- [ ] 과매도(30 이하) 시 매수 신호
- [ ] 과매수(70 이상) 시 매도 신호
- [ ] 신호 수 합리적

### 4.3 거래 기록

```python
# test_10_trade_recording.py
# 매수 기록
db.add_trade("005930", "BUY", quantity=10, price=70000,
            strategy="SMA_CROSSOVER", signal_strength=0.8)
print("✓ 매수 기록 완료")

# 매도 기록
db.add_trade("005930", "SELL", quantity=10, price=71000,
            strategy="SMA_CROSSOVER", signal_strength=0.7)
print("✓ 매도 기록 완료")

# 거래 내역 조회
trades = db.get_trades("005930")
print(f"총 거래: {len(trades)}건")
for trade in trades:
    print(f"  - {trade.trade_date}: {trade.trade_type} {trade.quantity}주 @ {trade.price}원")
```

**테스트 항목**:
- [ ] 매수/매도 기록 성공
- [ ] 거래 내역 조회 성공
- [ ] 수수료 자동 계산
- [ ] 거래액 계산 정확

---

## 5️⃣ 백테스팅 엔진 테스트

### 5.1 백테스팅 실행

```python
# test_11_backtest_engine.py
from src.strategy import SMAStrategy
from src.execution import BacktestEngine
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

db = Database()

# 데이터 조회 (1년)
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=365)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

# 기술적 지표 추가
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

# SMA 전략
strategy = SMAStrategy(short_period=5, long_period=20)

# 백테스팅 실행
backtest = BacktestEngine(initial_capital=10000000)
result = backtest.run(strategy, df_with_indicators)

print(f"초기 자본: 10,000,000원")
print(f"최종 자본: {result['final_capital']:,.0f}원")
print(f"총 수익률: {result['total_return']:.2f}%")
print(f"샤프 비율: {result['sharpe_ratio']:.2f}")
print(f"최대 낙폭: {result['max_drawdown']:.2f}%")
print(f"승률: {result['win_rate']:.2f}%")
print(f"거래 횟수: {result['total_trades']}회")
```

**테스트 항목**:
- [ ] 백테스팅 실행 성공
- [ ] 수익률 계산 정확
- [ ] 샤프 비율 계산 정확
- [ ] 최대 낙폭 계산 정확
- [ ] 승률 계산 정확
- [ ] 거래 내역 추적 정확

**예상 결과**:
```
초기 자본: 10,000,000원
최종 자본: 12,637,229원
총 수익률: 26.37%
샤프 비율: 3.29
최대 낙폭: -3.29%
승률: 86.36%
거래 횟수: 22회
```

### 5.2 백테스트 결과 저장

```python
# test_12_backtest_save.py
db.add_backtest_result(
    strategy_name="SMA_CROSSOVER",
    start_date=start_date,
    end_date=end_date,
    initial_capital=10000000,
    final_capital=result['final_capital'],
    metrics={
        'total_return': result['total_return'],
        'annual_return': result['annual_return'],
        'sharpe_ratio': result['sharpe_ratio'],
        'max_drawdown': result['max_drawdown'],
        'win_rate': result['win_rate'],
        'total_trades': result['total_trades'],
        'profitable_trades': result['profitable_trades']
    }
)
print("✓ 백테스트 결과 저장 완료")
```

**테스트 항목**:
- [ ] 결과 저장 성공
- [ ] 결과 조회 가능

---

## 6️⃣ 포트폴리오 관리 테스트

### 6.1 포트폴리오 업데이트

```python
# test_13_portfolio_management.py
from src.database.database import Database

db = Database()

# 포트폴리오 업데이트 (삼성전자 10주 매수, 평균가 70,000원)
portfolio = db.update_portfolio("005930", quantity=10, avg_buy_price=70000)
print(f"✓ 포트폴리오 업데이트: {portfolio.stock_id} {portfolio.quantity}주 @ {portfolio.avg_buy_price}원")

# 추가 매수 (5주 추가, 평균가 재계산)
portfolio = db.update_portfolio("005930", quantity=15, avg_buy_price=70333.33)
print(f"✓ 포트폴리오 수정: {portfolio.quantity}주 @ {portfolio.avg_buy_price}원")
```

**테스트 항목**:
- [ ] 포트폴리오 추가 성공
- [ ] 포트폴리오 수정 성공
- [ ] 타임스탐프 업데이트 확인

### 6.2 포트폴리오 조회

```python
# test_14_portfolio_retrieval.py
portfolio = db.get_portfolio()
print(f"현재 포트폴리오: {len(portfolio)}개 종목")

for pos in portfolio:
    stock = db.get_stock(pos.stock_id)
    current_price = 71000  # 현재가 (실제로는 API에서 조회)
    current_value = pos.quantity * current_price
    cost = pos.quantity * pos.avg_buy_price
    profit = current_value - cost
    profit_rate = (profit / cost) * 100 if cost > 0 else 0

    print(f"  - {stock.ticker}: {pos.quantity}주 @ {pos.avg_buy_price:.0f}원")
    print(f"    현재가: {current_price}원, 현재자산: {current_value:,.0f}원")
    print(f"    손익: {profit:,.0f}원 ({profit_rate:.2f}%)")
```

**테스트 항목**:
- [ ] 포트폴리오 조회 성공
- [ ] 손익 계산 정확
- [ ] 수익률 계산 정확

---

## 7️⃣ 데이터베이스 CRUD 테스트

### 7.1 Stock 테이블

```python
# test_15_stock_crud.py
from src.database.database import Database

db = Database()

# Create: 종목 추가
stock = db.add_stock("000660", "LG화학", "KOSPI", "화학")
print(f"✓ 종목 추가: {stock.ticker} - {stock.name}")

# Read: 종목 조회
retrieved = db.get_stock("000660")
assert retrieved.ticker == "000660", "종목 조회 실패"
print(f"✓ 종목 조회: {retrieved.name}")

# Read All: 전체 종목 조회
all_stocks = db.get_all_stocks()
assert len(all_stocks) > 0, "종목 목록이 비어있음"
print(f"✓ 전체 종목 조회: {len(all_stocks)}개")
```

**테스트 항목**:
- [ ] 종목 추가 성공
- [ ] 종목 조회 성공
- [ ] 종목 중복 추가 시 기존 데이터 반환
- [ ] 전체 종목 조회 성공

### 7.2 StockPrice 테이블

```python
# test_16_stockprice_crud.py
import pandas as pd

# Create: 주가 데이터 추가
df = pd.DataFrame({
    'Open': [70000, 71000, 72000],
    'High': [71000, 72000, 73000],
    'Low': [69000, 70000, 71000],
    'Close': [70500, 71500, 72500],
    'Volume': [1000000, 1100000, 1200000],
    'Amount': [70500000000, 78650000000, 87000000000]
}, index=pd.date_range('2025-10-20', periods=3))

count = db.add_stock_prices("005930", df)
print(f"✓ 주가 데이터 추가: {count}건")

# Read: 주가 데이터 조회
prices = db.get_stock_prices("005930")
assert len(prices) > 0, "주가 데이터가 없음"
print(f"✓ 주가 데이터 조회: {len(prices)}건")
print(prices.tail(3))
```

**테스트 항목**:
- [ ] 주가 데이터 추가 성공
- [ ] 데이터 형식 변환 정상
- [ ] 중복 추가 시 건너뜀
- [ ] 주가 데이터 조회 성공
- [ ] 기간 필터링 작동

---

## 8️⃣ 웹 대시보드 테스트

### 8.1 서버 실행

```bash
# test_17_webapp_start.py
cd webapp
python app.py
```

**테스트 항목**:
- [ ] Flask 서버 정상 실행
- [ ] 포트 5000에서 서비스 중
- [ ] 에러 로그 없음

### 8.2 메인 페이지

```
방문: http://localhost:5000
```

**테스트 항목**:
- [ ] 메인 페이지 로드 성공
- [ ] 레이아웃 정상 렌더링
- [ ] 메뉴 항목 모두 표시
- [ ] 반응형 디자인 확인

### 8.3 API 테스트

#### 8.3.1 주가 조회 API

```bash
curl "http://localhost:5000/api/stock?ticker=005930"
```

**테스트 항목**:
- [ ] API 응답 성공 (200)
- [ ] JSON 형식 정상
- [ ] 주가 데이터 포함
- [ ] 기술적 지표 포함

#### 8.3.2 기술적 지표 API

```bash
curl "http://localhost:5000/api/indicators?ticker=005930&period=20"
```

**테스트 항목**:
- [ ] 지표 계산 성공
- [ ] 모든 지표 포함 (SMA, RSI, MACD, BB 등)
- [ ] 숫자 데이터 유효성

#### 8.3.3 AI 예측 API

```bash
curl "http://localhost:5000/api/predict?ticker=005930&days=7"
```

**테스트 항목**:
- [ ] 예측 실행 성공
- [ ] 7일 예측값 반환
- [ ] 예측 신뢰도 포함
- [ ] 응답 시간 적절 (< 10초)

#### 8.3.4 백테스팅 API

```bash
curl -X POST "http://localhost:5000/api/backtest" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"005930", "strategy":"SMA_CROSSOVER"}'
```

**테스트 항목**:
- [ ] 백테스팅 실행 성공
- [ ] 결과 반환 (수익률, 샤프비율 등)
- [ ] 응답 시간 적절 (< 30초)

#### 8.3.5 포트폴리오 API

```bash
curl "http://localhost:5000/api/portfolio"
```

**테스트 항목**:
- [ ] 포트폴리오 조회 성공
- [ ] 보유 종목 목록
- [ ] 손익 정보 포함

### 8.4 페이지별 기능 테스트

#### 분석 페이지
```
주소: http://localhost:5000/analysis
```

- [ ] 종목 검색 가능
- [ ] 기술적 지표 차트 표시
- [ ] 신호 표시 (매수/매도)
- [ ] 차트 인터랙션 작동

#### 예측 페이지
```
주소: http://localhost:5000/predict
```

- [ ] 모델 선택 가능 (LSTM, XGBoost)
- [ ] 예측 기간 선택 가능
- [ ] 예측 결과 표시
- [ ] 신뢰도 표시

#### 백테스팅 페이지
```
주소: http://localhost:5000/backtest
```

- [ ] 전략 선택 가능
- [ ] 기간 선택 가능
- [ ] 초기 자본 입력 가능
- [ ] 결과 표시 (수익률, 거래수 등)

#### 포트폴리오 페이지
```
주소: http://localhost:5000/portfolio
```

- [ ] 보유 종목 목록
- [ ] 손익 현황
- [ ] 자산 배분 차트
- [ ] 거래 내역

---

## 9️⃣ 통합 테스트

### 9.1 전체 워크플로우 테스트

```python
# test_18_full_workflow.py
from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from src.analysis.prediction_models import LSTMPredictor
from src.strategy import SMAStrategy
from src.execution import BacktestEngine
from datetime import datetime, timedelta

print("=" * 60)
print("AutoQuant 전체 워크플로우 테스트")
print("=" * 60)

db = Database()

# 1단계: 데이터 조회
print("\n1단계: KIS에서 데이터 조회")
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)
print(f"✓ {symbol} {len(ohlcv_df)}건 데이터 조회")

# 2단계: 기술적 지표 계산
print("\n2단계: 기술적 지표 계산")
df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)
print(f"✓ {len(df_with_indicators.columns)} 개 지표 계산")

# 3단계: 신호 생성
print("\n3단계: 거래 신호 생성")
strategy = SMAStrategy(short_period=5, long_period=20)
signals = strategy.generate_signals(df_with_indicators)
print(f"✓ {(signals == 1).sum()}개 매수 신호, {(signals == -1).sum()}개 매도 신호")

# 4단계: 백테스팅
print("\n4단계: 백테스팅 실행")
backtest = BacktestEngine(initial_capital=10000000)
result = backtest.run(strategy, df_with_indicators)
print(f"✓ 수익률: {result['total_return']:.2f}%, 샤프비율: {result['sharpe_ratio']:.2f}")

# 5단계: 예측
print("\n5단계: AI 예측 실행")
lstm = LSTMPredictor()
X, y = lstm.prepare_data(ohlcv_df['close'].values)
lstm.train(X, y, epochs=30, verbose=0)
predictions = lstm.predict_future(ohlcv_df, days=7)
print(f"✓ 7일 예측 완료: {predictions[-1]:.0f}원")

# 6단계: DB 저장
print("\n6단계: 결과 저장")
db.add_backtest_result(
    "SMA_CROSSOVER_TEST",
    start_date, end_date,
    10000000, result['final_capital'],
    result
)
db.add_prediction(symbol, end_date + timedelta(days=7), "LSTM", predictions[-1])
print("✓ 결과 저장 완료")

print("\n" + "=" * 60)
print("✅ 전체 워크플로우 테스트 완료!")
print("=" * 60)
```

**테스트 항목**:
- [ ] 모든 단계 성공
- [ ] 오류 없음
- [ ] 데이터 일관성 유지
- [ ] 성능 적절 (전체 소요시간 < 2분)

---

## 🔟 성능 및 안정성 테스트

### 10.1 다중 종목 처리

```python
# test_19_multiple_stocks.py
from src.database.database import Database

db = Database()

# 상위 10개 종목 조회
symbols_df = db.get_available_symbols_from_kis()
symbols = symbols_df['symbol_code'].head(10).tolist()

print(f"테스트 종목: {symbols}")

for symbol in symbols:
    ohlcv_df = db.get_daily_ohlcv_from_kis(symbol)
    print(f"✓ {symbol}: {len(ohlcv_df)}건")
```

**테스트 항목**:
- [ ] 모든 종목 조회 성공
- [ ] 조회 속도 적절 (종목당 < 1초)
- [ ] 메모리 누수 없음

### 10.2 대량 데이터 처리

```python
# test_20_large_data.py
# 1년 데이터로 처리 속도 테스트
from datetime import timedelta
import time

start_time = time.time()

ohlcv_df = db.get_daily_ohlcv_from_kis(
    "005930",
    datetime(2024, 1, 1),
    datetime(2025, 1, 1)
)

elapsed = time.time() - start_time
print(f"✓ 1년 데이터 ({len(ohlcv_df)}건) 조회 시간: {elapsed:.2f}초")
```

**테스트 항목**:
- [ ] 대량 데이터 조회 성공
- [ ] 조회 시간 적절 (< 5초)
- [ ] 메모리 사용량 적절

### 10.3 동시 요청 처리

```python
# test_21_concurrent_requests.py
import concurrent.futures
import time

def fetch_stock_data(symbol):
    try:
        ohlcv_df = db.get_daily_ohlcv_from_kis(symbol)
        return f"✓ {symbol}: {len(ohlcv_df)}건"
    except Exception as e:
        return f"✗ {symbol}: {e}"

symbols = symbols_df['symbol_code'].head(20).tolist()

start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_stock_data, symbols))

elapsed = time.time() - start_time

print(f"동시 처리 (20개 종목, 5개 워커): {elapsed:.2f}초")
for result in results:
    print(result)
```

**테스트 항목**:
- [ ] 동시 요청 처리 성공
- [ ] 데이터 무결성 유지
- [ ] 응답 시간 적절

---

## ✅ 최종 체크리스트

### 데이터 수집
- [x] KIS PostgreSQL 데이터 조회 완료 (2025-10-23 완료)
- [x] 종목별 일봉 데이터 확인 (2025-10-23 완료)
- [x] 4,359개 종목 가용성 확인 (2025-10-23 완료)

### 기술적 분석
- [x] 10개 이상 지표 계산 성공 (2025-10-23 완료 - 16개 컬럼)
- [x] 신뢰할 수 있는 신호 생성 (2025-10-23 완료)
- [x] 매수/매도 신호 구분 (2025-10-23 완료 - 8개 신호)

### AI 예측
- [ ] LSTM 모델 훈련 완료
- [ ] XGBoost 모델 훈련 완료
- [ ] 7일 예측 정확도 검증

### 매매 전략
- [ ] SMA 크로스오버 신호 생성
- [ ] RSI 전략 신호 생성
- [ ] 확장 가능한 구조 확인

### 백테스팅
- [ ] 과거 데이터 기반 검증 성공
- [ ] 성능 지표 계산 정확
- [ ] 거래 내역 추적 정확

### 포트폴리오
- [ ] 포지션 추적 정상
- [ ] 손익 계산 정확
- [ ] 자산 배분 관리 가능

### 웹 대시보드
- [ ] 서버 정상 실행
- [ ] 모든 API 정상 작동
- [ ] UI 반응형 디자인

### 데이터베이스
- [ ] PostgreSQL 연결 안정
- [ ] CRUD 작업 정상
- [ ] 데이터 무결성 유지

### 성능 & 안정성
- [ ] 다중 종목 처리 정상
- [ ] 대량 데이터 처리 가능
- [ ] 동시 요청 처리 가능
- [ ] 메모리 누수 없음
- [ ] 에러 처리 적절

---

## 📝 테스트 결과 기록

### 테스트 실행 정보
- **테스트 날짜**: 2025-10-23
- **테스트자**: Claude Code
- **테스트 환경**: Python 3.x, OS Linux, PostgreSQL 연결
- **소요 시간**: 진행 중

### 각 섹션별 결과

| 섹션 | 결과 | 비고 |
|------|------|------|
| 데이터 수집 | ✅ | 1.1, 1.2 완료 (4,359개 종목, 삼성전자 일봉 데이터) |
| 기술적 지표 | ✅ | 2.1, 2.2, 2.3 완료 (11개 지표 + 8개 매매 신호, 100% 성공) |
| AI 예측 | ⏳ | 대기 중 |
| 매매 전략 | ⏳ | 대기 중 |
| 백테스팅 | ⏳ | 대기 중 |
| 포트폴리오 | ⏳ | 대기 중 |
| 웹 대시보드 | ⏳ | 대기 중 |
| DB CRUD | ⏳ | 대기 중 |
| 성능/안정성 | ⏳ | 대기 중 |

### 발견된 이슈

#### 1. Decimal/Float 타입 충돌 - ✅ **해결 완료** (2025-10-23)
- **증상**: Stochastic, ATR, OBV 지표 계산 실패
- **원인**: KIS PostgreSQL 데이터가 Decimal 타입, TechnicalIndicators가 float 연산
- **영향**: Stochastic, ATR, OBV 3개 지표
- **해결 방법**: `technical_indicators.py`의 3개 함수에 `.astype(float)` 변환 추가
  - `calculate_stochastic()`: High, Low, Close 변환
  - `calculate_atr()`: High, Low, Close 변환
  - `calculate_obv()`: Close, Volume 변환
- **상태**: ✅ 수정 완료, 모든 지표 100% 정상 작동

### 테스트 상세 내역

#### 1. 데이터 수집 모듈 (2025-10-23)
- **1.1 PostgreSQL 데이터 조회**:
  - ✅ 4,359개 종목 조회 성공
  - ✅ 최신 거래일: 2025-10-22
  - ✅ 평균 데이터 건수: 112건/종목
  - 상세 결과: tests/user_tests/TEST_RESULTS_01_DATA_COLLECTION.md

- **1.2 특정 종목 일봉 데이터 조회**:
  - ✅ 삼성전자(005930) 66거래일 조회
  - ✅ OHLCV + 거래대금 컬럼 모두 정상
  - ✅ 데이터 품질 검증 통과 (결측치 없음)
  - ✅ 가격 유효성 검증 통과

#### 2. 기술적 지표 계산 (2025-10-23) - ✅ **수정 완료**
- **2.1 모든 지표 계산**:
  - ✅ 16개 컬럼 추가 성공 (모든 지표 100%)
  - ✅ 11개 지표 정상 작동: SMA×3, EMA×2, RSI, MACD×3, BB×3, Stochastic×2, ATR, OBV
  - ✅ 데이터 품질: 최근 데이터 NaN 없음
  - ✅ Decimal 타입 이슈 수정 완료
  - 상세 결과: tests/user_tests/TEST_RESULTS_02_TECHNICAL_INDICATORS.md

- **2.2 개별 지표 검증**:
  - ✅ RSI: 74.51 (과매수 구간, 0-100 범위 확인)
  - ✅ MACD: 상승 신호 (Histogram 계산 정확도 검증)
  - ✅ Bollinger Bands: 밴드 순서 정상, 밴드 내 위치 84.8%
  - ✅ Stochastic: %K=90.96, %D=92.53 (과매수 구간)
  - ✅ ATR: 3,243원 (높은 변동성 3.29%)
  - ✅ OBV: 상승 추세 확인
  - ✅ 이동평균선: 강한 상승 추세 확인
  - **검증 통과율: 7/7 (100%)**

- **2.3 매매 신호 생성**:
  - ✅ 8개 매매 신호 생성 완료
  - ✅ Golden Cross: 2회, Death Cross: 1회
  - ✅ RSI 과매수: 30회 (현재 74.51)
  - ✅ MACD 크로스: 상승 4회, 하락 4회
  - ✅ BB 돌파: 상단 18회, 하단 1회
  - ✅ 최근 10일 신호 분석 완료
  - **검증 통과율: 5/5 (100%)**
  - 상세 결과: tests/user_tests/TEST_RESULTS_03_TRADING_SIGNALS.md

### 개선 제안

#### ✅ 완료된 개선 사항 (2025-10-23)
1. **Decimal 타입 호환성 개선** - 완료
   - PostgreSQL Decimal 타입과 pandas float 연산의 호환성 문제 해결
   - `technical_indicators.py`에 자동 타입 변환 추가
   - 모든 기술적 지표 100% 정상 작동

#### 향후 개선 제안
1. **더 많은 기술적 지표 추가**
   - CCI (Commodity Channel Index)
   - Williams %R
   - Ichimoku Cloud

2. **지표 성능 최적화**
   - 대용량 데이터 처리 시 계산 속도 개선
   - 벡터화 연산 추가 활용

---

## 📞 지원

### 테스트 중 문제 발생 시

1. **로그 확인**
   ```bash
   tail -f logs/autoquant.log
   ```

2. **DB 연결 확인**
   ```bash
   python test_db_connection.py
   ```

3. **가상환경 재설정**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **캐시 정리**
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   ```

### 문서 참고
- DATABASE_SETUP.md: PostgreSQL 설정
- USER_GUIDE.md: 상세 사용 가이드
- TESTING_RESULTS.md: 이전 테스트 결과

---

**마지막 업데이트**: 2025-10-23
**버전**: 1.0
**상태**: 테스트 준비 완료
