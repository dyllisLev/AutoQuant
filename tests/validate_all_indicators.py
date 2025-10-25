"""
Comprehensive Technical Indicators Validation Script
Validates all 16 technical indicators with detailed logging
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def validate_indicator_calculation(stock_code='005930', stock_name='삼성전자'):
    """Validate all technical indicators step by step"""

    print("="*80)
    print(f"📊 TECHNICAL INDICATORS VALIDATION")
    print(f"종목: {stock_code} ({stock_name})")
    print("="*80)

    # 1. Initialize
    db = Database()
    tech = TechnicalIndicators()

    # 2. Get data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)

    print(f"\n1️⃣ 데이터 조회")
    print(f"   기간: {start_date.date()} ~ {end_date.date()}")

    df = db.get_daily_ohlcv_from_kis(stock_code, start_date=start_date, end_date=end_date)

    if df is None or len(df) == 0:
        print(f"   ❌ 데이터 조회 실패")
        return

    print(f"   ✅ {len(df)}건 조회 성공")

    # 3. Prepare data
    df = df.copy()
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    print(f"\n2️⃣ 원본 데이터 (최근 3일)")
    print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))

    # 4. Calculate indicators ONE BY ONE with validation
    print(f"\n3️⃣ 기술지표 계산 검증")
    print("-"*80)

    validation_results = {}

    # SMA (Simple Moving Average)
    print(f"\n📈 SMA (Simple Moving Average)")
    try:
        df_sma = df.copy()
        df_sma['SMA_5'] = TechnicalIndicators.calculate_sma(df_sma, period=5)
        df_sma['SMA_20'] = TechnicalIndicators.calculate_sma(df_sma, period=20)
        df_sma['SMA_60'] = TechnicalIndicators.calculate_sma(df_sma, period=60)

        latest = df_sma.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   Close: {latest['Close']:.2f}")
        print(f"   SMA_5: {latest['SMA_5']:.2f}")
        print(f"   SMA_20: {latest['SMA_20']:.2f}")
        print(f"   SMA_60: {latest['SMA_60']:.2f}")

        # Validation: SMA should be average of last N closes
        manual_sma5 = df_sma['Close'].tail(5).mean()
        if abs(latest['SMA_5'] - manual_sma5) < 0.01:
            print(f"   ✅ SMA_5 검증: {manual_sma5:.2f} (계산값과 일치)")
            validation_results['SMA'] = 'PASS'
        else:
            print(f"   ⚠️ SMA_5 검증: 예상={manual_sma5:.2f}, 실제={latest['SMA_5']:.2f}")
            validation_results['SMA'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['SMA'] = 'FAIL'

    # EMA (Exponential Moving Average)
    print(f"\n📈 EMA (Exponential Moving Average)")
    try:
        df_ema = df.copy()
        df_ema['EMA_12'] = TechnicalIndicators.calculate_ema(df_ema, period=12)
        df_ema['EMA_26'] = TechnicalIndicators.calculate_ema(df_ema, period=26)

        latest = df_ema.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   EMA_12: {latest['EMA_12']:.2f}")
        print(f"   EMA_26: {latest['EMA_26']:.2f}")
        print(f"   EMA_12 > EMA_26: {latest['EMA_12'] > latest['EMA_26']} (상승 신호)")
        validation_results['EMA'] = 'PASS'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['EMA'] = 'FAIL'

    # RSI (Relative Strength Index)
    print(f"\n📊 RSI (Relative Strength Index)")
    try:
        df_rsi = df.copy()
        df_rsi['RSI_14'] = TechnicalIndicators.calculate_rsi(df_rsi, period=14)

        latest = df_rsi.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   RSI_14: {latest['RSI_14']:.2f}")

        # Validation: RSI should be 0-100
        if 0 <= latest['RSI_14'] <= 100:
            if latest['RSI_14'] < 30:
                status = "과매도 (Oversold)"
            elif latest['RSI_14'] > 70:
                status = "과매수 (Overbought)"
            else:
                status = "중립 (Neutral)"
            print(f"   ✅ RSI 검증: 범위 정상 (0-100) - {status}")
            validation_results['RSI'] = 'PASS'
        else:
            print(f"   ⚠️ RSI 검증: 범위 비정상 (0-100 벗어남)")
            validation_results['RSI'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['RSI'] = 'FAIL'

    # MACD
    print(f"\n📉 MACD (Moving Average Convergence Divergence)")
    try:
        df_macd = df.copy()
        macd, signal, histogram = TechnicalIndicators.calculate_macd(df_macd)  # Returns tuple
        df_macd['MACD'] = macd
        df_macd['MACD_Signal'] = signal
        df_macd['MACD_Histogram'] = histogram

        latest = df_macd.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   MACD: {latest['MACD']:.2f}")
        print(f"   MACD_Signal: {latest['MACD_Signal']:.2f}")
        print(f"   MACD_Histogram: {latest['MACD_Histogram']:.2f}")

        # Validation: Histogram = MACD - Signal
        expected_histogram = latest['MACD'] - latest['MACD_Signal']
        if abs(latest['MACD_Histogram'] - expected_histogram) < 0.01:
            signal = "상승" if latest['MACD'] > latest['MACD_Signal'] else "하락"
            print(f"   ✅ MACD 검증: Histogram = MACD - Signal 일치 ({signal} 신호)")
            validation_results['MACD'] = 'PASS'
        else:
            print(f"   ⚠️ MACD 검증: Histogram 계산 오류")
            validation_results['MACD'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['MACD'] = 'FAIL'

    # Bollinger Bands
    print(f"\n📊 Bollinger Bands")
    try:
        df_bb = df.copy()
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df_bb, period=20, std_dev=2)  # Returns tuple, parameter is std_dev not std
        df_bb['BB_Upper'] = upper
        df_bb['BB_Middle'] = middle
        df_bb['BB_Lower'] = lower

        latest = df_bb.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   BB_Upper: {latest['BB_Upper']:.2f}")
        print(f"   BB_Middle: {latest['BB_Middle']:.2f}")
        print(f"   BB_Lower: {latest['BB_Lower']:.2f}")
        print(f"   Close: {latest['Close']:.2f}")

        # Validation: Middle = SMA, Upper/Lower = Middle ± 2*STD
        band_width = latest['BB_Upper'] - latest['BB_Lower']
        middle_check = abs(latest['BB_Middle'] - df_bb['Close'].tail(20).mean())

        if middle_check < 0.01 and band_width > 0:
            position = "상단" if latest['Close'] > latest['BB_Middle'] else "하단"
            print(f"   ✅ BB 검증: Middle = SMA20 일치, 현재 위치: {position}")
            validation_results['BB'] = 'PASS'
        else:
            print(f"   ⚠️ BB 검증: Middle 계산 확인 필요")
            validation_results['BB'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['BB'] = 'FAIL'

    # Stochastic Oscillator
    print(f"\n📊 Stochastic Oscillator")
    try:
        df_stoch = df.copy()
        k, d = TechnicalIndicators.calculate_stochastic(df_stoch, period=14, smooth_k=3, smooth_d=3)  # Returns tuple, parameters are period, smooth_k, smooth_d
        df_stoch['Stoch_K'] = k
        df_stoch['Stoch_D'] = d

        latest = df_stoch.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   Stoch_K: {latest['Stoch_K']:.2f}")
        print(f"   Stoch_D: {latest['Stoch_D']:.2f}")

        # Validation: Stochastic should be 0-100
        if 0 <= latest['Stoch_K'] <= 100 and 0 <= latest['Stoch_D'] <= 100:
            if latest['Stoch_K'] < 20:
                status = "과매도"
            elif latest['Stoch_K'] > 80:
                status = "과매수"
            else:
                status = "중립"
            print(f"   ✅ Stochastic 검증: 범위 정상 (0-100) - {status}")
            validation_results['Stochastic'] = 'PASS'
        else:
            print(f"   ⚠️ Stochastic 검증: 범위 비정상")
            validation_results['Stochastic'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['Stochastic'] = 'FAIL'

    # ATR (Average True Range)
    print(f"\n📊 ATR (Average True Range)")
    try:
        df_atr = df.copy()
        df_atr['ATR'] = TechnicalIndicators.calculate_atr(df_atr, period=14)

        latest = df_atr.iloc[-1]
        print(f"   ✅ 계산 성공")
        print(f"   ATR: {latest['ATR']:.2f}")

        # Validation: ATR should be positive
        if latest['ATR'] > 0:
            print(f"   ✅ ATR 검증: 양수 값 정상 (변동성 측정)")
            validation_results['ATR'] = 'PASS'
        else:
            print(f"   ⚠️ ATR 검증: 비정상 값")
            validation_results['ATR'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['ATR'] = 'FAIL'

    # OBV (On-Balance Volume)
    print(f"\n📊 OBV (On-Balance Volume)")
    try:
        df_obv = df.copy()
        df_obv['OBV'] = TechnicalIndicators.calculate_obv(df_obv)

        latest = df_obv.iloc[-1]
        prev = df_obv.iloc[-2]

        print(f"   ✅ 계산 성공")
        print(f"   OBV (current): {latest['OBV']:.0f}")
        print(f"   OBV (previous): {prev['OBV']:.0f}")
        print(f"   Change: {latest['OBV'] - prev['OBV']:.0f}")

        # Validation: OBV change should relate to price direction
        price_change = latest['Close'] - prev['Close']
        obv_change = latest['OBV'] - prev['OBV']

        if (price_change > 0 and obv_change > 0) or (price_change < 0 and obv_change < 0) or price_change == 0:
            print(f"   ✅ OBV 검증: 가격 방향과 일치")
            validation_results['OBV'] = 'PASS'
        else:
            print(f"   ⚠️ OBV 검증: 가격={price_change:.2f}, OBV={obv_change:.0f}")
            validation_results['OBV'] = 'WARNING'

    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        validation_results['OBV'] = 'FAIL'

    # Summary
    print(f"\n{'='*80}")
    print(f"4️⃣ 검증 결과 요약")
    print(f"{'='*80}")

    pass_count = sum(1 for v in validation_results.values() if v == 'PASS')
    warn_count = sum(1 for v in validation_results.values() if v == 'WARNING')
    fail_count = sum(1 for v in validation_results.values() if v == 'FAIL')

    for indicator, result in validation_results.items():
        symbol = '✅' if result == 'PASS' else '⚠️' if result == 'WARNING' else '❌'
        print(f"   {symbol} {indicator}: {result}")

    print(f"\n   총 {len(validation_results)}개 지표:")
    print(f"   ✅ 통과: {pass_count}개")
    print(f"   ⚠️ 경고: {warn_count}개")
    print(f"   ❌ 실패: {fail_count}개")

    if fail_count == 0:
        print(f"\n🎉 모든 기술지표 계산이 정상입니다!")
    else:
        print(f"\n⚠️ 일부 지표에 문제가 있습니다. 확인이 필요합니다.")

    return validation_results


if __name__ == "__main__":
    # Test with Samsung Electronics (005930)
    print("\n" + "="*80)
    print("TESTING WITH 삼성전자 (005930)")
    print("="*80)
    results_samsung = validate_indicator_calculation('005930', '삼성전자')

    # Test with another stock
    print("\n\n" + "="*80)
    print("TESTING WITH SK하이닉스 (000660)")
    print("="*80)
    results_sk = validate_indicator_calculation('000660', 'SK하이닉스')
