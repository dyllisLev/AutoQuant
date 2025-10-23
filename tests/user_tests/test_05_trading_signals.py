"""
테스트 2.3: 매매 신호 생성
USER_TEST_CHECKLIST.md의 2.3 섹션 테스트
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
print("테스트 2.3: 매매 신호 생성")
print("=" * 70)

# Database 인스턴스 생성
db = Database()

# 삼성전자(005930) 최근 200일 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

print(f"\n[데이터 조회 및 지표 계산]")
print(f"종목: {symbol} (삼성전자)")
print(f"조회 기간: {start_date} ~ {end_date}")
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

    # 모든 기술적 지표 계산
    df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

    print(f"✓ 데이터 조회 성공: {len(df_with_indicators)}건")
    print(f"✓ 기술적 지표 계산 완료")

except Exception as e:
    print(f"✗ 데이터 준비 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"\n[매매 신호 생성]")
print("-" * 70)

try:
    # 매매 신호 생성
    df_with_signals = TechnicalIndicators.get_trading_signals(df_with_indicators)

    # 추가된 신호 컬럼 확인
    signal_columns = [col for col in df_with_signals.columns
                     if col not in df_with_indicators.columns]

    print(f"✓ 매매 신호 생성 완료")
    print(f"✓ 추가된 신호 컬럼: {len(signal_columns)}개")

    print(f"\n[생성된 신호 목록]")
    for i, col in enumerate(signal_columns, 1):
        print(f"  {i}. {col}")

except Exception as e:
    print(f"✗ 매매 신호 생성 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"\n[신호 유효성 검증]")
print("-" * 70)

validation_passed = 0
validation_failed = 0

# 1. Golden Cross / Death Cross 검증
print("[1] Golden Cross / Death Cross 검증")
try:
    golden_cross_count = df_with_signals['Golden_Cross'].sum()
    death_cross_count = df_with_signals['Death_Cross'].sum()

    print(f"  Golden Cross 발생: {golden_cross_count}회")
    print(f"  Death Cross 발생: {death_cross_count}회")

    # 최근 발생 확인
    recent_golden = df_with_signals['Golden_Cross'].tail(20).sum()
    recent_death = df_with_signals['Death_Cross'].tail(20).sum()

    if recent_golden > 0:
        golden_dates = df_with_signals[df_with_signals['Golden_Cross']].tail(1).index
        print(f"  → 최근 Golden Cross: {golden_dates[0] if len(golden_dates) > 0 else 'None'}")

    if recent_death > 0:
        death_dates = df_with_signals[df_with_signals['Death_Cross']].tail(1).index
        print(f"  → 최근 Death Cross: {death_dates[0] if len(death_dates) > 0 else 'None'}")

    print(f"  ✓ Golden/Death Cross 검증 완료")
    validation_passed += 1

except Exception as e:
    print(f"  ✗ Golden/Death Cross 검증 실패: {e}")
    validation_failed += 1

# 2. RSI 과매수/과매도 검증
print(f"\n[2] RSI 과매수/과매도 검증")
try:
    oversold_count = df_with_signals['RSI_Oversold'].sum()
    overbought_count = df_with_signals['RSI_Overbought'].sum()

    print(f"  RSI 과매도(<30) 발생: {oversold_count}회")
    print(f"  RSI 과매수(>70) 발생: {overbought_count}회")

    # 현재 상태
    latest_rsi = df_with_signals['RSI_14'].iloc[-1]
    latest_oversold = df_with_signals['RSI_Oversold'].iloc[-1]
    latest_overbought = df_with_signals['RSI_Overbought'].iloc[-1]

    print(f"  현재 RSI: {latest_rsi:.2f}")
    if latest_oversold:
        print(f"  → 현재 과매도 상태 (매수 신호)")
    elif latest_overbought:
        print(f"  → 현재 과매수 상태 (매도 신호)")
    else:
        print(f"  → 현재 중립 구간")

    print(f"  ✓ RSI 신호 검증 완료")
    validation_passed += 1

except Exception as e:
    print(f"  ✗ RSI 신호 검증 실패: {e}")
    validation_failed += 1

# 3. MACD 크로스 검증
print(f"\n[3] MACD 크로스 검증")
try:
    macd_up_count = df_with_signals['MACD_Cross_Up'].sum()
    macd_down_count = df_with_signals['MACD_Cross_Down'].sum()

    print(f"  MACD 상승 크로스: {macd_up_count}회")
    print(f"  MACD 하락 크로스: {macd_down_count}회")

    # 최근 크로스 확인
    recent_up = df_with_signals['MACD_Cross_Up'].tail(20).sum()
    recent_down = df_with_signals['MACD_Cross_Down'].tail(20).sum()

    if recent_up > 0:
        up_dates = df_with_signals[df_with_signals['MACD_Cross_Up']].tail(1).index
        print(f"  → 최근 상승 크로스: {up_dates[0] if len(up_dates) > 0 else 'None'}")

    if recent_down > 0:
        down_dates = df_with_signals[df_with_signals['MACD_Cross_Down']].tail(1).index
        print(f"  → 최근 하락 크로스: {down_dates[0] if len(down_dates) > 0 else 'None'}")

    print(f"  ✓ MACD 크로스 검증 완료")
    validation_passed += 1

except Exception as e:
    print(f"  ✗ MACD 크로스 검증 실패: {e}")
    validation_failed += 1

# 4. Bollinger Bands 돌파 검증
print(f"\n[4] Bollinger Bands 돌파 검증")
try:
    bb_upper_break = df_with_signals['BB_Break_Upper'].sum()
    bb_lower_break = df_with_signals['BB_Break_Lower'].sum()

    print(f"  상단 밴드 돌파: {bb_upper_break}회")
    print(f"  하단 밴드 이탈: {bb_lower_break}회")

    # 현재 상태
    latest_upper_break = df_with_signals['BB_Break_Upper'].iloc[-1]
    latest_lower_break = df_with_signals['BB_Break_Lower'].iloc[-1]

    if latest_upper_break:
        print(f"  → 현재 상단 밴드 돌파 (과매수 경고)")
    elif latest_lower_break:
        print(f"  → 현재 하단 밴드 이탈 (과매도 경고)")
    else:
        print(f"  → 현재 밴드 내 정상 위치")

    print(f"  ✓ Bollinger Bands 돌파 검증 완료")
    validation_passed += 1

except Exception as e:
    print(f"  ✗ Bollinger Bands 돌파 검증 실패: {e}")
    validation_failed += 1

# 5. 최근 10일 신호 분석
print(f"\n[5] 최근 10일 신호 분석")
print("-" * 70)

try:
    recent_data = df_with_signals.tail(10)

    print(f"{'날짜':<12} {'종가':>10} {'Golden':>8} {'Death':>8} {'RSI<30':>8} {'RSI>70':>8} {'MACD↑':>8} {'MACD↓':>8}")
    print("-" * 70)

    for idx, row in recent_data.iterrows():
        date_str = idx.strftime('%Y-%m-%d')
        close = float(row['Close'])
        golden = '✓' if row['Golden_Cross'] else ''
        death = '✓' if row['Death_Cross'] else ''
        rsi_low = '✓' if row['RSI_Oversold'] else ''
        rsi_high = '✓' if row['RSI_Overbought'] else ''
        macd_up = '✓' if row['MACD_Cross_Up'] else ''
        macd_down = '✓' if row['MACD_Cross_Down'] else ''

        print(f"{date_str:<12} {close:>10,.0f} {golden:>8} {death:>8} {rsi_low:>8} {rsi_high:>8} {macd_up:>8} {macd_down:>8}")

    print(f"\n✓ 최근 10일 신호 분석 완료")
    validation_passed += 1

except Exception as e:
    print(f"✗ 최근 신호 분석 실패: {e}")
    import traceback
    traceback.print_exc()
    validation_failed += 1

# 최종 결과
print("\n" + "=" * 70)
print(f"검증 결과: 성공 {validation_passed}개, 실패 {validation_failed}개")

if validation_failed == 0:
    print("✅ 테스트 2.3 완료! (모든 신호 검증 통과)")
else:
    print(f"⚠ 테스트 2.3 완료 (일부 실패: {validation_failed}개)")

print("=" * 70)
