# AutoQuant Project Overview

## Purpose
AI-based **pre-market analysis system** for Korean stock markets that generates daily trading signals for the next trading day.

**Key Identity**: This is a **signal generation and analysis tool**, NOT a trading execution program. Separate external program reads TradingSignal table and executes trades.

## System Architecture (8-Layer Pipeline)
1. **Data Collection**: pykrx (4,359 Korean stocks daily OHLCV)
2. **Market Analysis**: MarketAnalyzer (sentiment, momentum, investor flows)
3. **AI Screening** (Phase 3): AIScreener (semantic analysis, 4,359 → 30~40)
4. **Technical Screening** (Phase 4): TechnicalScreener (quantitative, 30~40 → 3~5)
5. **AI Prediction** (Phase 5): LSTM/XGBoost models (7-day forward prices)
6. **Price Calculation** (Phase 5): Hybrid pricing (AI + support/resistance + ATR)
7. **Signal Persistence** (Phase 6): TradingSignal table (buy/target/stop-loss)
8. **External Trading**: KIS/Kiwoom API executes trades (NOT part of AutoQuant)

## Current Status
- ✅ Phase 1: Database schema (TradingSignal, MarketSnapshot)
- ✅ Phase 2: Market analysis (5-factor momentum + 3 improvements: RSI+MACD, volume strength, signal convergence)
- 🔄 Phase 3: AI-based screening (next - uses improved sentiment confidence)
- ⏳ Phases 4-6: Technical screening, price calculation, daily execution

## Key Concepts

### Two-Layer Filtering (Cost Optimization)
- **Layer 1 (AI, 4,359→30~40)**: External AI analyzes all stocks semantically
- **Layer 2 (Technical, 30~40→3~5)**: TechnicalScreener scores quantitatively
- **Why**: Reduces computational cost by 99.8%

### Backtesting Scope (PREDICTION VALIDATION ONLY)
- ✅ Validate LSTM/XGBoost prediction accuracy
- ✅ Measure directional accuracy % and MAPE
- ✅ Validate confidence score calibration
- ❌ Does NOT measure strategy performance (system doesn't execute)
- ❌ Results don't apply to real trading

### Phase 2 Improvements (Just Completed)
1. **Technical Signals (RSI+MACD)**: Detects overbought/oversold and trend changes
2. **Volume Strength**: ±10 point adjustment based on 20-day volume ratio
3. **Signal Convergence**: Confidence multiplier (0.7-1.15) based on signal alignment

Returns sentiment with detailed breakdown and confidence level (높음/중간/낮음).

## Tech Stack
- **Language**: Python 3.8+
- **Database**: PostgreSQL (KIS data) + SQLite/PostgreSQL (AutoQuant)
- **ML**: TensorFlow/Keras (LSTM), XGBoost, scikit-learn
- **Data**: pandas, numpy
- **APIs**: pykrx (Korean stocks), external AI (OpenAI/Anthropic/Google)
- **Web**: Flask dashboard
- **Logging**: loguru
- **Automation**: Daily cron job (3:45 PM KST post-market)

## Two-Database Architecture
- **KIS PostgreSQL** (read-only): daily_ohlcv table, 4,359 stocks
- **AutoQuant DB** (read/write): Stock, StockPrice, Prediction, TradingSignal, MarketSnapshot, etc.
- Configured in .env: DB_TYPE=postgresql or sqlite

## Daily Execution Flow
1. **3:45 PM KST**: daily_analysis.py runs post-market
2. **Market Analysis**: MarketAnalyzer generates sentiment for next day
3. **AI Screening**: AIScreener selects 30~40 candidates
4. **Technical Screening**: TechnicalScreener ranks top 3~5
5. **Price Calculation**: Calculate buy/target/stop-loss prices
6. **Signal Storage**: Write to TradingSignal table
7. **External Trader**: Reads signals and executes trades

## External AI API Requirement
- **Cost**: ~$0.03-0.90/month (1 call/day)
- **Providers**: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini)
- **Configuration**: AI_SCREENING_PROVIDER in .env
- **Mandatory**: Required for Phase 3 screening layer