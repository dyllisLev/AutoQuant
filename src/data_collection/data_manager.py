"""
데이터 수집 통합 매니저
"""

from typing import List, Dict, Optional
import pandas as pd
from loguru import logger
from datetime import datetime

from .stock_collector import StockDataCollector
from .market_collector import MarketDataCollector
from .financial_collector import FinancialDataCollector


class DataCollectionManager:
    """데이터 수집 통합 매니저"""

    def __init__(self):
        self.stock_collector = StockDataCollector()
        self.market_collector = MarketDataCollector()
        self.financial_collector = FinancialDataCollector()

    def collect_daily_data(
        self,
        tickers: Optional[List[str]] = None,
        market: str = 'KOSPI',
        top_n: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        일일 데이터 수집 (매일 실행될 메인 함수)

        Args:
            tickers: 종목코드 리스트 (None이면 상위 종목 자동 선택)
            market: 시장 구분
            top_n: 상위 n개 종목 (tickers가 None일 때)

        Returns:
            수집된 데이터 딕셔너리
        """
        logger.info("=" * 50)
        logger.info(f"일일 데이터 수집 시작: {datetime.now()}")
        logger.info("=" * 50)

        result = {}

        try:
            # 1. 종목 리스트 결정
            if tickers is None:
                logger.info(f"{market} 상위 {top_n}개 종목 자동 선택")
                tickers = self.market_collector.get_top_stocks(
                    market=market,
                    criterion='market_cap',
                    top_n=top_n
                )

            if not tickers:
                logger.error("종목 리스트가 비어있습니다")
                return result

            logger.info(f"총 {len(tickers)}개 종목 데이터 수집 예정")

            # 2. 주가 데이터 수집
            logger.info("주가 데이터 수집 중...")
            stock_data = self.stock_collector.collect_multiple(
                tickers=tickers,
                days=365  # 최근 1년 데이터
            )
            result['stock_data'] = stock_data
            logger.info(f"주가 데이터 수집 완료: {len(stock_data)}개 종목")

            # 3. 시장 데이터 수집
            logger.info("시장 데이터 수집 중...")
            market_data = self.market_collector.collect(market=market)
            result['market_data'] = market_data
            logger.info(f"시장 데이터 수집 완료: {len(market_data)}개 종목")

            # 4. 재무 데이터 수집 (주요 종목만)
            logger.info("재무 데이터 수집 중... (상위 20개)")
            financial_data = {}
            for ticker in tickers[:20]:  # 상위 20개만
                try:
                    fundamental = self.financial_collector.get_fundamental_data(ticker)
                    if fundamental:
                        financial_data[ticker] = fundamental
                except Exception as e:
                    logger.warning(f"재무 데이터 수집 실패: {ticker}, {str(e)}")
                    continue

            result['financial_data'] = financial_data
            logger.info(f"재무 데이터 수집 완료: {len(financial_data)}개 종목")

            # 5. 수집 통계
            self._print_collection_stats(result)

        except Exception as e:
            logger.error(f"일일 데이터 수집 중 오류 발생: {str(e)}")

        logger.info("=" * 50)
        logger.info(f"일일 데이터 수집 완료: {datetime.now()}")
        logger.info("=" * 50)

        return result

    def collect_stock_history(
        self,
        ticker: str,
        days: int = 365
    ) -> pd.DataFrame:
        """
        특정 종목의 과거 데이터 수집

        Args:
            ticker: 종목코드
            days: 과거 일수

        Returns:
            주가 히스토리 DataFrame
        """
        logger.info(f"종목 히스토리 수집: {ticker}, 최근 {days}일")

        try:
            df = self.stock_collector.collect(ticker=ticker, days=days)
            return df
        except Exception as e:
            logger.error(f"종목 히스토리 수집 실패: {str(e)}")
            return pd.DataFrame()

    def collect_market_overview(self, market: str = 'KOSPI') -> Dict:
        """
        시장 전체 개요 수집

        Args:
            market: 시장 구분

        Returns:
            시장 개요 딕셔너리
        """
        logger.info(f"{market} 시장 개요 수집")

        overview = {}

        try:
            # 전체 종목 수
            tickers = self.market_collector.get_ticker_list(market)
            overview['total_stocks'] = len(tickers)

            # 시가총액 데이터
            market_cap_df = self.market_collector.get_market_cap(market)
            if not market_cap_df.empty and '시가총액' in market_cap_df.columns:
                overview['total_market_cap'] = market_cap_df['시가총액'].sum()
                overview['avg_market_cap'] = market_cap_df['시가총액'].mean()

            # 상위 10개 종목
            top_10 = self.market_collector.get_top_stocks(market, top_n=10)
            overview['top_10_stocks'] = top_10

            logger.info(f"{market} 시장 개요 수집 완료")

        except Exception as e:
            logger.error(f"시장 개요 수집 실패: {str(e)}")

        return overview

    def update_stock_data(self, ticker: str) -> bool:
        """
        특정 종목 데이터 업데이트

        Args:
            ticker: 종목코드

        Returns:
            성공 여부
        """
        logger.info(f"종목 데이터 업데이트: {ticker}")

        try:
            # 최근 30일 데이터 수집
            stock_data = self.stock_collector.collect(ticker, days=30)

            if stock_data is not None and not stock_data.empty:
                # 여기서 데이터베이스에 저장하는 로직 추가 예정
                logger.info(f"종목 데이터 업데이트 완료: {ticker}")
                return True
            else:
                logger.warning(f"수집된 데이터가 없습니다: {ticker}")
                return False

        except Exception as e:
            logger.error(f"종목 데이터 업데이트 실패: {ticker}, {str(e)}")
            return False

    def _print_collection_stats(self, data: Dict):
        """수집 통계 출력"""
        logger.info("=" * 50)
        logger.info("데이터 수집 통계")
        logger.info("-" * 50)

        if 'stock_data' in data:
            logger.info(f"주가 데이터: {len(data['stock_data'])}개 종목")

        if 'market_data' in data:
            logger.info(f"시장 데이터: {len(data['market_data'])}개 종목")

        if 'financial_data' in data:
            logger.info(f"재무 데이터: {len(data['financial_data'])}개 종목")

        logger.info("=" * 50)

    def get_ticker_info(self, ticker: str) -> Dict:
        """
        종목 기본 정보 조회

        Args:
            ticker: 종목코드

        Returns:
            종목 정보 딕셔너리
        """
        info = {}

        try:
            # 종목명
            name = self.market_collector.get_ticker_name(ticker)
            if name:
                info['name'] = name

            # 현재가
            current_price = self.stock_collector.get_current_price(ticker)
            if current_price:
                info['current_price'] = current_price

            # 재무 지표
            fundamental = self.financial_collector.get_fundamental_data(ticker)
            if fundamental:
                info.update(fundamental)

            logger.info(f"종목 정보 조회 완료: {ticker}")

        except Exception as e:
            logger.error(f"종목 정보 조회 실패: {ticker}, {str(e)}")

        return info
