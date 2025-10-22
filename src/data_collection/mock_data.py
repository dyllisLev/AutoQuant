"""
모의 데이터 생성기 (테스트 및 데모용)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class MockDataGenerator:
    """모의 주식 데이터 생성기"""

    def __init__(self, seed: int = 42):
        """
        Args:
            seed: 난수 시드 (재현 가능한 데이터 생성)
        """
        np.random.seed(seed)
        self.stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '005380': '현대차',
            '006400': '삼성SDI',
            '000270': '기아',
            '105560': 'KB금융',
            '055550': '신한지주'
        }

    def generate_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        initial_price: int = 50000
    ) -> pd.DataFrame:
        """
        주가 데이터 생성

        Args:
            ticker: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            initial_price: 초기 가격

        Returns:
            주가 데이터 DataFrame
        """
        # 날짜 범위 생성
        start = pd.to_datetime(start_date, format='%Y%m%d')
        end = pd.to_datetime(end_date, format='%Y%m%d')

        # 거래일만 생성 (주말 제외)
        dates = pd.bdate_range(start=start, end=end)

        if len(dates) == 0:
            return pd.DataFrame()

        # 가격 데이터 생성 (랜덤워크)
        returns = np.random.normal(0.001, 0.02, len(dates))  # 평균 0.1%, 표준편차 2%
        prices = initial_price * np.exp(np.cumsum(returns))

        data = []
        for i, date in enumerate(dates):
            close = prices[i]
            daily_volatility = close * 0.015  # 1.5% 일일 변동성

            open_price = close + np.random.normal(0, daily_volatility * 0.5)
            high = max(open_price, close) + abs(np.random.normal(0, daily_volatility * 0.3))
            low = min(open_price, close) - abs(np.random.normal(0, daily_volatility * 0.3))

            volume = np.random.randint(1000000, 10000000)
            amount = volume * close

            data.append({
                'Open': int(open_price),
                'High': int(high),
                'Low': int(low),
                'Close': int(close),
                'Volume': volume,
                'Amount': int(amount),
                'Ticker': ticker
            })

        df = pd.DataFrame(data, index=dates)
        df.index.name = 'Date'

        return df

    def generate_market_data(self, market: str = 'KOSPI', date: str = None) -> pd.DataFrame:
        """
        시장 데이터 생성

        Args:
            market: 시장 구분
            date: 기준일

        Returns:
            시장 데이터 DataFrame
        """
        tickers = list(self.stock_names.keys())
        data = []

        for ticker in tickers:
            name = self.stock_names[ticker]
            market_cap = np.random.randint(1000000, 100000000) * 100000  # 시가총액
            volume = np.random.randint(100000, 5000000)
            close = np.random.randint(30000, 100000)

            data.append({
                'Ticker': ticker,
                'Name': name,
                'Close': close,
                'MarketCap': market_cap,
                'Volume': volume,
                'Market': market
            })

        df = pd.DataFrame(data)
        df.set_index('Ticker', inplace=True)

        # 시가총액 순으로 정렬
        df.sort_values('MarketCap', ascending=False, inplace=True)

        return df

    def generate_fundamental_data(self, ticker: str) -> Dict:
        """
        재무 지표 생성

        Args:
            ticker: 종목코드

        Returns:
            재무 지표 딕셔너리
        """
        return {
            'PER': round(np.random.uniform(5, 25), 2),
            'PBR': round(np.random.uniform(0.5, 3.0), 2),
            'ROE': round(np.random.uniform(5, 20), 2),
            'EPS': int(np.random.uniform(1000, 10000)),
            'BPS': int(np.random.uniform(10000, 50000)),
            'DIV': round(np.random.uniform(0.5, 3.5), 2)
        }

    def get_ticker_list(self, market: str = 'KOSPI') -> List[str]:
        """종목 리스트 반환"""
        return list(self.stock_names.keys())

    def get_ticker_name(self, ticker: str) -> str:
        """종목명 반환"""
        return self.stock_names.get(ticker, f"종목{ticker}")

    def get_current_price(self, ticker: str) -> int:
        """현재가 생성"""
        return np.random.randint(30000, 100000)


# 전역 인스턴스
mock_generator = MockDataGenerator()
