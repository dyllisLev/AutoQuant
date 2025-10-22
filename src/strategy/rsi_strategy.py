"""
RSI 전략
"""

import pandas as pd
from .base_strategy import BaseStrategy
from src.analysis.technical_indicators import TechnicalIndicators


class RSIStrategy(BaseStrategy):
    """RSI 과매수/과매도 전략"""

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI_{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 시그널 생성

        Args:
            df: 주가 데이터

        Returns:
            시그널이 추가된 DataFrame
        """
        df = df.copy()

        # RSI 계산
        df['RSI'] = TechnicalIndicators.calculate_rsi(df, period=self.period)

        # 시그널 생성
        df['Signal'] = 'HOLD'

        # 과매도 -> 매수
        oversold_signal = (
            (df['RSI'] > self.oversold) &
            (df['RSI'].shift(1) <= self.oversold)
        )
        df.loc[oversold_signal, 'Signal'] = 'BUY'

        # 과매수 -> 매도
        overbought_signal = (
            (df['RSI'] < self.overbought) &
            (df['RSI'].shift(1) >= self.overbought)
        )
        df.loc[overbought_signal, 'Signal'] = 'SELL'

        return df
