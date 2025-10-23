"""
테스트 1.2: 특정 종목 일봉 데이터 조회
USER_TEST_CHECKLIST.md의 1.2 섹션 테스트
"""

from src.database.database import Database
from datetime import datetime, timedelta

print("=" * 70)
print("테스트 1.2: 특정 종목 일봉 데이터 조회")
print("=" * 70)

# Database 인스턴스 생성
db = Database()

# 삼성전자(005930) 최근 100일 데이터 조회
symbol = "005930"
end_date = datetime.now().date()
start_date = end_date - timedelta(days=100)

print(f"\n[테스트 2] {symbol} (삼성전자) 일봉 데이터 조회")
print(f"조회 기간: {start_date} ~ {end_date}")
print("-" * 70)

try:
    ohlcv_df = db.get_daily_ohlcv_from_kis(symbol, start_date, end_date)

    # 테스트 항목 검증
    print(f"✓ 종목코드로 데이터 조회 성공")
    print(f"✓ 데이터 건수: {len(ohlcv_df)}")

    # 기간 확인
    actual_start = ohlcv_df.index.min()
    actual_end = ohlcv_df.index.max()
    print(f"✓ 실제 기간: {actual_start} ~ {actual_end}")

    # OHLCV 컬럼 확인
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in ohlcv_df.columns]

    if not missing_columns:
        print(f"✓ OHLCV 컬럼 모두 존재")
    else:
        print(f"✗ 누락된 컬럼: {missing_columns}")

    # 전체 컬럼 출력
    print(f"\n전체 컬럼: {list(ohlcv_df.columns)}")

    # 거래량, 거래대금 확인
    if 'volume' in ohlcv_df.columns:
        print(f"✓ 평균 거래량: {ohlcv_df['volume'].mean():,.0f}")

    if 'amount' in ohlcv_df.columns:
        print(f"✓ 평균 거래대금: {ohlcv_df['amount'].mean():,.0f}원")

    # 데이터 정렬 순서 확인 (오래된 → 최신)
    if len(ohlcv_df) > 1:
        is_sorted = ohlcv_df.index.is_monotonic_increasing
        if is_sorted:
            print(f"✓ 데이터 정렬: 오래된 → 최신 (정상)")
        else:
            print(f"⚠ 데이터 정렬: 비정상 (정렬 필요)")

    # 최근 5일 데이터 출력
    print(f"\n최근 5일 데이터:")
    print(ohlcv_df.tail(5).to_string())

    # 데이터 품질 검증
    print(f"\n[데이터 품질 검증]")
    null_counts = ohlcv_df.isnull().sum()
    if null_counts.sum() == 0:
        print(f"✓ 결측치 없음")
    else:
        print(f"⚠ 결측치 발견:")
        print(null_counts[null_counts > 0])

    # 가격 유효성 검증
    if (ohlcv_df['high'] >= ohlcv_df['low']).all():
        print(f"✓ 가격 유효성: 고가 >= 저가")
    else:
        print(f"✗ 가격 유효성: 고가 < 저가인 데이터 존재")

    if ((ohlcv_df['high'] >= ohlcv_df['open']) &
        (ohlcv_df['high'] >= ohlcv_df['close']) &
        (ohlcv_df['low'] <= ohlcv_df['open']) &
        (ohlcv_df['low'] <= ohlcv_df['close'])).all():
        print(f"✓ 가격 유효성: 고가/저가 범위 내 시가/종가")
    else:
        print(f"⚠ 가격 유효성: 범위 벗어난 데이터 존재")

except Exception as e:
    print(f"✗ 데이터 조회 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("✅ 테스트 1.2 완료!")
print("=" * 70)
