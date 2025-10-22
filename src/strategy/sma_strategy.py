"""
SMA 크로스오버 전략
"""

import pandas as pd
from .base_strategy import BaseStrategy
from src.analysis.technical_indicators import TechnicalIndicators


class SMAStrategy(BaseStrategy):
    """단순 이동평균 크로스오버 전략"""

    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__(f"SMA_{short_period}_{long_period}")
        self.short_period = short_period
        self.long_period = long_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SMA 크로스오버 시그널 생성

        Args:
            df: 주가 데이터

        Returns:
            시그널이 추가된 DataFrame
        """
        df = df.copy()

        # SMA 계산
        df[f'SMA_{self.short_period}'] = TechnicalIndicators.calculate_sma(df, period=self.short_period)
        df[f'SMA_{self.long_period}'] = TechnicalIndicators.calculate_sma(df, period=self.long_period)

        # 시그널 생성
        df['Signal'] = 'HOLD'

        # Golden Cross (매수)
        golden_cross = (
            (df[f'SMA_{self.short_period}'] > df[f'SMA_{self.long_period}']) &
            (df[f'SMA_{self.short_period}'].shift(1) <= df[f'SMA_{self.long_period}'].shift(1))
        )
        df.loc[golden_cross, 'Signal'] = 'BUY'

        # Death Cross (매도)
        death_cross = (
            (df[f'SMA_{self.short_period}'] < df[f'SMA_{self.long_period}']) &
            (df[f'SMA_{self.short_period}'].shift(1) >= df[f'SMA_{self.long_period}'].shift(1))
        )
        df.loc[death_cross, 'Signal'] = 'SELL'

        return df
