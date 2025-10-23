"""
테스트 2.2: 개별 지표 검증
USER_TEST_CHECKLIST.md의 2.2 섹션 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from datetime import datetime, timedelta

print("=" * 70)
print("테스트 2.2: 개별 지표 검증")
print("=" * 70)

# Database 인스턴스 생성
db = Database()

# 삼성전자(005930) 최근 200일 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

print(f"\n[데이터 조회 및 지표 계산]")
print("-" * 70)

try:
    ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

    # 컬럼 이름을 대문자로 변환 (TechnicalIndicators 호환)
    ohlcv_df = ohlcv_df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'amount': 'Amount'
    })

    df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)
    print(f"✓ 데이터 조회 및 지표 계산 완료: {len(df_with_indicators)}건")
except Exception as e:
    print(f"✗ 데이터 준비 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"\n[개별 지표 유효성 검증]")
print("-" * 70)

# 최신 데이터 가져오기
latest = df_with_indicators.iloc[-1]
latest_date = df_with_indicators.index[-1]

print(f"검증 기준일: {latest_date}")
print(f"종가: {latest['Close']:,.0f}원\n")

validation_passed = 0
validation_failed = 0

# 1. RSI 검증
print("[1] RSI (Relative Strength Index) 검증")
try:
    rsi = latest['RSI_14']
    print(f"  현재 RSI_14: {rsi:.2f}")

    if 0 <= rsi <= 100:
        print(f"  ✓ RSI 유효 범위 (0-100)")
        validation_passed += 1
    else:
        print(f"  ✗ RSI 범위 벗어남: {rsi:.2f}")
        validation_failed += 1

    # RSI 해석
    if rsi >= 70:
        print(f"  → 과매수 구간 (RSI >= 70)")
    elif rsi <= 30:
        print(f"  → 과매도 구간 (RSI <= 30)")
    else:
        print(f"  → 중립 구간 (30 < RSI < 70)")

except KeyError:
    print(f"  ✗ RSI_14 컬럼 없음")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ RSI 검증 실패: {e}")
    validation_failed += 1

# 2. MACD 검증
print(f"\n[2] MACD 검증")
try:
    macd = latest['MACD']
    signal = latest['MACD_Signal']
    histogram = latest['MACD_Histogram']

    print(f"  MACD: {macd:.4f}")
    print(f"  Signal: {signal:.4f}")
    print(f"  Histogram: {histogram:.4f}")

    # MACD Histogram = MACD - Signal 확인
    calculated_histogram = macd - signal
    if abs(histogram - calculated_histogram) < 0.0001:
        print(f"  ✓ MACD Histogram 계산 정확")
        validation_passed += 1
    else:
        print(f"  ✗ MACD Histogram 계산 오류")
        print(f"    예상: {calculated_histogram:.4f}, 실제: {histogram:.4f}")
        validation_failed += 1

    # MACD 신호 해석
    if macd > signal:
        print(f"  → 상승 신호 (MACD > Signal)")
    else:
        print(f"  → 하락 신호 (MACD < Signal)")

except KeyError as e:
    print(f"  ✗ MACD 컬럼 없음: {e}")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ MACD 검증 실패: {e}")
    validation_failed += 1

# 3. Bollinger Bands 검증
print(f"\n[3] Bollinger Bands 검증")
try:
    upper = latest['BB_Upper']
    middle = latest['BB_Middle']
    lower = latest['BB_Lower']
    close = latest['Close']

    print(f"  상단 밴드: {upper:,.0f}원")
    print(f"  중간 밴드: {middle:,.0f}원")
    print(f"  하단 밴드: {lower:,.0f}원")
    print(f"  현재 가격: {close:,.0f}원")

    # 밴드 순서 확인 (상단 > 중단 > 하단)
    if upper > middle > lower:
        print(f"  ✓ 밴드 순서 정상 (상단 > 중단 > 하단)")
        validation_passed += 1
    else:
        print(f"  ✗ 밴드 순서 비정상")
        validation_failed += 1

    # 가격 위치 확인
    bb_position = (float(close) - float(lower)) / (float(upper) - float(lower)) * 100
    print(f"  밴드 내 위치: {bb_position:.1f}%")

    if close > upper:
        print(f"  → 상단 밴드 돌파 (과매수 가능성)")
    elif close < lower:
        print(f"  → 하단 밴드 이탈 (과매도 가능성)")
    else:
        print(f"  → 밴드 내 정상 위치")

except KeyError as e:
    print(f"  ✗ Bollinger Bands 컬럼 없음: {e}")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ Bollinger Bands 검증 실패: {e}")
    validation_failed += 1

# 4. Stochastic 검증
print(f"\n[4] Stochastic Oscillator 검증")
try:
    stoch_k = latest['Stoch_K']
    stoch_d = latest['Stoch_D']

    print(f"  %K: {stoch_k:.2f}")
    print(f"  %D: {stoch_d:.2f}")

    if 0 <= stoch_k <= 100 and 0 <= stoch_d <= 100:
        print(f"  ✓ Stochastic 유효 범위 (0-100)")
        validation_passed += 1
    else:
        print(f"  ✗ Stochastic 범위 벗어남")
        validation_failed += 1

    # Stochastic 해석
    if stoch_k >= 80:
        print(f"  → 과매수 구간 (%K >= 80)")
    elif stoch_k <= 20:
        print(f"  → 과매도 구간 (%K <= 20)")
    else:
        print(f"  → 중립 구간 (20 < %K < 80)")

except KeyError as e:
    print(f"  ✗ Stochastic 컬럼 없음: {e}")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ Stochastic 검증 실패: {e}")
    validation_failed += 1

# 5. ATR 검증
print(f"\n[5] ATR (Average True Range) 검증")
try:
    atr = latest['ATR']
    close = latest['Close']

    print(f"  ATR: {atr:,.0f}원")
    print(f"  ATR/Close 비율: {(float(atr)/float(close)*100):.2f}%")

    if atr > 0:
        print(f"  ✓ ATR 양수 확인")
        validation_passed += 1
    else:
        print(f"  ✗ ATR 비정상: {atr}")
        validation_failed += 1

    # 변동성 해석
    volatility_pct = (float(atr) / float(close)) * 100
    if volatility_pct > 3:
        print(f"  → 높은 변동성 (>3%)")
    elif volatility_pct < 1:
        print(f"  → 낮은 변동성 (<1%)")
    else:
        print(f"  → 보통 변동성 (1-3%)")

except KeyError:
    print(f"  ✗ ATR 컬럼 없음")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ ATR 검증 실패: {e}")
    validation_failed += 1

# 6. OBV 검증
print(f"\n[6] OBV (On-Balance Volume) 검증")
try:
    obv = latest['OBV']

    print(f"  OBV: {obv:,.0f}")

    # OBV 추세 확인 (최근 5일)
    recent_obv = df_with_indicators['OBV'].tail(5)
    obv_trend = recent_obv.iloc[-1] - recent_obv.iloc[0]

    if obv_trend > 0:
        print(f"  → 최근 5일 OBV 상승 추세 (+{obv_trend:,.0f})")
    elif obv_trend < 0:
        print(f"  → 최근 5일 OBV 하락 추세 ({obv_trend:,.0f})")
    else:
        print(f"  → 최근 5일 OBV 보합")

    print(f"  ✓ OBV 계산 완료")
    validation_passed += 1

except KeyError:
    print(f"  ✗ OBV 컬럼 없음")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ OBV 검증 실패: {e}")
    validation_failed += 1

# 7. SMA/EMA 검증
print(f"\n[7] 이동평균선 검증")
try:
    sma_5 = latest['SMA_5']
    sma_20 = latest['SMA_20']
    sma_60 = latest['SMA_60']
    close = latest['Close']

    print(f"  SMA_5:  {sma_5:,.0f}원")
    print(f"  SMA_20: {sma_20:,.0f}원")
    print(f"  SMA_60: {sma_60:,.0f}원")
    print(f"  현재가: {close:,.0f}원")

    # 골든크로스/데드크로스 확인
    if sma_5 > sma_20 > sma_60:
        print(f"  → 강한 상승 추세 (단기 > 중기 > 장기)")
    elif sma_5 < sma_20 < sma_60:
        print(f"  → 강한 하락 추세 (단기 < 중기 < 장기)")
    else:
        print(f"  → 혼조세")

    print(f"  ✓ 이동평균선 계산 완료")
    validation_passed += 1

except KeyError as e:
    print(f"  ✗ 이동평균선 컬럼 없음: {e}")
    validation_failed += 1
except Exception as e:
    print(f"  ✗ 이동평균선 검증 실패: {e}")
    validation_failed += 1

# 최종 결과
print("\n" + "=" * 70)
print(f"검증 결과: 성공 {validation_passed}개, 실패 {validation_failed}개")

if validation_failed == 0:
    print("✅ 테스트 2.2 완료! (모든 지표 검증 통과)")
else:
    print(f"⚠ 테스트 2.2 완료 (일부 실패: {validation_failed}개)")

print("=" * 70)
