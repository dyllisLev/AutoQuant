#!/usr/bin/env python3
"""
실제 데이터 수집 작동 여부 최종 테스트
"""

from datetime import datetime, timedelta
from pykrx import stock
import pandas as pd

print("=" * 80)
print("실제 데이터 수집 최종 테스트")
print("=" * 80)
print()

# 1. 종목 리스트 조회
print("1. KOSPI 종목 리스트 조회")
print("-" * 80)

try:
    date = "20240101"
    tickers = stock.get_market_ticker_list(date, market="KOSPI")

    if tickers:
        print(f"✓ 성공: {len(tickers)}개 종목 조회")
        print(f"  상위 10개: {tickers[:10]}")

        # 삼성전자, SK하이닉스, LG전자 등 확인
        major_stocks = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '066570': 'LG전자',
            '005380': '현대차',
            '035720': '카카오',
        }

        print("\n  주요 종목 포함 여부:")
        for code, name in major_stocks.items():
            if code in tickers:
                print(f"    ✓ {code} ({name})")
            else:
                print(f"    ✗ {code} ({name}) - 리스트에 없음")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 2. 시장 전체 데이터 조회
print("2. 시장 전체 OHLCV 데이터 조회")
print("-" * 80)

try:
    date = "20240105"  # 2024년 1월 5일 (거래일)
    print(f"  조회 날짜: {date}")

    # 전체 시장 데이터 조회
    df = stock.get_market_ohlcv_by_date("20240105", "20240105", "005930")

    if df is not None and not df.empty:
        print(f"✓ 성공: 데이터 수집")
        print(f"\n{df}")
    else:
        # 다른 날짜로 시도
        print(f"  {date}에 데이터 없음, 다른 날짜 시도...")

        for day_offset in range(1, 10):
            test_date = f"202401{day_offset:02d}"
            print(f"\n  시도: {test_date}")

            df = stock.get_market_ohlcv_by_date(test_date, test_date, "005930")

            if df is not None and not df.empty:
                print(f"  ✓ 성공: {test_date}에 {len(df)} 건 데이터")
                print(df)
                break
        else:
            print("  ✗ 모든 날짜에서 데이터 조회 실패")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 3. 시장 전체 시가총액 조회
print("3. 시장 시가총액 데이터 조회")
print("-" * 80)

try:
    date = "20240105"
    print(f"  조회 날짜: {date}")

    df = stock.get_market_cap_by_date("20240101", "20240110", "005930")

    if df is not None and not df.empty:
        print(f"✓ 성공: {len(df)} 건")
        print(df)
    else:
        print("✗ 데이터 없음")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. 최근 날짜로 시도 (2024년 실제 거래일)
print("4. 최근 거래일 데이터 조회")
print("-" * 80)

try:
    # 2024년 12월 최근 거래일로 시도
    recent_dates = [
        ("20241220", "20241220"),
        ("20241213", "20241213"),
        ("20241206", "20241206"),
        ("20241129", "20241129"),
    ]

    for start, end in recent_dates:
        print(f"\n  시도: {start} ~ {end}")

        df = stock.get_market_ohlcv_by_date(start, end, "005930")

        if df is not None and not df.empty:
            print(f"  ✓ 성공: {len(df)} 건")
            print(df)
            break
        else:
            print(f"  - 데이터 없음")
    else:
        print("\n  모든 최근 날짜에서 데이터 없음")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 5. 전체 시장 일별 데이터 조회 (종목별이 아닌)
print("5. 전체 KOSPI 시장 일별 데이터")
print("-" * 80)

try:
    date = "20240105"
    print(f"  조회 날짜: {date}")

    # 전체 시장 지수
    df = stock.get_index_ohlcv_by_date("20240101", "20240110", "1001")  # KOSPI

    if df is not None and not df.empty:
        print(f"✓ 성공: KOSPI 지수 데이터 {len(df)} 건")
        print(df)
    else:
        print("✗ 데이터 없음")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 6. 전체 종목 일별 거래 데이터
print("6. 특정일 전체 종목 거래 데이터")
print("-" * 80)

try:
    date = "20240105"
    print(f"  조회 날짜: {date}")

    # 특정일의 전체 종목 데이터
    df = stock.get_market_ohlcv_by_ticker(date, market="KOSPI")

    if df is not None and not df.empty:
        print(f"✓ 성공: {len(df)} 개 종목 데이터")
        print(f"\n상위 5개 종목:")
        print(df.head())

        # 삼성전자 데이터 확인
        if '005930' in df.index:
            print(f"\n삼성전자 데이터:")
            print(df.loc['005930'])
        else:
            print("\n삼성전자 데이터 없음")
    else:
        print("✗ 데이터 없음")

except Exception as e:
    print(f"✗ 실패: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("테스트 완료")
print("=" * 80)
