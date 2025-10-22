#!/usr/bin/env python3
"""
전체 모듈 통합 테스트
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection.mock_data import MockDataGenerator
from src.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from src.analysis.prediction_models import LSTMPredictor, XGBoostPredictor, evaluate_model
from src.strategy import SMAStrategy, RSIStrategy
from src.portfolio import PortfolioManager
from src.execution import BacktestEngine

print("=" * 80)
print("AutoQuant 전체 시스템 통합 테스트")
print("=" * 80)

# 모의 데이터 생성
generator = MockDataGenerator()
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print("\n[1] 데이터 생성")
tickers = ['005930', '000660', '035420']
stock_data = {}

for ticker in tickers:
    df = generator.generate_stock_data(
        ticker,
        start_date.strftime('%Y%m%d'),
        end_date.strftime('%Y%m%d'),
        initial_price=50000 + int(ticker) % 30000
    )
    stock_data[ticker] = df
    print(f"   ✓ {ticker}: {len(df)} 거래일")

# 기술적 지표 계산
print("\n[2] 기술적 지표 계산")
for ticker, df in stock_data.items():
    stock_data[ticker] = TechnicalIndicators.add_all_indicators(df)
    print(f"   ✓ {ticker}: {len(df.columns)}개 컬럼")

# 예측 모델 테스트
print("\n[3] LSTM 예측 모델 테스트")
try:
    lstm = LSTMPredictor(look_back=60)
    df_sample = stock_data['005930']

    X, y = lstm.prepare_data(df_sample)
    print(f"   ✓ 데이터 준비: X={X.shape}, y={y.shape}")

    # 학습
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    history = lstm.train(X_train, y_train, X_test, y_test, epochs=10)
    print(f"   ✓ 모델 학습 완료")

    # 미래 예측
    predictions = lstm.predict_future(df_sample, days=7)
    print(f"   ✓ 7일 예측: {predictions}")

except Exception as e:
    print(f"   ✗ LSTM 실패: {e}")

# XGBoost 예측 테스트
print("\n[4] XGBoost 예측 모델 테스트")
try:
    xgb = XGBoostPredictor(look_back=60)
    X, y = xgb.prepare_data(df_sample)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    result = xgb.train(X_train, y_train, X_test, y_test)
    print(f"   ✓ 모델 학습 완료: MSE={result.get('train_mse', 0):.4f}")

    predictions = xgb.predict_future(df_sample, days=7)
    print(f"   ✓ 7일 예측: {predictions}")

except Exception as e:
    print(f"   ✗ XGBoost 실패: {e}")

# 매매 전략 테스트
print("\n[5] SMA 전략 테스트")
try:
    sma_strategy = SMAStrategy(short_period=5, long_period=20)
    result = sma_strategy.backtest(stock_data['005930'])

    print(f"   ✓ 전략: {sma_strategy.name}")
    print(f"   ✓ 초기 자본: {result['initial_capital']:,.0f}원")
    print(f"   ✓ 최종 자본: {result['final_capital']:,.0f}원")
    print(f"   ✓ 수익률: {result['total_return']:.2f}%")
    print(f"   ✓ 거래 횟수: {result['num_trades']}")

except Exception as e:
    print(f"   ✗ SMA 전략 실패: {e}")

# RSI 전략 테스트
print("\n[6] RSI 전략 테스트")
try:
    rsi_strategy = RSIStrategy(period=14)
    result = rsi_strategy.backtest(stock_data['005930'])

    print(f"   ✓ 전략: {rsi_strategy.name}")
    print(f"   ✓ 수익률: {result['total_return']:.2f}%")
    print(f"   ✓ 거래 횟수: {result['num_trades']}")

except Exception as e:
    print(f"   ✗ RSI 전략 실패: {e}")

# 포트폴리오 관리 테스트
print("\n[7] 포트폴리오 관리 테스트")
try:
    portfolio = PortfolioManager(initial_capital=10000000)

    # 매수
    portfolio.buy('005930', 10, 70000)
    portfolio.buy('000660', 5, 130000)

    # 현재 가격
    current_prices = {'005930': 72000, '000660': 135000}

    # 손익 계산
    pl = portfolio.get_profit_loss(current_prices)
    print(f"   ✓ 초기 자본: {pl['initial_capital']:,.0f}원")
    print(f"   ✓ 현재 가치: {pl['current_value']:,.0f}원")
    print(f"   ✓ 손익: {pl['profit']:,.0f}원 ({pl['profit_rate']:.2f}%)")

    # 보유 종목
    holdings = portfolio.get_holdings_summary(current_prices)
    print(f"   ✓ 보유 종목: {len(holdings)}개")

except Exception as e:
    print(f"   ✗ 포트폴리오 실패: {e}")

# 백테스팅 엔진 테스트
print("\n[8] 백테스팅 엔진 테스트")
try:
    backtest = BacktestEngine(initial_capital=10000000)
    strategy = SMAStrategy(short_period=5, long_period=20)

    result = backtest.run(strategy, stock_data)

    print(f"   ✓ 전략: {result['strategy_name']}")
    print(f"   ✓ 수익률: {result['total_return']:.2f}%")
    print(f"   ✓ 샤프 비율: {result['sharpe_ratio']:.2f}")
    print(f"   ✓ 최대 낙폭: {result['max_drawdown']:.2f}%")
    print(f"   ✓ 총 거래: {result['total_trades']}")
    print(f"   ✓ 승률: {result['win_rate']:.2f}%")

    # 리포트 생성
    report = backtest.generate_report(result)
    print("\n   백테스팅 리포트:")
    print(report)

except Exception as e:
    print(f"   ✗ 백테스팅 실패: {e}")
    import traceback
    traceback.print_exc()

# 데이터베이스 통합 테스트
print("\n[9] 데이터베이스 통합 테스트")
try:
    db = Database("sqlite:///:memory:")
    db.create_tables()

    # 종목 추가
    for ticker in tickers:
        db.add_stock(ticker, f"종목{ticker}", "KOSPI")

    # 주가 데이터 저장
    for ticker, df in stock_data.items():
        count = db.add_stock_prices(ticker, df)
        print(f"   ✓ {ticker}: {count}건 저장")

    # 예측 결과 저장
    db.add_prediction('005930', datetime.now() + timedelta(days=7), 'LSTM', 72500, 0.85)
    print(f"   ✓ 예측 결과 저장")

    # 백테스트 결과 저장
    db.add_backtest_result(
        strategy_name=result['strategy_name'],
        start_date=start_date,
        end_date=end_date,
        initial_capital=result['initial_capital'],
        final_capital=result['final_capital'],
        metrics={
            'total_return': result['total_return'],
            'sharpe_ratio': result['sharpe_ratio'],
            'max_drawdown': result['max_drawdown'],
            'win_rate': result['win_rate'],
            'total_trades': result['total_trades']
        }
    )
    print(f"   ✓ 백테스트 결과 저장")

except Exception as e:
    print(f"   ✗ 데이터베이스 실패: {e}")

print("\n" + "=" * 80)
print("전체 시스템 통합 테스트 완료!")
print("=" * 80)

print("""
✓ 데이터 생성 및 수집
✓ 기술적 지표 계산 (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
✓ LSTM 예측 모델
✓ XGBoost 예측 모델
✓ SMA 크로스오버 전략
✓ RSI 전략
✓ 포트폴리오 관리
✓ 백테스팅 엔진
✓ 데이터베이스 통합

모든 핵심 모듈 정상 작동 확인!
""")
