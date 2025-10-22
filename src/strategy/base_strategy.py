"""
매매 전략 기본 클래스
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Optional
from loguru import logger


class BaseStrategy(ABC):
    """매매 전략 기본 클래스"""

    def __init__(self, name: str):
        self.name = name
        self.signals = []

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        매매 시그널 생성

        Args:
            df: 주가 데이터 (기술적 지표 포함)

        Returns:
            시그널이 추가된 DataFrame
        """
        pass

    def get_position(self, df: pd.DataFrame, index: int) -> str:
        """
        현재 포지션 확인

        Args:
            df: 데이터프레임
            index: 인덱스

        Returns:
            'BUY', 'SELL', 'HOLD'
        """
        if 'Signal' not in df.columns:
            return 'HOLD'

        signal = df.iloc[index]['Signal']
        return signal if pd.notna(signal) else 'HOLD'

    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000000) -> Dict:
        """
        백테스팅 수행

        Args:
            df: 주가 데이터
            initial_capital: 초기 자본

        Returns:
            백테스팅 결과
        """
        df = self.generate_signals(df)

        capital = initial_capital
        shares = 0
        trades = []

        for i in range(len(df)):
            signal = self.get_position(df, i)
            price = df.iloc[i]['Close']
            date = df.index[i]

            if signal == 'BUY' and shares == 0:
                # 매수
                shares = capital // price
                cost = shares * price
                capital -= cost
                trades.append({
                    'date': date,
                    'type': 'BUY',
                    'price': price,
                    'shares': shares,
                    'capital': capital
                })

            elif signal == 'SELL' and shares > 0:
                # 매도
                revenue = shares * price
                capital += revenue
                trades.append({
                    'date': date,
                    'type': 'SELL',
                    'price': price,
                    'shares': shares,
                    'capital': capital
                })
                shares = 0

        # 최종 청산
        if shares > 0:
            final_price = df.iloc[-1]['Close']
            capital += shares * final_price

        total_return = ((capital - initial_capital) / initial_capital) * 100

        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'trades': trades,
            'num_trades': len(trades)
        }
