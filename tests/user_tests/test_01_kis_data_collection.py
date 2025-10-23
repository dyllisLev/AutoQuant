"""
테스트 1.1: PostgreSQL 데이터 조회 (KIS 시스템)
USER_TEST_CHECKLIST.md의 1.1 섹션 테스트
"""

from src.database.database import Database
from datetime import datetime, timedelta

print("=" * 70)
print("테스트 1.1: PostgreSQL 데이터 조회 (KIS 시스템)")
print("=" * 70)

# Database 인스턴스 생성
try:
    db = Database()
    print("✓ Database 인스턴스 생성 성공")
except Exception as e:
    print(f"✗ Database 인스턴스 생성 실패: {e}")
    exit(1)

# 1. 사용 가능한 종목 조회
print("\n[테스트 1] 사용 가능한 종목 조회")
print("-" * 70)

try:
    symbols_df = db.get_available_symbols_from_kis()

    # 테스트 항목 검증
    print(f"✓ PostgreSQL 연결 성공")
    print(f"✓ 총 종목 수: {len(symbols_df)}")

    # 4,359개 종목 확인
    if len(symbols_df) == 4359:
        print(f"✓ 예상 종목 수(4,359개) 일치")
    else:
        print(f"⚠ 종목 수가 예상과 다름 (예상: 4,359, 실제: {len(symbols_df)})")

    # 컬럼 확인
    print(f"\n컬럼 목록: {list(symbols_df.columns)}")

    # 상위 10개 종목 출력
    print(f"\n상위 10개 종목:")
    print(symbols_df.head(10).to_string())

    # 최신 업데이트 날짜 확인
    if 'last_trade_date' in symbols_df.columns:
        print(f"\n✓ 최신 거래일: {symbols_df['last_trade_date'].max()}")

    # 데이터 카운트 통계
    if 'data_count' in symbols_df.columns:
        print(f"✓ 평균 데이터 건수: {symbols_df['data_count'].mean():.0f}")
        print(f"✓ 최소 데이터 건수: {symbols_df['data_count'].min()}")
        print(f"✓ 최대 데이터 건수: {symbols_df['data_count'].max()}")

except Exception as e:
    print(f"✗ 종목 조회 실패: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("✅ 테스트 1.1 완료!")
print("=" * 70)
