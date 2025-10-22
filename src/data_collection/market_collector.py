"""
시장 데이터 수집기
"""

from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
from loguru import logger

try:
    from pykrx import stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False
    logger.warning("pykrx를 사용할 수 없습니다.")

try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
    logger.warning("FinanceDataReader를 사용할 수 없습니다.")

from .base_collector import BaseCollector


class MarketDataCollector(BaseCollector):
    """시장 데이터 수집기"""

    def __init__(self, retry_count: int = 3, retry_delay: int = 1):
        super().__init__(retry_count, retry_delay)

    def collect(self, market: str = 'KOSPI', date: Optional[str] = None) -> pd.DataFrame:
        """
        특정 시장의 전체 종목 데이터 수집

        Args:
            market: 시장 구분 ('KOSPI', 'KOSDAQ', 'KONEX')
            date: 기준일 (YYYYMMDD), None이면 오늘

        Returns:
            시장 데이터 DataFrame
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        logger.info(f"{market} 시장 데이터 수집: {date}")

        if PYKRX_AVAILABLE:
            df = self._retry_on_failure(self._collect_market_data_pykrx, market, date)
        else:
            df = self._retry_on_failure(self._collect_market_data_fdr, market)

        if df is not None and not df.empty:
            logger.info(f"{market} 시장 데이터 수집 완료: {len(df)} 종목")
        else:
            logger.warning(f"{market} 시장 데이터가 비어있습니다")

        return df

    def _collect_market_data_pykrx(self, market: str, date: str) -> pd.DataFrame:
        """pykrx를 사용한 시장 데이터 수집"""
        df = stock.get_market_cap_by_ticker(date, market=market)

        # 종목명 추가
        tickers = df.index.tolist()
        names = [stock.get_market_ticker_name(ticker) for ticker in tickers]
        df['Name'] = names
        df['Market'] = market
        df['Date'] = date

        return df

    def _collect_market_data_fdr(self, market: str) -> pd.DataFrame:
        """FinanceDataReader를 사용한 시장 데이터 수집"""
        if market == 'KOSPI':
            df = fdr.StockListing('KOSPI')
        elif market == 'KOSDAQ':
            df = fdr.StockListing('KOSDAQ')
        elif market == 'KONEX':
            df = fdr.StockListing('KONEX')
        else:
            df = fdr.StockListing('KRX')

        return df

    def get_ticker_list(self, market: str = 'KOSPI') -> List[str]:
        """
        시장의 전체 종목코드 리스트 조회

        Args:
            market: 시장 구분

        Returns:
            종목코드 리스트
        """
        logger.info(f"{market} 종목 리스트 조회")

        try:
            if PYKRX_AVAILABLE:
                tickers = stock.get_market_ticker_list(market=market)
                logger.info(f"{market} 종목 수: {len(tickers)}")
                return tickers
            elif FDR_AVAILABLE:
                df = self._collect_market_data_fdr(market)
                if 'Code' in df.columns:
                    return df['Code'].tolist()
                elif 'Symbol' in df.columns:
                    return df['Symbol'].tolist()
        except Exception as e:
            logger.error(f"종목 리스트 조회 실패: {str(e)}")

        return []

    def get_ticker_name(self, ticker: str) -> Optional[str]:
        """
        종목코드로 종목명 조회

        Args:
            ticker: 종목코드

        Returns:
            종목명
        """
        try:
            if PYKRX_AVAILABLE:
                return stock.get_market_ticker_name(ticker)
        except Exception as e:
            logger.error(f"종목명 조회 실패: {ticker}, {str(e)}")

        return None

    def get_market_cap(self, market: str = 'KOSPI', date: Optional[str] = None) -> pd.DataFrame:
        """
        시가총액 정보 조회

        Args:
            market: 시장 구분
            date: 기준일

        Returns:
            시가총액 데이터
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        logger.info(f"{market} 시가총액 조회: {date}")

        try:
            if PYKRX_AVAILABLE:
                df = stock.get_market_cap_by_ticker(date, market=market)
                return df
        except Exception as e:
            logger.error(f"시가총액 조회 실패: {str(e)}")

        return pd.DataFrame()

    def get_top_stocks(
        self,
        market: str = 'KOSPI',
        criterion: str = 'market_cap',
        top_n: int = 100
    ) -> List[str]:
        """
        특정 기준으로 상위 종목 조회

        Args:
            market: 시장 구분
            criterion: 정렬 기준 ('market_cap': 시가총액, 'volume': 거래량)
            top_n: 상위 n개

        Returns:
            상위 종목코드 리스트
        """
        logger.info(f"{market} 상위 {top_n}개 종목 조회 (기준: {criterion})")

        try:
            date = datetime.now().strftime('%Y%m%d')
            df = self.collect(market, date)

            if df.empty:
                return []

            if criterion == 'market_cap' and '시가총액' in df.columns:
                df_sorted = df.sort_values('시가총액', ascending=False)
            elif criterion == 'volume' and '거래량' in df.columns:
                df_sorted = df.sort_values('거래량', ascending=False)
            else:
                logger.warning(f"정렬 기준을 찾을 수 없습니다: {criterion}")
                return []

            tickers = df_sorted.head(top_n).index.tolist()
            logger.info(f"상위 {len(tickers)}개 종목 조회 완료")
            return tickers

        except Exception as e:
            logger.error(f"상위 종목 조회 실패: {str(e)}")
            return []

    def get_sector_stocks(self, sector: str) -> List[str]:
        """
        특정 섹터의 종목 리스트 조회

        Args:
            sector: 섹터명

        Returns:
            종목코드 리스트
        """
        logger.info(f"{sector} 섹터 종목 조회")

        try:
            if FDR_AVAILABLE:
                df = fdr.StockListing('KRX')
                if 'Sector' in df.columns:
                    sector_df = df[df['Sector'] == sector]
                    return sector_df['Code'].tolist()
        except Exception as e:
            logger.error(f"섹터 종목 조회 실패: {str(e)}")

        return []
