#!/usr/bin/env python3
"""
디버깅 테스트 2 - 올바른 날짜로 테스트
"""

from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd

print("=" * 60)
print("pykrx API 테스트 (2025년 데이터)")
print("=" * 60)

# 올바른 날짜 설정
today = datetime.now()
print(f"\n현재 날짜: {today.strftime('%Y-%m-%d')}")

# 최근 30일 데이터
start_str = (today - timedelta(days=30)).strftime('%Y%m%d')
end_str = today.strftime('%Y%m%d')

print(f"기간: {start_str} ~ {end_str}")

# 1. 주가 데이터 테스트
print("\n1. 삼성전자 주가 데이터 조회...")
try:
    df = stock.get_market_ohlcv_by_date(start_str, end_str, "005930")
    print(f"   데이터 수: {len(df)}")
    if len(df) > 0:
        print(f"   컬럼: {df.columns.tolist()}")
        print("\n   최근 3일 데이터:")
        print(df.tail(3))
    else:
        print("   ⚠ 데이터가 비어있습니다 (휴장일이거나 연결 문제)")
except Exception as e:
    print(f"   오류: {e}")
    import traceback
    traceback.print_exc()

# 2. 더 과거 데이터로 테스트 (2024년)
print("\n2. 2024년 데이터로 테스트...")
try:
    df = stock.get_market_ohlcv_by_date("20240901", "20240930", "005930")
    print(f"   데이터 수: {len(df)}")
    if len(df) > 0:
        print(f"   컬럼: {df.columns.tolist()}")
        print("\n   9월 마지막 3일 데이터:")
        print(df.tail(3))
except Exception as e:
    print(f"   오류: {e}")

# 3. 종목 리스트 조회
print("\n3. KOSPI 종목 리스트 조회...")
try:
    tickers = stock.get_market_ticker_list(market="KOSPI")
    print(f"   종목 수: {len(tickers)}")
    if len(tickers) > 0:
        print(f"   상위 10개: {tickers[:10]}")
except Exception as e:
    print(f"   오류: {e}")

# 4. FinanceDataReader로 테스트
print("\n4. FinanceDataReader 테스트...")
try:
    import FinanceDataReader as fdr
    df_fdr = fdr.DataReader('005930', '2024-09-01', '2024-09-30')
    print(f"   데이터 수: {len(df_fdr)}")
    if len(df_fdr) > 0:
        print(f"   컬럼: {df_fdr.columns.tolist()}")
        print("\n   최근 3일 데이터:")
        print(df_fdr.tail(3))
except Exception as e:
    print(f"   오류: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("네트워크 연결 테스트")
print("=" * 60)

# 5. 인터넷 연결 테스트
print("\n5. 인터넷 연결 확인...")
try:
    import requests
    response = requests.get("https://www.google.com", timeout=5)
    print(f"   ✓ 인터넷 연결 정상 (상태코드: {response.status_code})")
except Exception as e:
    print(f"   ✗ 인터넷 연결 문제: {e}")

print("\n" + "=" * 60)
