"""
Price Calculator - Hybrid Trading Price Calculation

Calculates buy/target/stop-loss prices using:
1. AI predictions (LSTM + XGBoost)
2. Support/Resistance levels
3. ATR-based volatility
4. Risk/Reward ratio validation
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from loguru import logger

from src.database.database import Database
from src.analysis.prediction_models import LSTMPredictor, XGBoostPredictor
from src.analysis.technical_indicators import TechnicalIndicators
from src.pricing.support_resistance import SupportResistanceDetector


class PriceCalculator:
    """
    Calculate trading prices for selected stocks

    Output:
    - buy_price: Entry price (current + 0.5~1.5%)
    - target_price: Profit target (AI prediction or resistance)
    - stop_loss_price: Loss limit (support or ATR-based)
    - ai_confidence: Prediction confidence (0-100)
    - predicted_return: Expected return %
    - risk_reward_ratio: Risk/Reward ratio
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize PriceCalculator

        Args:
            db: Database instance (optional, creates new if None)
        """
        self.db = db or Database()
        self.tech_indicators = TechnicalIndicators()
        self.sr_detector = SupportResistanceDetector()

        # AI models (using simple prediction for MVP)
        self.use_ai_prediction = False  # Set to True when models are trained
        self.lstm_predictor = None
        self.xgboost_predictor = None

    def calculate_prices(
        self,
        stock_code: str,
        current_price: float,
        technical_data: pd.DataFrame,
        prediction_days: int = 7
    ) -> Dict[str, float]:
        """
        Calculate buy/target/stop-loss prices

        Args:
            stock_code: Stock code
            current_price: Current close price
            technical_data: DataFrame with OHLCV and technical indicators
            prediction_days: Days to predict ahead (default: 7)

        Returns:
            Dictionary with:
            - buy_price
            - target_price
            - stop_loss_price
            - ai_confidence
            - predicted_return
            - risk_reward_ratio
            - current_price
            - support_level
            - resistance_level
        """
        logger.info(f"💰 Calculating prices for {stock_code}")

        # 1. Get Support/Resistance levels
        sr_levels = self.sr_detector.find_levels(technical_data, lookback=60)
        support = sr_levels['support']
        resistance = sr_levels['resistance']
        pivot = sr_levels['pivot']

        logger.debug(f"   Support: {support:,.0f}, Resistance: {resistance:,.0f}, Pivot: {pivot:,.0f}")

        # 2. Get ATR for volatility-based calculations
        latest = technical_data.iloc[-1]
        atr = latest.get('ATR', None)

        if pd.isna(atr) or atr == 0:
            # Fallback: use 3% of current price
            atr = current_price * 0.03
            logger.warning(f"   ATR not available, using 3% fallback: {atr:,.0f}")

        # 3. Get AI prediction (if available)
        ai_target_price, ai_confidence = self._get_ai_prediction(
            technical_data,
            current_price,
            prediction_days
        )

        # 4. Calculate Buy Price
        # Buy at current price + small premium (0.5~1.5%)
        # Ensure it's above support
        buy_premium_pct = self._calculate_buy_premium(technical_data)
        buy_price = current_price * (1 + buy_premium_pct / 100)

        # Ensure buy price is above support
        if buy_price < support:
            buy_price = support * 1.005  # 0.5% above support
            logger.debug(f"   Buy price adjusted to above support: {buy_price:,.0f}")

        # 5. Calculate Target Price
        # Use minimum of:
        # - AI prediction (if available and bullish)
        # - Resistance level (conservative)
        # - Technical target (current + 2*ATR)

        technical_target = current_price + (2 * atr)

        if ai_target_price and ai_target_price > current_price:
            # Use AI prediction if bullish
            target_candidates = [ai_target_price, resistance, technical_target]
        else:
            # Use technical levels only
            target_candidates = [resistance, technical_target]

        # Choose conservative target (lower of candidates, but above current)
        valid_targets = [t for t in target_candidates if t > buy_price]
        if valid_targets:
            target_price = min(valid_targets)
        else:
            target_price = buy_price * 1.02  # Minimum 2% profit

        # 6. Calculate Stop-Loss Price
        # Use maximum of:
        # - Support level * 0.98 (2% below support for safety)
        # - Current price - 2*ATR (volatility-based)
        # But ensure it's below buy price

        support_stop = support * 0.98
        atr_stop = current_price - (2 * atr)

        stop_loss_price = max(support_stop, atr_stop)

        # Ensure stop-loss is below buy price
        if stop_loss_price >= buy_price:
            stop_loss_price = buy_price * 0.97  # 3% below buy price
            logger.warning(f"   Stop-loss adjusted to below buy price: {stop_loss_price:,.0f}")

        # 7. Calculate Risk/Reward Ratio
        potential_profit = target_price - buy_price
        potential_loss = buy_price - stop_loss_price

        if potential_loss > 0:
            risk_reward_ratio = potential_profit / potential_loss
        else:
            risk_reward_ratio = 99.0  # Extremely favorable

        # 8. Calculate predicted return
        predicted_return = ((target_price - buy_price) / buy_price) * 100

        # 9. Validate Risk/Reward
        if risk_reward_ratio < 0.8:
            logger.warning(f"   ⚠️ Risk/Reward ratio too low: {risk_reward_ratio:.2f}")
            # Adjust target to improve R/R
            target_price = buy_price + (potential_loss * 1.0)  # 1:1 minimum
            predicted_return = ((target_price - buy_price) / buy_price) * 100
            risk_reward_ratio = 1.0

        logger.info(f"   ✅ Buy: {buy_price:,.0f} | Target: {target_price:,.0f} | Stop: {stop_loss_price:,.0f}")
        logger.info(f"   📊 Profit: +{predicted_return:.2f}% | Risk: -{(potential_loss/buy_price)*100:.2f}% | R/R: {risk_reward_ratio:.2f}")

        return {
            'buy_price': round(buy_price, -1),  # Round to nearest 10
            'target_price': round(target_price, -1),
            'stop_loss_price': round(stop_loss_price, -1),
            'ai_confidence': ai_confidence,
            'predicted_return': round(predicted_return, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'current_price': current_price,
            'support_level': support,
            'resistance_level': resistance,
            'pivot_point': pivot,
            'atr': atr,
        }

    def _calculate_buy_premium(self, df: pd.DataFrame) -> float:
        """
        Calculate buy premium percentage based on market conditions

        Args:
            df: Technical data with indicators

        Returns:
            Premium percentage (0.5 ~ 1.5%)
        """
        latest = df.iloc[-1]

        # Start with base premium
        premium = 1.0  # 1%

        # Adjust based on RSI
        rsi = latest.get('RSI_14', 50)
        if rsi < 30:
            # Oversold: lower premium
            premium -= 0.3
        elif rsi > 70:
            # Overbought: higher premium
            premium += 0.3

        # Adjust based on MACD
        macd = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_Signal', 0)
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:
                # Bullish MACD: slightly higher premium
                premium += 0.2

        # Cap between 0.5% and 1.5%
        premium = max(0.5, min(1.5, premium))

        return premium

    def _get_ai_prediction(
        self,
        df: pd.DataFrame,
        current_price: float,
        days_ahead: int = 7
    ) -> tuple:
        """
        Get AI price prediction (LSTM + XGBoost)

        Args:
            df: Historical price data
            current_price: Current price
            days_ahead: Days to predict

        Returns:
            (predicted_price, confidence)
        """
        if not self.use_ai_prediction:
            # AI models not trained yet, use simple technical projection
            logger.debug("   AI prediction not available, using technical projection")

            # Use trend-based projection
            sma_5 = df.iloc[-1].get('SMA_5', current_price)
            sma_20 = df.iloc[-1].get('SMA_20', current_price)

            # Calculate trend strength
            if sma_5 > sma_20:
                # Uptrend: project 2-5% gain
                trend_strength = min((sma_5 - sma_20) / sma_20 * 100, 5)
                predicted_price = current_price * (1 + trend_strength / 100)
                confidence = 60  # Moderate confidence
            else:
                # Downtrend or neutral: conservative 1% gain
                predicted_price = current_price * 1.01
                confidence = 50  # Low confidence

            return predicted_price, confidence

        # TODO: Implement actual LSTM + XGBoost prediction when models are ready
        # For now, return None to use technical-only approach
        return None, 0

    def calculate_batch_prices(
        self,
        selected_stocks: pd.DataFrame,
        prediction_days: int = 7
    ) -> pd.DataFrame:
        """
        Calculate prices for multiple stocks (batch processing)

        Args:
            selected_stocks: DataFrame with selected stocks (from Phase 4)
                Must have columns: stock_code, company_name, final_score
            prediction_days: Days ahead to predict

        Returns:
            DataFrame with price calculations added
        """
        logger.info(f"💰 Calculating prices for {len(selected_stocks)} stocks")

        results = []

        for idx, stock in selected_stocks.iterrows():
            stock_code = stock['stock_code']

            try:
                # Get OHLCV data
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=200)

                ohlcv_df = self.db.get_daily_ohlcv_from_kis(
                    stock_code,
                    start_date=start_date,
                    end_date=end_date
                )

                if ohlcv_df is None or len(ohlcv_df) < 60:
                    logger.warning(f"⚠️ Insufficient data for {stock_code}, skipping")
                    continue

                # Prepare data
                ohlcv_df = ohlcv_df.copy()
                ohlcv_df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)

                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in ohlcv_df.columns:
                        ohlcv_df[col] = ohlcv_df[col].astype(float)

                # Add technical indicators
                ohlcv_with_indicators = self.tech_indicators.add_all_indicators(ohlcv_df)

                # Get current price
                current_price = float(ohlcv_with_indicators.iloc[-1]['Close'])

                # Calculate prices
                prices = self.calculate_prices(
                    stock_code=stock_code,
                    current_price=current_price,
                    technical_data=ohlcv_with_indicators,
                    prediction_days=prediction_days
                )

                # Combine with stock info
                result = stock.to_dict()
                result.update(prices)
                results.append(result)

            except Exception as e:
                logger.error(f"❌ Error calculating prices for {stock_code}: {str(e)}")
                continue

        if not results:
            logger.warning("⚠️ No price calculations succeeded")
            return pd.DataFrame()

        result_df = pd.DataFrame(results)
        logger.info(f"✅ Price calculation complete: {len(result_df)} stocks")

        return result_df
