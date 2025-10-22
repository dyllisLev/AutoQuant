"""
주가 데이터 수집기
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
from loguru import logger

try:
    from pykrx import stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False
    logger.warning("pykrx를 사용할 수 없습니다. pip install pykrx를 실행하세요.")

try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
    logger.warning("FinanceDataReader를 사용할 수 없습니다.")

from .base_collector import BaseCollector


class StockDataCollector(BaseCollector):
    """주가 데이터 수집기"""

    def __init__(self, retry_count: int = 3, retry_delay: int = 1):
        super().__init__(retry_count, retry_delay)
        self.market = 'KOSPI'  # 기본 시장

    def collect(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 365
    ) -> pd.DataFrame:
        """
        주가 데이터 수집

        Args:
            ticker: 종목코드 (예: '005930' - 삼성전자)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            days: start_date가 없을 경우 최근 n일 데이터 수집

        Returns:
            주가 데이터 DataFrame (날짜, 시가, 고가, 저가, 종가, 거래량 등)
        """
        logger.info(f"주가 데이터 수집 시작: {ticker}")

        if not start_date or not end_date:
            start_date, end_date = self._get_date_range(days)

        # pykrx 우선 사용
        if PYKRX_AVAILABLE:
            df = self._retry_on_failure(self._collect_with_pykrx, ticker, start_date, end_date)
        elif FDR_AVAILABLE:
            df = self._retry_on_failure(self._collect_with_fdr, ticker, start_date, end_date)
        else:
            raise ImportError("pykrx 또는 FinanceDataReader를 설치해주세요")

        if df is not None and not df.empty:
            df = self._process_stock_data(df, ticker)
            logger.info(f"주가 데이터 수집 완료: {ticker}, {len(df)} 건")
        else:
            logger.warning(f"주가 데이터가 비어있습니다: {ticker}")

        return df

    def _collect_with_pykrx(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """pykrx를 사용한 주가 데이터 수집"""
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        return df

    def _collect_with_fdr(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """FinanceDataReader를 사용한 주가 데이터 수집"""
        # YYYYMMDD -> YYYY-MM-DD 형식 변환
        start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        df = fdr.DataReader(ticker, start, end)
        return df

    def _process_stock_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """주가 데이터 전처리"""
        df = df.copy()

        # 컬럼명 표준화
        column_mapping = {
            '시가': 'Open',
            '고가': 'High',
            '저가': 'Low',
            '종가': 'Close',
            '거래량': 'Volume',
            '거래대금': 'Amount',
            '등락률': 'Change'
        }
        df.rename(columns=column_mapping, inplace=True)

        # 종목코드 추가
        df['Ticker'] = ticker

        # 날짜 인덱스 확인
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 결측치 처리
        df.fillna(method='ffill', inplace=True)

        return df

    def collect_multiple(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 365
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 주가 데이터 수집

        Args:
            tickers: 종목코드 리스트
            start_date: 시작일
            end_date: 종료일
            days: 데이터 수집 기간

        Returns:
            종목코드를 키로 하는 DataFrame 딕셔너리
        """
        logger.info(f"{len(tickers)}개 종목 데이터 수집 시작")

        result = {}
        for ticker in tickers:
            try:
                df = self.collect(ticker, start_date, end_date, days)
                if df is not None and not df.empty:
                    result[ticker] = df
            except Exception as e:
                logger.error(f"종목 {ticker} 데이터 수집 실패: {str(e)}")
                continue

        logger.info(f"{len(result)}개 종목 데이터 수집 완료")
        return result

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        현재가 조회

        Args:
            ticker: 종목코드

        Returns:
            현재가
        """
        try:
            if PYKRX_AVAILABLE:
                today = datetime.now().strftime('%Y%m%d')
                df = stock.get_market_ohlcv_by_date(today, today, ticker)
                if not df.empty:
                    return float(df.iloc[-1]['종가'])
        except Exception as e:
            logger.error(f"현재가 조회 실패: {ticker}, {str(e)}")

        return None

    def get_trading_volume(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """
        거래량 데이터 조회

        Args:
            ticker: 종목코드
            days: 조회 기간(일)

        Returns:
            거래량 데이터
        """
        start_date, end_date = self._get_date_range(days)
        df = self.collect(ticker, start_date, end_date)

        if df is not None and not df.empty:
            return df[['Volume', 'Close']]

        return pd.DataFrame()
