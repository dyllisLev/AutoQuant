#!/usr/bin/env python3
"""
빠른 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("AutoQuant 데이터 수집 테스트")
print("=" * 60)

# 1. 패키지 import 테스트
print("\n1. 패키지 import 테스트...")
try:
    import pykrx
    print("   ✓ pykrx 로드 성공")
except ImportError as e:
    print(f"   ✗ pykrx 로드 실패: {e}")

try:
    import FinanceDataReader as fdr
    print("   ✓ FinanceDataReader 로드 성공")
except ImportError as e:
    print(f"   ✗ FinanceDataReader 로드 실패: {e}")

try:
    import pandas as pd
    print("   ✓ pandas 로드 성공")
except ImportError as e:
    print(f"   ✗ pandas 로드 실패: {e}")

# 2. 모듈 import 테스트
print("\n2. AutoQuant 모듈 import 테스트...")
try:
    from src.data_collection import StockDataCollector, MarketDataCollector
    print("   ✓ 데이터 수집 모듈 로드 성공")
except Exception as e:
    print(f"   ✗ 모듈 로드 실패: {e}")
    sys.exit(1)

# 3. 주가 데이터 수집 테스트
print("\n3. 삼성전자(005930) 주가 데이터 수집 테스트...")
try:
    collector = StockDataCollector()
    df = collector.collect(ticker='005930', days=5)

    if df is not None and not df.empty:
        print(f"   ✓ 데이터 수집 성공: {len(df)} 건")
        print(f"\n   최근 데이터:")
        print(df.tail(3).to_string())
    else:
        print("   ✗ 데이터가 비어있습니다")
except Exception as e:
    print(f"   ✗ 수집 실패: {e}")
    import traceback
    traceback.print_exc()

# 4. 현재가 조회 테스트
print("\n4. 현재가 조회 테스트...")
try:
    collector = StockDataCollector()
    price = collector.get_current_price('005930')

    if price:
        print(f"   ✓ 삼성전자 현재가: {price:,.0f}원")
    else:
        print("   ℹ 현재가 조회 불가 (휴장일이거나 시간 외)")
except Exception as e:
    print(f"   ✗ 현재가 조회 실패: {e}")

# 5. 시장 데이터 테스트
print("\n5. KOSPI 상위 5개 종목 조회 테스트...")
try:
    market_collector = MarketDataCollector()
    top_5 = market_collector.get_top_stocks(market='KOSPI', top_n=5)

    if top_5:
        print(f"   ✓ 상위 종목 조회 성공:")
        for i, ticker in enumerate(top_5, 1):
            name = market_collector.get_ticker_name(ticker)
            print(f"      {i}. {name} ({ticker})")
    else:
        print("   ✗ 종목 조회 실패")
except Exception as e:
    print(f"   ✗ 시장 데이터 조회 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
