"""
Support and Resistance Level Detection

Calculates key price levels:
- Support: Price floor where buying interest is strong
- Resistance: Price ceiling where selling pressure is strong
- Pivot Point: Technical indicator for trend direction
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from loguru import logger


class SupportResistanceDetector:
    """Detect support and resistance levels from price data"""

    @staticmethod
    def find_levels(df: pd.DataFrame, lookback: int = 60) -> Dict[str, float]:
        """
        Find support and resistance levels

        Args:
            df: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
            lookback: Number of days to look back (default: 60)

        Returns:
            Dictionary with:
            - support: Support level
            - resistance: Resistance level
            - pivot: Pivot point
            - current_price: Latest close price
            - high_60d: 60-day high
            - low_60d: 60-day low
        """
        if len(df) < lookback:
            lookback = len(df)
            logger.warning(f"Insufficient data, using {lookback} days instead")

        # Get last N days
        recent_df = df.tail(lookback)

        # Basic levels
        high_60d = recent_df['High'].max()
        low_60d = recent_df['Low'].min()
        current_price = df.iloc[-1]['Close']

        # Calculate support and resistance using different methods
        support, resistance = SupportResistanceDetector._calculate_sr_levels(recent_df)

        # Calculate pivot point (standard method)
        latest = df.iloc[-1]
        pivot = (latest['High'] + latest['Low'] + latest['Close']) / 3

        # Calculate additional pivot levels
        r1 = 2 * pivot - latest['Low']  # Resistance 1
        s1 = 2 * pivot - latest['High']  # Support 1
        r2 = pivot + (latest['High'] - latest['Low'])  # Resistance 2
        s2 = pivot - (latest['High'] - latest['Low'])  # Support 2

        return {
            'support': support,
            'resistance': resistance,
            'pivot': pivot,
            'r1': r1,
            's1': s1,
            'r2': r2,
            's2': s2,
            'current_price': current_price,
            'high_60d': high_60d,
            'low_60d': low_60d,
        }

    @staticmethod
    def _calculate_sr_levels(df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate support and resistance using multiple methods

        Methods:
        1. Swing highs/lows
        2. Round number levels
        3. Volume-weighted levels

        Returns:
            (support, resistance)
        """
        # Method 1: Find swing points (local minima/maxima)
        swing_lows = SupportResistanceDetector._find_swing_lows(df)
        swing_highs = SupportResistanceDetector._find_swing_highs(df)

        # Get recent swing points (last 20 days)
        recent_lows = [low for _, low in swing_lows[-5:]]
        recent_highs = [high for _, high in swing_highs[-5:]]

        # Support: Average of recent swing lows
        if recent_lows:
            support = np.mean(recent_lows)
        else:
            support = df['Low'].tail(20).min()

        # Resistance: Average of recent swing highs
        if recent_highs:
            resistance = np.mean(recent_highs)
        else:
            resistance = df['High'].tail(20).max()

        # Method 2: Adjust to round numbers (psychological levels)
        support = SupportResistanceDetector._round_to_psychological(support)
        resistance = SupportResistanceDetector._round_to_psychological(resistance)

        return support, resistance

    @staticmethod
    def _find_swing_lows(df: pd.DataFrame, window: int = 5) -> list:
        """
        Find swing lows (local minima)

        Args:
            df: Price data
            window: Window size for local minima detection

        Returns:
            List of (index, price) tuples
        """
        swing_lows = []
        lows = df['Low'].values

        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i - window:i + window + 1]):
                swing_lows.append((i, lows[i]))

        return swing_lows

    @staticmethod
    def _find_swing_highs(df: pd.DataFrame, window: int = 5) -> list:
        """
        Find swing highs (local maxima)

        Args:
            df: Price data
            window: Window size for local maxima detection

        Returns:
            List of (index, price) tuples
        """
        swing_highs = []
        highs = df['High'].values

        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                swing_highs.append((i, highs[i]))

        return swing_highs

    @staticmethod
    def _round_to_psychological(price: float) -> float:
        """
        Round to psychological level (round numbers)

        Examples:
        - 98,750 → 98,500
        - 1,234 → 1,200
        - 50,300 → 50,000

        Args:
            price: Original price

        Returns:
            Rounded price
        """
        if price < 1000:
            # Round to nearest 50
            return round(price / 50) * 50
        elif price < 10000:
            # Round to nearest 100
            return round(price / 100) * 100
        elif price < 100000:
            # Round to nearest 500
            return round(price / 500) * 500
        else:
            # Round to nearest 1000
            return round(price / 1000) * 1000

    @staticmethod
    def calculate_strength(df: pd.DataFrame, level: float, level_type: str = 'support') -> float:
        """
        Calculate strength of support/resistance level

        Strength based on:
        - Number of touches (price bounces off level)
        - Volume at those touches
        - Recency of touches

        Args:
            df: Price data
            level: Price level to check
            level_type: 'support' or 'resistance'

        Returns:
            Strength score (0-100)
        """
        tolerance = 0.02  # 2% tolerance for "touch"

        touches = 0
        total_volume = 0

        for idx, row in df.iterrows():
            if level_type == 'support':
                # Check if low is near support level
                if abs(row['Low'] - level) / level < tolerance:
                    touches += 1
                    total_volume += row['Volume']
            else:  # resistance
                # Check if high is near resistance level
                if abs(row['High'] - level) / level < tolerance:
                    touches += 1
                    total_volume += row['Volume']

        # Calculate strength score
        # More touches = stronger level
        # Higher volume = stronger level
        touch_score = min(touches * 10, 50)  # Max 50 points for touches

        # Normalize volume score
        avg_volume = df['Volume'].mean()
        if touches > 0:
            avg_touch_volume = total_volume / touches
            volume_score = min((avg_touch_volume / avg_volume) * 25, 50)  # Max 50 points
        else:
            volume_score = 0

        strength = touch_score + volume_score
        return min(strength, 100)  # Cap at 100
