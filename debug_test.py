#!/usr/bin/env python3
"""
디버깅 테스트 - pykrx API 직접 테스트
"""

from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd

print("=" * 60)
print("pykrx API 직접 테스트")
print("=" * 60)

# 날짜 설정 - 최근 거래일
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# 거래일을 고려하여 더 이전 날짜 사용
start_str = "20241001"
end_str = "20241022"

print(f"\n기간: {start_str} ~ {end_str}")

# 1. 주가 데이터 테스트
print("\n1. 삼성전자 주가 데이터 조회...")
try:
    df = stock.get_market_ohlcv_by_date(start_str, end_str, "005930")
    print(f"   데이터 수: {len(df)}")
    print(f"   컬럼: {df.columns.tolist()}")
    if not df.empty:
        print("\n   최근 3일 데이터:")
        print(df.tail(3))
except Exception as e:
    print(f"   오류: {e}")

# 2. 시장 데이터 테스트
print("\n2. KOSPI 시가총액 데이터 조회...")
try:
    df_market = stock.get_market_cap_by_ticker("20241021", market="KOSPI")
    print(f"   종목 수: {len(df_market)}")
    print(f"   컬럼: {df_market.columns.tolist()}")
    if not df_market.empty:
        print("\n   상위 5개:")
        print(df_market.head(5))
except Exception as e:
    print(f"   오류: {e}")

# 3. 종목 리스트 조회
print("\n3. KOSPI 종목 리스트 조회...")
try:
    tickers = stock.get_market_ticker_list(market="KOSPI")
    print(f"   종목 수: {len(tickers)}")
    print(f"   상위 10개: {tickers[:10]}")
except Exception as e:
    print(f"   오류: {e}")

# 4. 종목명 조회
print("\n4. 종목명 조회...")
try:
    name = stock.get_market_ticker_name("005930")
    print(f"   005930: {name}")
except Exception as e:
    print(f"   오류: {e}")

print("\n" + "=" * 60)
