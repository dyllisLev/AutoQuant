"""
테스트 2.1: 기술적 지표 계산 (전체)
USER_TEST_CHECKLIST.md의 2.1 섹션 테스트
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
print("테스트 2.1: 기술적 지표 계산 (전체)")
print("=" * 70)

# Database 인스턴스 생성
db = Database()

# 삼성전자(005930) 최근 200일 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=200)

print(f"\n[데이터 조회] {symbol} (삼성전자)")
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

    print(f"✓ 데이터 조회 성공: {len(ohlcv_df)}건")
    print(f"✓ 기본 컬럼: {list(ohlcv_df.columns)}")
except Exception as e:
    print(f"✗ 데이터 조회 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"\n[기술적 지표 계산]")
print("-" * 70)

try:
    # 모든 기술적 지표 계산
    df_with_indicators = TechnicalIndicators.add_all_indicators(ohlcv_df)

    # 결과 통계
    original_columns = len(ohlcv_df.columns)
    new_columns = len(df_with_indicators.columns)
    added_columns = new_columns - original_columns

    print(f"✓ 기술적 지표 계산 완료")
    print(f"✓ 추가된 컬럼: {added_columns}개")
    print(f"✓ 총 컬럼: {new_columns}개")

    # 추가된 지표 컬럼 목록
    added_indicator_columns = [col for col in df_with_indicators.columns
                               if col not in ohlcv_df.columns]

    print(f"\n[추가된 지표 목록]")
    for i, col in enumerate(added_indicator_columns, 1):
        print(f"  {i:2d}. {col}")

    # 개별 지표 확인
    print(f"\n[개별 지표 확인]")

    # SMA 확인
    sma_cols = [col for col in added_indicator_columns if 'SMA' in col]
    if sma_cols:
        print(f"✓ SMA 계산 완료: {sma_cols}")
    else:
        print(f"⚠ SMA 컬럼 없음")

    # EMA 확인
    ema_cols = [col for col in added_indicator_columns if 'EMA' in col]
    if ema_cols:
        print(f"✓ EMA 계산 완료: {ema_cols}")
    else:
        print(f"⚠ EMA 컬럼 없음")

    # RSI 확인
    rsi_cols = [col for col in added_indicator_columns if 'RSI' in col]
    if rsi_cols:
        print(f"✓ RSI 계산 완료: {rsi_cols}")
    else:
        print(f"⚠ RSI 컬럼 없음")

    # MACD 확인
    macd_cols = [col for col in added_indicator_columns if 'MACD' in col]
    if macd_cols:
        print(f"✓ MACD 계산 완료: {macd_cols}")
    else:
        print(f"⚠ MACD 컬럼 없음")

    # Bollinger Bands 확인
    bb_cols = [col for col in added_indicator_columns if 'BB_' in col]
    if bb_cols:
        print(f"✓ Bollinger Bands 계산 완료: {bb_cols}")
    else:
        print(f"⚠ Bollinger Bands 컬럼 없음")

    # Stochastic 확인
    stoch_cols = [col for col in added_indicator_columns if 'Stoch' in col]
    if stoch_cols:
        print(f"✓ Stochastic 계산 완료: {stoch_cols}")
    else:
        print(f"⚠ Stochastic 컬럼 없음")

    # ATR 확인
    atr_cols = [col for col in added_indicator_columns if 'ATR' in col]
    if atr_cols:
        print(f"✓ ATR 계산 완료: {atr_cols}")
    else:
        print(f"⚠ ATR 컬럼 없음")

    # OBV 확인
    obv_cols = [col for col in added_indicator_columns if 'OBV' in col]
    if obv_cols:
        print(f"✓ OBV 계산 완료: {obv_cols}")
    else:
        print(f"⚠ OBV 컬럼 없음")

    # NaN 값 확인
    print(f"\n[데이터 품질 검증]")
    nan_counts = df_with_indicators.isnull().sum()

    # 초기 데이터는 NaN이 있을 수 있음 (이동평균 계산 시)
    total_nan = nan_counts.sum()
    if total_nan > 0:
        print(f"⚠ NaN 값 발견: 총 {total_nan}개")
        print(f"  (지표 계산 초기값은 NaN이 정상입니다)")

        # 마지막 5개 행의 NaN 확인
        recent_nan = df_with_indicators.tail(5).isnull().sum().sum()
        if recent_nan == 0:
            print(f"✓ 최근 5개 행: NaN 없음 (정상)")
        else:
            print(f"⚠ 최근 5개 행에도 NaN 존재: {recent_nan}개")
    else:
        print(f"✓ NaN 값 없음")

    # 최근 5일 데이터 출력
    print(f"\n[최근 5일 데이터 샘플]")
    print(df_with_indicators.tail(5).to_string())

except Exception as e:
    print(f"✗ 기술적 지표 계산 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("✅ 테스트 2.1 완료!")
print("=" * 70)
