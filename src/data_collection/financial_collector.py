"""
재무제표 데이터 수집기
"""

from datetime import datetime
from typing import Optional, Dict
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


class FinancialDataCollector(BaseCollector):
    """재무제표 데이터 수집기"""

    def __init__(self, retry_count: int = 3, retry_delay: int = 1):
        super().__init__(retry_count, retry_delay)

    def collect(self, ticker: str, year: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        재무제표 데이터 수집

        Args:
            ticker: 종목코드
            year: 연도 (None이면 최신)

        Returns:
            재무제표 데이터 딕셔너리 (BS, IS, CF)
        """
        if year is None:
            year = datetime.now().year

        logger.info(f"재무제표 수집: {ticker}, {year}년")

        result = {}

        try:
            # 재무상태표 (Balance Sheet)
            bs = self.get_balance_sheet(ticker, year)
            if bs is not None and not bs.empty:
                result['balance_sheet'] = bs

            # 손익계산서 (Income Statement)
            income_stmt = self.get_income_statement(ticker, year)
            if income_stmt is not None and not income_stmt.empty:
                result['income_statement'] = income_stmt

            # 현금흐름표 (Cash Flow)
            cf = self.get_cash_flow(ticker, year)
            if cf is not None and not cf.empty:
                result['cash_flow'] = cf

            logger.info(f"재무제표 수집 완료: {ticker}, {len(result)}개 보고서")

        except Exception as e:
            logger.error(f"재무제표 수집 실패: {ticker}, {str(e)}")

        return result

    def get_balance_sheet(self, ticker: str, year: int) -> Optional[pd.DataFrame]:
        """
        재무상태표 조회

        Args:
            ticker: 종목코드
            year: 연도

        Returns:
            재무상태표 DataFrame
        """
        try:
            if PYKRX_AVAILABLE:
                # pykrx는 현재 재무제표 API를 직접 제공하지 않음
                # 대안: 크롤링 또는 다른 API 사용
                pass

            # 여기서는 구조만 정의
            logger.warning("재무상태표 수집 기능은 추가 구현 필요")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"재무상태표 조회 실패: {str(e)}")
            return None

    def get_income_statement(self, ticker: str, year: int) -> Optional[pd.DataFrame]:
        """
        손익계산서 조회

        Args:
            ticker: 종목코드
            year: 연도

        Returns:
            손익계산서 DataFrame
        """
        try:
            logger.warning("손익계산서 수집 기능은 추가 구현 필요")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"손익계산서 조회 실패: {str(e)}")
            return None

    def get_cash_flow(self, ticker: str, year: int) -> Optional[pd.DataFrame]:
        """
        현금흐름표 조회

        Args:
            ticker: 종목코드
            year: 연도

        Returns:
            현금흐름표 DataFrame
        """
        try:
            logger.warning("현금흐름표 수집 기능은 추가 구현 필요")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"현금흐름표 조회 실패: {str(e)}")
            return None

    def get_fundamental_data(self, ticker: str, date: Optional[str] = None) -> Dict:
        """
        기본적 분석 지표 조회 (PER, PBR, ROE, 배당수익률 등)

        Args:
            ticker: 종목코드
            date: 기준일 (YYYYMMDD)

        Returns:
            기본적 분석 지표 딕셔너리
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        logger.info(f"기본적 분석 지표 조회: {ticker}, {date}")

        result = {}

        try:
            if PYKRX_AVAILABLE:
                # 기본적 지표 조회
                df = stock.get_market_fundamental_by_ticker(date, market="ALL")

                if ticker in df.index:
                    ticker_data = df.loc[ticker]

                    result['PER'] = ticker_data.get('PER', None)
                    result['PBR'] = ticker_data.get('PBR', None)
                    result['DIV'] = ticker_data.get('DIV', None)  # 배당수익률
                    result['EPS'] = ticker_data.get('EPS', None)
                    result['BPS'] = ticker_data.get('BPS', None)

                    logger.info(f"기본적 지표 조회 완료: {ticker}")
                else:
                    logger.warning(f"종목을 찾을 수 없습니다: {ticker}")

        except Exception as e:
            logger.error(f"기본적 지표 조회 실패: {str(e)}")

        return result

    def get_eps_history(
        self,
        ticker: str,
        start_year: int,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        EPS 히스토리 조회

        Args:
            ticker: 종목코드
            start_year: 시작 연도
            end_year: 종료 연도 (None이면 현재 연도)

        Returns:
            EPS 히스토리 DataFrame
        """
        if end_year is None:
            end_year = datetime.now().year

        logger.info(f"EPS 히스토리 조회: {ticker}, {start_year}-{end_year}")

        eps_data = []

        try:
            for year in range(start_year, end_year + 1):
                for quarter in range(1, 5):
                    date = f"{year}{quarter:02d}01"
                    fundamental = self.get_fundamental_data(ticker, date)
                    if fundamental and 'EPS' in fundamental:
                        eps_data.append({
                            'Year': year,
                            'Quarter': quarter,
                            'Date': date,
                            'EPS': fundamental['EPS']
                        })

            df = pd.DataFrame(eps_data)
            logger.info(f"EPS 히스토리 조회 완료: {len(df)} 건")
            return df

        except Exception as e:
            logger.error(f"EPS 히스토리 조회 실패: {str(e)}")
            return pd.DataFrame()

    def get_financial_ratios(self, ticker: str) -> Dict:
        """
        재무비율 계산

        Args:
            ticker: 종목코드

        Returns:
            재무비율 딕셔너리
        """
        logger.info(f"재무비율 계산: {ticker}")

        ratios = {}

        try:
            fundamental = self.get_fundamental_data(ticker)

            if fundamental:
                # PER, PBR은 이미 수집됨
                ratios['PER'] = fundamental.get('PER')
                ratios['PBR'] = fundamental.get('PBR')
                ratios['Dividend_Yield'] = fundamental.get('DIV')

                # ROE 계산 (추가 구현 필요)
                # ROE = 순이익 / 자기자본
                # ratios['ROE'] = ...

                logger.info(f"재무비율 계산 완료: {ticker}")

        except Exception as e:
            logger.error(f"재무비율 계산 실패: {str(e)}")

        return ratios
