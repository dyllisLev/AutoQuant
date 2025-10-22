"""
AutoQuant 기본 사용 예제
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection import (
    StockDataCollector,
    MarketDataCollector,
    FinancialDataCollector
)
from src.data_collection.data_manager import DataCollectionManager


def example_1_collect_single_stock():
    """예제 1: 단일 종목 데이터 수집"""
    print("=" * 60)
    print("예제 1: 삼성전자 주가 데이터 수집")
    print("=" * 60)

    collector = StockDataCollector()

    # 삼성전자 (005930) 최근 30일 데이터 수집
    df = collector.collect(ticker='005930', days=30)

    if df is not None and not df.empty:
        print(f"\n수집된 데이터: {len(df)} 건")
        print("\n최근 5일 데이터:")
        print(df.tail())

        # 현재가 조회
        current_price = collector.get_current_price('005930')
        if current_price:
            print(f"\n삼성전자 현재가: {current_price:,.0f}원")
    else:
        print("데이터 수집 실패")


def example_2_collect_multiple_stocks():
    """예제 2: 여러 종목 데이터 수집"""
    print("\n" + "=" * 60)
    print("예제 2: 여러 종목 데이터 수집")
    print("=" * 60)

    collector = StockDataCollector()

    # 주요 종목 리스트
    tickers = {
        '005930': '삼성전자',
        '000660': 'SK하이닉스',
        '035420': 'NAVER',
        '035720': '카카오'
    }

    print(f"\n{len(tickers)}개 종목 수집 중...")

    data = collector.collect_multiple(
        tickers=list(tickers.keys()),
        days=30
    )

    print(f"\n수집 완료: {len(data)}개 종목")

    for ticker, df in data.items():
        name = tickers.get(ticker, ticker)
        if not df.empty:
            latest_price = df.iloc[-1]['Close']
            print(f"- {name} ({ticker}): {latest_price:,.0f}원, {len(df)} 건")


def example_3_market_data():
    """예제 3: 시장 데이터 수집"""
    print("\n" + "=" * 60)
    print("예제 3: KOSPI 시장 데이터 수집")
    print("=" * 60)

    collector = MarketDataCollector()

    # KOSPI 전체 종목 조회
    tickers = collector.get_ticker_list(market='KOSPI')
    print(f"\nKOSPI 전체 종목 수: {len(tickers)}")

    # 시가총액 상위 10개 종목
    top_10 = collector.get_top_stocks(market='KOSPI', top_n=10)
    print(f"\n시가총액 상위 10개 종목:")

    for i, ticker in enumerate(top_10[:10], 1):
        name = collector.get_ticker_name(ticker)
        print(f"{i:2d}. {name} ({ticker})")


def example_4_fundamental_data():
    """예제 4: 재무 데이터 수집"""
    print("\n" + "=" * 60)
    print("예제 4: 재무 데이터 수집")
    print("=" * 60)

    collector = FinancialDataCollector()

    # 삼성전자 기본적 지표
    ticker = '005930'
    fundamental = collector.get_fundamental_data(ticker)

    if fundamental:
        print(f"\n삼성전자 기본적 분석 지표:")
        print(f"- PER (주가수익비율): {fundamental.get('PER', 'N/A')}")
        print(f"- PBR (주가순자산비율): {fundamental.get('PBR', 'N/A')}")
        print(f"- EPS (주당순이익): {fundamental.get('EPS', 'N/A')}")
        print(f"- BPS (주당순자산): {fundamental.get('BPS', 'N/A')}")
        print(f"- DIV (배당수익률): {fundamental.get('DIV', 'N/A')}")


def example_5_comprehensive_collection():
    """예제 5: 종합 데이터 수집"""
    print("\n" + "=" * 60)
    print("예제 5: 종합 데이터 수집 (DataCollectionManager)")
    print("=" * 60)

    manager = DataCollectionManager()

    # KOSPI 상위 20개 종목 데이터 수집
    print("\nKOSPI 상위 20개 종목 데이터 수집 중...")

    result = manager.collect_daily_data(
        market='KOSPI',
        top_n=20
    )

    if result:
        print("\n수집 결과:")
        if 'stock_data' in result:
            print(f"- 주가 데이터: {len(result['stock_data'])}개 종목")
        if 'market_data' in result:
            print(f"- 시장 데이터: {len(result['market_data'])}개 종목")
        if 'financial_data' in result:
            print(f"- 재무 데이터: {len(result['financial_data'])}개 종목")


def example_6_ticker_info():
    """예제 6: 종목 정보 조회"""
    print("\n" + "=" * 60)
    print("예제 6: 종목 상세 정보 조회")
    print("=" * 60)

    manager = DataCollectionManager()

    tickers = ['005930', '000660', '035420']

    for ticker in tickers:
        info = manager.get_ticker_info(ticker)

        if info:
            print(f"\n종목코드: {ticker}")
            print(f"종목명: {info.get('name', 'N/A')}")
            print(f"현재가: {info.get('current_price', 'N/A'):,.0f}원" if info.get('current_price') else "현재가: N/A")

            if 'PER' in info:
                print(f"PER: {info['PER']}")
            if 'PBR' in info:
                print(f"PBR: {info['PBR']}")


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("AutoQuant 기본 사용 예제")
    print("=" * 60)

    # 모든 예제 실행
    try:
        example_1_collect_single_stock()
        example_2_collect_multiple_stocks()
        example_3_market_data()
        example_4_fundamental_data()
        # example_5_comprehensive_collection()  # 시간이 오래 걸릴 수 있음
        example_6_ticker_info()

        print("\n" + "=" * 60)
        print("모든 예제 실행 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
