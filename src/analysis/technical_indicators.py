"""
기술적 지표 계산
"""

import pandas as pd
import numpy as np
from typing import Optional
from loguru import logger


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, column: str = 'Close', period: int = 20) -> pd.Series:
        """
        단순 이동평균 (Simple Moving Average)

        Args:
            df: 주가 데이터
            column: 계산할 컬럼
            period: 기간

        Returns:
            SMA 시리즈
        """
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, column: str = 'Close', period: int = 20) -> pd.Series:
        """
        지수 이동평균 (Exponential Moving Average)

        Args:
            df: 주가 데이터
            column: 계산할 컬럼
            period: 기간

        Returns:
            EMA 시리즈
        """
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, column: str = 'Close', period: int = 14) -> pd.Series:
        """
        상대강도지수 (Relative Strength Index)

        Args:
            df: 주가 데이터
            column: 계산할 컬럼
            period: 기간

        Returns:
            RSI 시리즈 (0-100)
        """
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(df: pd.DataFrame, column: str = 'Close',
                      fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """
        MACD (Moving Average Convergence Divergence)

        Args:
            df: 주가 데이터
            column: 계산할 컬럼
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간
            signal: 시그널 기간

        Returns:
            (MACD, Signal, Histogram) 튜플
        """
        ema_fast = df[column].ewm(span=fast, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow, adjust=False).mean()

        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return macd, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, column: str = 'Close',
                                  period: int = 20, std_dev: float = 2.0) -> tuple:
        """
        볼린저 밴드 (Bollinger Bands)

        Args:
            df: 주가 데이터
            column: 계산할 컬럼
            period: 기간
            std_dev: 표준편차 배수

        Returns:
            (Upper, Middle, Lower) 튜플
        """
        middle = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> tuple:
        """
        스토캐스틱 (Stochastic Oscillator)

        Args:
            df: 주가 데이터 (High, Low, Close 필요)
            period: 기간
            smooth_k: %K 스무딩
            smooth_d: %D 스무딩

        Returns:
            (%K, %D) 튜플
        """
        # Decimal 타입을 float로 변환 (PostgreSQL 호환)
        low = df['Low'].astype(float)
        high = df['High'].astype(float)
        close = df['Close'].astype(float)

        low_min = low.rolling(window=period).min()
        high_max = high.rolling(window=period).max()

        k = 100 * ((close - low_min) / (high_max - low_min))
        k = k.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        평균 진폭 범위 (Average True Range)

        Args:
            df: 주가 데이터 (High, Low, Close 필요)
            period: 기간

        Returns:
            ATR 시리즈
        """
        # Decimal 타입을 float로 변환 (PostgreSQL 호환)
        high = df['High'].astype(float)
        low = df['Low'].astype(float)
        close = df['Close'].astype(float)

        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """
        거래량 누적 (On-Balance Volume)

        Args:
            df: 주가 데이터 (Close, Volume 필요)

        Returns:
            OBV 시리즈
        """
        # Decimal 타입을 float로 변환 (PostgreSQL 호환)
        close = df['Close'].astype(float)
        volume = df['Volume'].astype(float)

        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 기술적 지표 추가

        Args:
            df: 주가 데이터

        Returns:
            지표가 추가된 DataFrame
        """
        df = df.copy()

        try:
            # 이동평균
            df['SMA_5'] = TechnicalIndicators.calculate_sma(df, period=5)
            df['SMA_20'] = TechnicalIndicators.calculate_sma(df, period=20)
            df['SMA_60'] = TechnicalIndicators.calculate_sma(df, period=60)

            df['EMA_12'] = TechnicalIndicators.calculate_ema(df, period=12)
            df['EMA_26'] = TechnicalIndicators.calculate_ema(df, period=26)

            # RSI
            df['RSI_14'] = TechnicalIndicators.calculate_rsi(df, period=14)

            # MACD
            macd, signal, histogram = TechnicalIndicators.calculate_macd(df)
            df['MACD'] = macd
            df['MACD_Signal'] = signal
            df['MACD_Histogram'] = histogram

            # 볼린저 밴드
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df)
            df['BB_Upper'] = upper
            df['BB_Middle'] = middle
            df['BB_Lower'] = lower

            # 스토캐스틱
            k, d = TechnicalIndicators.calculate_stochastic(df)
            df['Stoch_K'] = k
            df['Stoch_D'] = d

            # ATR
            df['ATR'] = TechnicalIndicators.calculate_atr(df)

            # OBV
            df['OBV'] = TechnicalIndicators.calculate_obv(df)

            logger.info("모든 기술적 지표 계산 완료")

        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")

        return df

    @staticmethod
    def get_trading_signals(df: pd.DataFrame) -> pd.DataFrame:
        """
        매매 시그널 생성

        Args:
            df: 지표가 계산된 데이터

        Returns:
            시그널이 추가된 DataFrame
        """
        df = df.copy()

        # Golden Cross / Death Cross
        df['Golden_Cross'] = ((df['SMA_5'] > df['SMA_20']) &
                             (df['SMA_5'].shift(1) <= df['SMA_20'].shift(1)))

        df['Death_Cross'] = ((df['SMA_5'] < df['SMA_20']) &
                            (df['SMA_5'].shift(1) >= df['SMA_20'].shift(1)))

        # RSI 과매수/과매도
        df['RSI_Oversold'] = df['RSI_14'] < 30  # 과매도
        df['RSI_Overbought'] = df['RSI_14'] > 70  # 과매수

        # MACD 크로스
        df['MACD_Cross_Up'] = ((df['MACD'] > df['MACD_Signal']) &
                              (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)))

        df['MACD_Cross_Down'] = ((df['MACD'] < df['MACD_Signal']) &
                                (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1)))

        # 볼린저 밴드 돌파
        df['BB_Break_Upper'] = df['Close'] > df['BB_Upper']
        df['BB_Break_Lower'] = df['Close'] < df['BB_Lower']

        return df
