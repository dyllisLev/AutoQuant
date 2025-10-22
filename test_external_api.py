#!/usr/bin/env python3
"""
외부 API를 이용한 실제 데이터 수집 테스트
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("외부 API 데이터 수집 테스트")
print("=" * 80)
print()

# 1. pykrx 테스트
print("1. pykrx 라이브러리 테스트")
print("-" * 80)
try:
    from pykrx import stock
    print("✓ pykrx 임포트 성공")

    # 최근 영업일 기준으로 삼성전자 주가 조회 시도
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    print(f"  테스트 기간: {start_date} ~ {end_date}")
    print(f"  테스트 종목: 005930 (삼성전자)")
    print("  데이터 수집 시도 중...")

    df = stock.get_market_ohlcv_by_date(start_date, end_date, "005930")

    if df is not None and not df.empty:
        print(f"✓ 데이터 수집 성공: {len(df)} 건")
        print("\n최근 데이터:")
        print(df.tail(3))
    else:
        print("✗ 데이터가 비어있습니다")

except ImportError as e:
    print(f"✗ pykrx 임포트 실패: {e}")
except Exception as e:
    print(f"✗ pykrx 데이터 수집 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 2. FinanceDataReader 테스트
print("2. FinanceDataReader 라이브러리 테스트")
print("-" * 80)
try:
    import FinanceDataReader as fdr
    print("✓ FinanceDataReader 임포트 성공")

    # 최근 7일간 삼성전자 데이터 조회
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    print(f"  테스트 기간: {start_date.date()} ~ {end_date.date()}")
    print(f"  테스트 종목: 005930 (삼성전자)")
    print("  데이터 수집 시도 중...")

    df = fdr.DataReader("005930", start_date, end_date)

    if df is not None and not df.empty:
        print(f"✓ 데이터 수집 성공: {len(df)} 건")
        print("\n최근 데이터:")
        print(df.tail(3))
    else:
        print("✗ 데이터가 비어있습니다")

except ImportError as e:
    print(f"✗ FinanceDataReader 임포트 실패: {e}")
except Exception as e:
    print(f"✗ FinanceDataReader 데이터 수집 실패: {e}")
    import traceback
    traceback.print_exc()

print()

# 3. StockDataCollector 클래스 테스트
print("3. StockDataCollector 클래스 테스트")
print("-" * 80)
try:
    from src.data_collection.stock_collector import StockDataCollector
    print("✓ StockDataCollector 임포트 성공")

    collector = StockDataCollector()
    print("  데이터 수집 시도 중 (최근 7일)...")

    df = collector.collect("005930", days=7)

    if df is not None and not df.empty:
        print(f"✓ 데이터 수집 성공: {len(df)} 건")
        print("\n최근 데이터:")
        print(df.tail(3))
    else:
        print("✗ 데이터가 비어있습니다")

except ImportError as e:
    print(f"✗ StockDataCollector 임포트 실패: {e}")
except Exception as e:
    print(f"✗ StockDataCollector 데이터 수집 실패: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("테스트 완료")
print("=" * 80)
