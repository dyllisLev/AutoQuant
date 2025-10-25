"""
Phase 4 Integration Test: Technical Screening
Filter AI-selected 30~40 candidates down to 3~5 final selections using technical scores

Run: python tests/user_tests/test_04_technical_screening.py
Or:  python -m pytest tests/user_tests/test_04_technical_screening.py -v -s
"""

import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from loguru import logger

from src.database.database import Database
from src.analysis.technical_screener import TechnicalScreener
from sqlalchemy import text


def test_phase4_technical_screening():
    """Test Phase 4: Technical screening from AI candidates"""

    logger.info("=" * 80)
    logger.info("🔍 PHASE 4: TECHNICAL SCREENING TEST")
    logger.info("=" * 80)

    try:
        # Initialize database and screener
        db = Database()
        tech_screener = TechnicalScreener()

        logger.info("\n📊 Step 1: Loading AI candidates from KIS DB (mock Phase 3 output)...")

        # Get latest stock data with company information
        session = db.get_session()

        query = """
            SELECT
                d.symbol_code,
                COALESCE(k.korean_name, kq.korean_name) as company_name,
                d.close_price as close,
                d.volume,
                COALESCE(k.market_cap, kq.prev_day_market_cap) as market_cap
            FROM daily_ohlcv d
            LEFT JOIN kospi_stock_info k ON d.symbol_code = k.short_code
            LEFT JOIN kosdaq_stock_info kq ON d.symbol_code = kq.short_code
            WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily_ohlcv)
            AND (
                COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%ETF%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%ETN%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%KODEX%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%KOSEF%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%TIGER%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%ACE%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%인버스%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%레버리지%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%선물%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%펀드%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%수익증권%'
                AND COALESCE(k.korean_name, kq.korean_name) NOT ILIKE '%채권%'
            )
            ORDER BY d.volume DESC
            LIMIT 40
        """

        result = session.execute(text(query))
        columns = result.keys()
        rows = result.fetchall()
        session.close()

        if not rows:
            logger.error("❌ Failed to load stock data")
            return False

        # Create DataFrame with AI candidates
        ai_candidates = pd.DataFrame(rows, columns=columns)

        # Add AI confidence scores (simulated Phase 3 output)
        ai_candidates['ai_confidence'] = np.random.uniform(70, 95, len(ai_candidates))
        ai_candidates['stock_code'] = ai_candidates['symbol_code']

        logger.info(f"✅ Loaded {len(ai_candidates)} AI candidates")
        logger.info(f"   Target range: 30~40 candidates")
        logger.info(f"   Actual: {len(ai_candidates)} candidates")

        # Show top AI selections
        logger.info(f"\n📈 Top 5 AI Candidates (by confidence):")
        top_ai = ai_candidates.nlargest(5, 'ai_confidence')
        for rank, (idx, stock) in enumerate(top_ai.iterrows(), 1):
            logger.info(f"   {rank}. {stock['stock_code']} ({stock['company_name']}) - "
                       f"AI Confidence: {stock['ai_confidence']:.0f}%")

        # ==========================================================================
        # PHASE 4: Technical Screening
        # ==========================================================================
        logger.info("\n⚡ Step 2: Technical Screening (30~40 → 3~5)...")

        final_selections = tech_screener.screen(ai_candidates)

        if final_selections is None or len(final_selections) == 0:
            logger.error("❌ Technical screening returned no results")
            return False

        logger.info(f"✅ Technical screening completed:")
        logger.info(f"   - Final selections: {len(final_selections)}")
        logger.info(f"   - Target range: 3~5")

        # Validate count
        if len(final_selections) < 1:
            logger.error("❌ No stocks selected!")
            return False

        # ==========================================================================
        # Results Summary
        # ==========================================================================
        logger.info("\n" + "=" * 80)
        logger.info("📋 FINAL RESULTS - STOCKS READY FOR TRADING SIGNAL GENERATION")
        logger.info("=" * 80)

        for rank, (idx, stock) in enumerate(final_selections.iterrows(), 1):
            logger.info(f"\n{rank}. {stock['stock_code']} - {stock['company_name']}")
            logger.info(f"   AI Confidence: {stock['ai_confidence']:.0f}%")
            logger.info(f"   Technical Scores:")
            logger.info(f"     - SMA: {stock['sma_score']:.1f}/20")
            logger.info(f"     - RSI: {stock['rsi_score']:.1f}/15")
            logger.info(f"     - MACD: {stock['macd_score']:.1f}/15")
            logger.info(f"     - Bollinger: {stock['bb_score']:.1f}/10")
            logger.info(f"     - Volume: {stock['volume_score']:.1f}/10")
            logger.info(f"     - Total Technical: {stock['technical_score']:.1f}/70")
            logger.info(f"   Final Score: {stock['final_score']:.1f}/100")

        logger.info("\n" + "=" * 80)
        logger.info("✅ PHASE 4 TEST PASSED - Ready for Phase 5 (Price Calculation)")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase4_technical_screening()
    exit(0 if success else 1)
