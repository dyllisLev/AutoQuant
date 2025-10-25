"""
Technical Screener: Phase 4 - Filter 30~40 AI candidates down to 3~5 final selections
Using 5-factor technical scoring system:
- SMA crossover alignment (20 points)
- RSI momentum (15 points)
- MACD strength (15 points)
- Bollinger band position (10 points)
- Volume confirmation (10 points)
Total: 70 points max
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger

from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators


class TechnicalScreener:
    """Filter AI-selected candidates (30~40) to final selections (3~5) using technical scores"""

    def __init__(self):
        self.db = Database()
        self.tech_indicators = TechnicalIndicators()
        self.min_final_selections = 3
        self.max_final_selections = 5

    def screen(self, ai_candidates: pd.DataFrame, trading_date: str = None) -> pd.DataFrame:
        """
        Screen AI candidates using technical indicators and return top 3~5 stocks

        Args:
            ai_candidates: DataFrame with columns [stock_code, company_name, ai_confidence, ...]
            trading_date: Date string 'YYYY-MM-DD' for data retrieval (default: latest)

        Returns:
            DataFrame with technical_score, final_score, and sorted by final_score (descending)
        """
        if len(ai_candidates) == 0:
            logger.warning("⚠️ No AI candidates provided for technical screening")
            return pd.DataFrame()

        # Note: ETF/ETN filtering is now done at query level when fetching candidates
        logger.info(f"🔍 {len(ai_candidates)}개 일반주식에 대해 기술적 스크리닝 시작...")

        # Add technical scores to each candidate
        candidates_with_scores = ai_candidates.copy()
        candidates_with_scores['technical_score'] = 0.0
        candidates_with_scores['sma_score'] = 0.0
        candidates_with_scores['rsi_score'] = 0.0
        candidates_with_scores['macd_score'] = 0.0
        candidates_with_scores['bb_score'] = 0.0
        candidates_with_scores['volume_score'] = 0.0
        candidates_with_scores['final_score'] = 0.0

        for idx, row in ai_candidates.iterrows():
            stock_code = row['stock_code']

            try:
                # Get OHLCV data for this stock (last 200 days)
                from datetime import datetime, timedelta

                end_date = datetime.now()
                start_date = end_date - timedelta(days=200)

                ohlcv_df = self.db.get_daily_ohlcv_from_kis(
                    stock_code,
                    start_date=start_date,
                    end_date=end_date
                )

                if ohlcv_df is None or len(ohlcv_df) < 50:
                    logger.warning(f"⚠️ Insufficient data for {stock_code}, skipping")
                    candidates_with_scores.loc[idx, 'final_score'] = -999  # Mark as invalid
                    continue

                # Rename columns to match TechnicalIndicators expectations
                ohlcv_df = ohlcv_df.copy()
                ohlcv_df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)

                # Convert Decimal to float
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in ohlcv_df.columns:
                        ohlcv_df[col] = ohlcv_df[col].astype(float)

                # Calculate all technical indicators
                ohlcv_with_indicators = self.tech_indicators.add_all_indicators(ohlcv_df)

                # Get latest values (today's candle)
                latest = ohlcv_with_indicators.iloc[-1]

                # Calculate individual scores
                sma_score = self._score_sma(ohlcv_with_indicators)
                rsi_score = self._score_rsi(latest)
                macd_score = self._score_macd(latest)
                bb_score = self._score_bollinger(latest)
                volume_score = self._score_volume(ohlcv_with_indicators)

                # Total technical score (0-70)
                technical_score = sma_score + rsi_score + macd_score + bb_score + volume_score

                # AI confidence (0-100)
                ai_confidence = row.get('ai_confidence', 50)

                # Final score: 60% technical + 40% AI confidence
                final_score = (technical_score * 0.6) + (ai_confidence * 0.4)

                # Store scores
                candidates_with_scores.loc[idx, 'sma_score'] = sma_score
                candidates_with_scores.loc[idx, 'rsi_score'] = rsi_score
                candidates_with_scores.loc[idx, 'macd_score'] = macd_score
                candidates_with_scores.loc[idx, 'bb_score'] = bb_score
                candidates_with_scores.loc[idx, 'volume_score'] = volume_score
                candidates_with_scores.loc[idx, 'technical_score'] = technical_score
                candidates_with_scores.loc[idx, 'final_score'] = final_score

                logger.debug(f"✓ {stock_code}: technical={technical_score:.1f}, final={final_score:.1f}")

            except Exception as e:
                logger.error(f"✗ Error screening {stock_code}: {str(e)}")
                candidates_with_scores.loc[idx, 'final_score'] = -999

        # Filter out invalid scores and sort by final_score
        valid_candidates = candidates_with_scores[candidates_with_scores['final_score'] > -999]
        valid_candidates = valid_candidates.sort_values('final_score', ascending=False)

        # Select top 3~5 (or fewer if less than 3 candidates available)
        num_selections = min(
            self.max_final_selections,
            max(self.min_final_selections, len(valid_candidates) // 8)
        )
        final_selections = valid_candidates.head(num_selections)

        logger.info(f"✅ Technical screening complete: {len(final_selections)} stocks selected from {len(ai_candidates)} candidates")
        logger.info(f"   AI 후보: {len(ai_candidates)}개 → 기술 스크리닝: {len(final_selections)}개 선정")

        for rank, (idx, stock) in enumerate(final_selections.iterrows(), 1):
            logger.info(f"  {rank}. {stock['stock_code']} ({stock['company_name']}) - "
                       f"Technical: {stock['technical_score']:.1f}, Final: {stock['final_score']:.1f}")

        return final_selections

    def _score_sma(self, df: pd.DataFrame) -> float:
        """
        Score SMA crossover alignment (0-20 points)
        Perfect: Close > SMA20 > SMA50 > SMA200 (20 points)
        Good: Close > SMA20 > SMA50 (15 points)
        Fair: Close > SMA20 (10 points)
        None: Below SMA20 (0 points)

        Note: If SMA_50/SMA_200 unavailable (not enough data), uses SMA_20 only
        """
        if len(df) < 20:
            return 0.0

        latest = df.iloc[-1]
        close = latest['Close']

        sma20 = latest.get('SMA_20')
        sma50 = latest.get('SMA_50')
        sma200 = latest.get('SMA_200')

        if pd.isna(sma20):
            return 0.0

        # Try full alignment first (if enough data for all SMAs)
        if pd.notna(sma50) and pd.notna(sma200):
            if close > sma20 > sma50 > sma200:
                return 20.0
            elif close > sma20 > sma50:
                return 15.0

        # Fallback: use available SMAs
        if close > sma20:
            return 10.0
        else:
            return 0.0

    def _score_rsi(self, latest: pd.Series) -> float:
        """
        Score RSI momentum (0-15 points)
        Uptrend (50-70): 15 points
        Neutral (30-50): 10 points
        Oversold (<30): 10 points (potential bounce)
        Overbought (>70): 5 points (caution)
        """
        rsi = latest.get('RSI_14')

        if pd.isna(rsi):
            return 0.0

        if 50 <= rsi <= 70:
            return 15.0
        elif 30 <= rsi < 50:
            return 10.0
        elif rsi < 30:
            return 10.0  # Oversold = potential bounce
        else:  # rsi > 70
            return 5.0   # Overbought = caution

    def _score_macd(self, latest: pd.Series) -> float:
        """
        Score MACD strength (0-15 points)
        Strong bullish: MACD > Signal + histogram increasing (15 points)
        Bullish: MACD > Signal (10 points)
        Bearish: MACD < Signal (0 points)
        """
        macd = latest.get('MACD')
        signal = latest.get('MACD_Signal')  # Fixed: was 'Signal_Line', correct name is 'MACD_Signal'
        histogram = latest.get('MACD_Histogram')

        if pd.isna(macd) or pd.isna(signal):
            return 0.0

        # Check if histogram is increasing (comparing with previous value would need full df)
        # For now, we use simpler logic: just MACD vs Signal

        if macd > signal:
            # If we had previous data, we could check if histogram is increasing
            return 15.0 if not pd.isna(histogram) and histogram > 0 else 10.0
        else:
            return 0.0

    def _score_bollinger(self, latest: pd.Series) -> float:
        """
        Score Bollinger Band position (0-10 points)
        Near upper band, above middle: 10 points
        Above middle: 7 points
        Near middle: 5 points
        Near lower band: 3 points
        """
        close = latest['Close']
        bb_upper = latest.get('BB_Upper')
        bb_middle = latest.get('BB_Middle')
        bb_lower = latest.get('BB_Lower')

        if pd.isna(bb_upper) or pd.isna(bb_middle) or pd.isna(bb_lower):
            return 0.0

        # Normalize position within band (0=lower, 1=upper)
        band_range = bb_upper - bb_lower
        if band_range == 0:
            return 5.0

        position = (close - bb_lower) / band_range

        if position >= 0.7:  # Upper 30%
            return 10.0
        elif position >= 0.55:  # Upper 45%
            return 7.0
        elif position >= 0.45:  # Middle 10%
            return 5.0
        else:  # Lower half
            return 3.0

    def _score_volume(self, df: pd.DataFrame) -> float:
        """
        Score volume confirmation (0-10 points)
        > 1.5x average: 10 points
        > 1.2x average: 7 points
        Average: 5 points
        < average: 2 points
        """
        if len(df) < 20:
            return 5.0

        latest_volume = df.iloc[-1]['Volume']
        avg_volume = df['Volume'].tail(20).mean()

        if avg_volume == 0:
            return 5.0

        volume_ratio = latest_volume / avg_volume

        if volume_ratio >= 1.5:
            return 10.0
        elif volume_ratio >= 1.2:
            return 7.0
        elif volume_ratio >= 0.8:
            return 5.0
        else:
            return 2.0


def run_technical_screening(ai_candidates: pd.DataFrame, trading_date: str = None) -> pd.DataFrame:
    """Convenience function to run technical screening"""
    screener = TechnicalScreener()
    return screener.screen(ai_candidates, trading_date)
