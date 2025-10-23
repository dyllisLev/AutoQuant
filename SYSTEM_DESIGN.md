# SYSTEM_DESIGN.md - AutoQuant AI-Based Pre-Market Analysis System

## System Identity

**AutoQuant** is transformed from a backtesting/analysis tool into an **AI-based pre-market analysis system** that:
- Analyzes market conditions and 4,359 Korean stocks daily (post-market)
- Generates AI-driven trading signals for the next trading day
- Calculates specific buy prices, target prices, and stop-loss prices
- Stores trading signals in database for a separate trading execution program
- Provides AI-powered portfolio analysis and recommendations

**Critical Note**: This is a **signal generation and analysis tool**, NOT a trading execution program. Actual trades are executed by a separate external program reading the `TradingSignal` database table.

---

## System Architecture Overview

### Eight-Layer Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: DATA COLLECTION & ENRICHMENT                           │
│ - KIS PostgreSQL: Daily OHLCV (4,359 Korean stocks)             │
│ - pykrx: Investor flow, market cap, trading volume              │
│ - FinanceDataReader: Sector/industry classification              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: MARKET ANALYSIS (MarketAnalyzer)                       │
│ - Consolidate market snapshot (sector trends, investor flow)    │
│ - Calculate market momentum indicators                           │
│ - Identify market regime (uptrend/downtrend/range)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: AI-BASED SCREENING - 1ST FILTER (AIScreener)           │
│ 4,359 stocks → 30~40 candidates                                 │
│ - Send market analysis + sector data to AI API (GPT-4/Claude)   │
│ - AI evaluates: investor sentiment, thematic momentum, relative │
│   strength vs market conditions                                  │
│ - AI returns ranked 30~40 candidate stocks with reasoning       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: TECHNICAL ANALYSIS - 2ND FILTER (TechnicalScreener)    │
│ 30~40 candidates → 3~5 final selections                         │
│ - Calculate technical indicators (SMA, RSI, MACD, Bollinger)    │
│ - Score each stock using point system:                          │
│   * SMA crossover alignment: 20 points                          │
│   * RSI momentum: 15 points                                     │
│   * MACD strength: 15 points                                    │
│   * Bollinger band position: 10 points                          │
│   * Volume confirmation: 10 points                              │
│ - Select top 3~5 highest-scoring stocks                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: AI PRICE PREDICTION (LSTMPredictor + XGBoostPredictor) │
│ - Train models on historical 1-year OHLCV data                  │
│ - Predict 7-day forward price direction and magnitude           │
│ - Generate confidence scores for prediction reliability         │
│ - Return predicted closing price and confidence level           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 6: TRADING PRICE CALCULATION (PriceCalculator)            │
│ - Support/Resistance levels: Identify key price levels          │
│ - BUY PRICE: Slightly above current price (technical entry)     │
│ - TARGET PRICE: Based on predicted price + resistance level     │
│ - STOP-LOSS: ATR-based volatility calculation + support level   │
│ - Calculate risk/reward ratio and expected return %             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 7: SIGNAL PERSISTENCE (TradingSignal Table)               │
│ - Store trading signals in PostgreSQL/SQLite                    │
│ - Include: stock code, buy price, target price, stop-loss,      │
│   analysis date, target trade date, AI confidence, predicted    │
│   return, technical indicators, status (pending/executed/...)   │
│ - Create MarketSnapshot for historical analysis                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 8: EXTERNAL TRADING EXECUTION                             │
│ (Separate Program - NOT part of AutoQuant)                      │
│ - Read TradingSignal table with websocket monitoring            │
│ - Execute trades via KIS/Kiwoom API when real-time prices      │
│   match buy/sell parameters                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Parallel Workflow: AI-Based Prediction Validation

```
┌──────────────────────────────────────────────────────────┐
│ BACKTESTING FLOW (Prediction Validation)                 │
│ - NOT for daily execution                                │
│ - Runs offline to validate AI model accuracy             │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Historical data (1 year minimum)                         │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Train LSTM + XGBoost models                              │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Generate predictions for test period                     │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Validate against actual price movements                  │
│ - Accuracy: % of correct direction predictions          │
│ - MAPE: Mean absolute percentage error in price level   │
│ - Confidence calibration: Do confidence scores match     │
│   actual accuracy?                                       │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ Monthly report: Model performance metrics                │
│ - Adjust prediction thresholds if needed                 │
│ - Retrain models if drift detected                       │
└──────────────────────────────────────────────────────────┘
```

---

## Daily Execution Flow (Example)

**Time: 3:45 PM KST (Post-market close at 3:30 PM)**

```
1. [daily_analysis.py] START
   Input: Current date (e.g., 2024-10-25 for next trading day 2024-10-28)

2. [DATA COLLECTION - LAYER 1]
   - Query KIS: Latest OHLCV for 4,359 stocks (today's data)
   - Query pykrx: Foreign/institution/retail flows (시가총액, 상한가 도달)
   - Consolidate into MarketSnapshot table

3. [MARKET ANALYSIS - LAYER 2]
   - Analyze sector performance
   - Calculate market momentum (KPI: KOSPI 상승장/하락장)
   - Identify investor flow patterns
   - Save to MarketSnapshot table

4. [AI SCREENING - LAYER 3]
   - Build prompt: Market conditions + 4,359 stock data + sector trends
   - Call external AI API (GPT-4, Claude, or Gemini)
   - Example AI response:
     ```
     Top candidates based on market analysis:
     1. 삼성전자 (005930) - AI chip demand + foreign buying
     2. SK하이닉스 (000660) - Sector momentum + earnings season
     3. 카카오 (035720) - Platform strength + media consumption trend
     ... (27 more stocks)

     Market Context: Positive investor sentiment, cyclical upturn,
     technology sector outperformance
     ```
   - Extract 30~40 candidate stock codes

5. [TECHNICAL SCREENING - LAYER 4]
   - For each of 30~40 candidates:
     * Calculate SMA_5, SMA_20, SMA_60, SMA_200
     * Calculate RSI(14)
     * Calculate MACD + Signal line
     * Calculate Bollinger Bands
     * Check volume confirmation
     * Score each indicator
   - Select top 3~5 highest-scoring stocks
   - Example output:
     ```
     삼성전자 (005930): 70 points
       - SMA: 20 (5>20>60, aligned uptrend)
       - RSI: 15 (52, strong momentum, not overbought)
       - MACD: 15 (positive, above signal line)
       - Bollinger: 10 (mid-band region, room to move)
       - Volume: 10 (confirmed above average)

     현대차 (005380): 68 points
     ... (3 more stocks)
     ```

6. [AI PRICE PREDICTION - LAYER 5]
   - For each of top 3~5 stocks:
     * Load LSTM model trained on this stock's 1-year historical data
     * Load XGBoost model trained on same data
     * Prepare input features: OHLCV + technical indicators
     * Generate 7-day forward predictions
     * Example prediction for Samsung (삼성전자):
       ```
       LSTM prediction: 79,500 KRW (confidence: 72%)
       XGBoost prediction: 78,800 KRW (confidence: 68%)
       Consensus: 79,150 KRW (confidence: 70%)
       ```

7. [TRADING PRICE CALCULATION - LAYER 6]
   - Current price example: Samsung 78,000 KRW
   - Find support/resistance:
     * Recent support: 77,500 KRW
     * Recent resistance: 80,500 KRW
   - Calculate trading prices:
     * BUY PRICE: 78,300 KRW (just above current, technical entry)
     * TARGET PRICE: 79,500 KRW (from AI prediction, below resistance)
     * Calculate ATR(14): 450 KRW
     * STOP-LOSS: 77,200 KRW (1.5x ATR below support)
     * Risk: 78,300 - 77,200 = 1,100 KRW
     * Reward: 79,500 - 78,300 = 1,200 KRW
     * Risk/Reward Ratio: 0.92 (acceptable)
     * Expected Return: +1.54% (if target hit)

8. [SIGNAL PERSISTENCE - LAYER 7]
   - INSERT into TradingSignal table:
     ```
     stock_id: 1 (Samsung's ID)
     analysis_date: 2024-10-25
     target_trade_date: 2024-10-28
     buy_price: 78,300
     target_price: 79,500
     stop_loss_price: 77,200
     ai_confidence: 70
     predicted_return: 1.54
     current_rsi: 52
     current_macd: 125
     current_bollinger_position: 'mid'
     market_trend: 'uptrend'
     investor_flow: 'positive'
     sector_momentum: 'strong'
     status: 'pending'
     created_at: 2024-10-25 15:45:00
     ```
   - Create 3~5 such records for all selected stocks

9. [COMPLETION]
   - Log: "Generated 3 trading signals for next trading day"
   - Email notification to trader with summary:
     ```
     Daily Analysis Complete - 2024-10-25
     Analysis Date: 2024-10-25 (for trading 2024-10-28)
     Signals Generated: 3

     Stock | Buy | Target | Stop-Loss | Risk/Reward | Confidence
     -------|-----|--------|-----------|-------------|----------
     Samsung| 78,300 | 79,500 | 77,200 | 0.92 | 70%
     Hyundai| 68,400 | 70,100 | 67,200 | 1.13 | 65%
     Kakao  | 42,500 | 44,200 | 41,800 | 1.21 | 68%
     ```
   - Next execution: Tomorrow at 3:45 PM
```

---

## Database Schema Extensions

### New Table: TradingSignal

```sql
CREATE TABLE trading_signal (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stock(id),
    analysis_date DATE NOT NULL,
    target_trade_date DATE NOT NULL,
    buy_price DECIMAL(10,2) NOT NULL,
    target_price DECIMAL(10,2) NOT NULL,
    stop_loss_price DECIMAL(10,2) NOT NULL,
    ai_confidence INTEGER NOT NULL,  -- 0-100%
    predicted_return DECIMAL(5,2) NOT NULL,  -- Expected % return
    current_rsi DECIMAL(5,2),
    current_macd DECIMAL(10,4),
    current_bollinger_position VARCHAR(20),  -- 'upper'/'middle'/'lower'
    market_trend VARCHAR(20),  -- 'uptrend'/'downtrend'/'range'
    investor_flow VARCHAR(20),  -- 'positive'/'negative'/'neutral'
    sector_momentum VARCHAR(20),  -- 'strong'/'moderate'/'weak'
    ai_reasoning TEXT,  -- Why AI selected this stock
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending'/'executed'/'missed'/'cancelled'
    executed_price DECIMAL(10,2),  -- Actual execution price if traded
    executed_date TIMESTAMP,
    actual_return DECIMAL(5,2),  -- Actual % return achieved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trading_signal_target_date ON trading_signal(target_trade_date);
CREATE INDEX idx_trading_signal_status ON trading_signal(status);
CREATE INDEX idx_trading_signal_stock_date ON trading_signal(stock_id, analysis_date);
```

### New Table: MarketSnapshot

```sql
CREATE TABLE market_snapshot (
    id BIGSERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    kospi_close DECIMAL(10,2),
    kospi_change DECIMAL(5,2),  -- Daily % change
    kosdaq_close DECIMAL(10,2),
    kosdaq_change DECIMAL(5,2),
    advance_decline_ratio DECIMAL(5,2),  -- Advancing / Declining stocks
    foreign_flow BIGINT,  -- Foreign investor net buying (KRW)
    institution_flow BIGINT,  -- Institutional net buying (KRW)
    retail_flow BIGINT,  -- Retail net buying (KRW)
    sector_performance JSON,  -- {'IT': 1.2, 'Finance': -0.5, ...}
    top_sectors TEXT[],  -- ['IT', 'Semiconductors', ...]
    market_sentiment VARCHAR(20),  -- 'bullish'/'bearish'/'neutral'
    momentum_score INTEGER,  -- 0-100, composite market momentum
    volatility_index DECIMAL(5,2),  -- VIX-like measure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_snapshot_date ON market_snapshot(snapshot_date);
```

---

## Directory Structure - New Modules

```
AutoQuant/
├── src/
│   ├── data_collection/          # [EXISTING - Enhanced]
│   │   ├── market_collector.py   # Now actively used
│   │   ├── financial_collector.py # Now actively used
│   │   ├── stock_collector.py    # Now actively used
│   │   └── ...
│   │
│   ├── database/                 # [EXISTING - Extended]
│   │   ├── models.py             # Add TradingSignal, MarketSnapshot models
│   │   └── database_manager.py   # Add methods for new tables
│   │
│   ├── analysis/                 # [EXISTING - Enhanced]
│   │   ├── technical_indicators.py       # [UNCHANGED]
│   │   ├── prediction_models.py          # Add confidence scoring
│   │   └── ...
│   │
│   ├── strategy/                 # [EXISTING - Repurposed]
│   │   └── ... (SMA/RSI strategies still present but not used for daily)
│   │
│   ├── screening/                # [NEW MODULE]
│   │   ├── __init__.py
│   │   ├── market_analyzer.py             # LAYER 2: Market analysis
│   │   ├── ai_screener.py                 # LAYER 3: AI-based screening
│   │   └── technical_screener.py          # LAYER 4: Technical screening
│   │
│   ├── pricing/                  # [NEW MODULE]
│   │   ├── __init__.py
│   │   ├── price_calculator.py            # LAYER 6: Trading price calculation
│   │   ├── support_resistance.py          # Support/Resistance detection
│   │   └── risk_calculator.py             # Risk/reward calculations
│   │
│   └── portfolio/                # [EXISTING - Enhanced]
│       ├── portfolio_manager.py           # Add AI analysis capability
│       └── ...
│
├── scripts/                      # [NEW/EXISTING]
│   ├── daily_analysis.py         # [NEW] MAIN: Daily signal generation
│   ├── backtest_strategy.py      # [NEW] Prediction validation
│   ├── monthly_evaluation.py     # [NEW] Model performance review
│   ├── collect_data.py           # [EXISTING]
│   └── ...
│
├── tests/                        # [EXISTING - Add new tests]
│   ├── screening/
│   │   ├── test_market_analyzer.py
│   │   ├── test_ai_screener.py
│   │   └── test_technical_screener.py
│   ├── pricing/
│   │   ├── test_price_calculator.py
│   │   ├── test_support_resistance.py
│   │   └── test_risk_calculator.py
│   └── ...
│
├── SYSTEM_DESIGN.md              # [NEW] This document
├── AI_INTEGRATION.md             # [NEW] AI API integration guide
├── IMPLEMENTATION_PLAN.md        # [NEW] 6-phase implementation plan
└── CLAUDE.md                     # [UPDATED] With references
```

---

## Key Modules Overview

### 1. MarketAnalyzer (src/screening/market_analyzer.py)

**Purpose**: Consolidate market data and identify market conditions.

**Key Methods**:
```python
class MarketAnalyzer:
    def analyze_market(self, date: str) -> MarketSnapshot:
        """Analyze market conditions for given date"""
        # 1. Get KOSPI/KOSDAQ prices
        # 2. Calculate investor flows (foreign/institution/retail)
        # 3. Analyze sector performance
        # 4. Identify market regime (uptrend/downtrend/range)
        # 5. Calculate momentum score
        # 6. Return comprehensive market snapshot

    def get_sector_performance(self) -> Dict[str, float]:
        """Get sector-wise performance metrics"""

    def get_investor_flows(self) -> Dict[str, int]:
        """Get investor type flows"""
```

**Output**: MarketSnapshot object containing all market context for AI screening.

### 2. AIScreener (src/screening/ai_screener.py)

**Purpose**: Use external AI API to reduce 4,359 stocks to 30~40 candidates.

**Key Methods**:
```python
class AIScreener:
    def screen_stocks(self, market_snapshot: MarketSnapshot) -> List[str]:
        """Screen 4,359 stocks down to 30~40 candidates using AI API"""
        # 1. Build comprehensive prompt with market context
        # 2. Include all 4,359 stock data + recent performance
        # 3. Call external AI API (GPT-4/Claude/Gemini)
        # 4. Parse AI response for stock codes
        # 5. Return top 30~40 candidates with reasoning

    def _build_screening_prompt(self, market_snapshot: MarketSnapshot) -> str:
        """Build detailed prompt for AI API"""

    def _call_ai_api(self, prompt: str) -> str:
        """Call external AI API (configurable provider)"""
```

**Output**: List of 30~40 stock codes ranked by AI confidence.

### 3. TechnicalScreener (src/screening/technical_screener.py)

**Purpose**: Further filter AI-selected 30~40 down to 3~5 using technical indicators.

**Key Methods**:
```python
class TechnicalScreener:
    def screen_stocks(self, candidates: List[str]) -> List[Dict]:
        """Score and rank 30~40 candidates, return top 3~5"""
        # For each candidate:
        #   1. Calculate all technical indicators
        #   2. Apply scoring rubric (SMA=20pts, RSI=15pts, ...)
        #   3. Sum to get total score
        #   4. Sort by score, return top 3~5

    def calculate_technical_score(self, df: pd.DataFrame) -> float:
        """Calculate composite technical score for single stock"""
        score = 0
        score += 20 if self._sma_aligned(df) else 0
        score += 15 if self._rsi_momentum(df) else 0
        score += 15 if self._macd_strength(df) else 0
        score += 10 if self._bollinger_position(df) else 0
        score += 10 if self._volume_confirmation(df) else 0
        return score
```

**Output**: Top 3~5 stocks with detailed technical analysis.

### 4. PriceCalculator (src/pricing/price_calculator.py)

**Purpose**: Calculate buy price, target price, and stop-loss price for final 3~5 stocks.

**Key Methods**:
```python
class PriceCalculator:
    def calculate_trading_prices(self, stock_code: str,
                                  predicted_price: float,
                                  ai_confidence: float) -> TradingPrices:
        """Calculate buy/target/stop-loss prices"""
        # 1. Find support/resistance levels
        # 2. Determine buy price (technical entry point)
        # 3. Set target price (from AI prediction + resistance)
        # 4. Calculate stop-loss (ATR-based volatility)
        # 5. Return TradingPrices with risk/reward analysis

    def _find_support_resistance(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Identify support and resistance levels"""

    def _calculate_stop_loss(self, price: float, atr: float) -> float:
        """Calculate stop-loss using ATR volatility"""
```

**Output**: TradingPrices object with buy/target/stop-loss and risk metrics.

### 5. Daily Analysis Script (scripts/daily_analysis.py)

**Purpose**: Main orchestrator that runs all 6 layers daily post-market.

**Execution**:
```python
def main():
    # 1. Data Collection (Layer 1)
    # 2. Market Analysis (Layer 2)
    # 3. AI Screening (Layer 3)
    # 4. Technical Screening (Layer 4)
    # 5. AI Price Prediction (Layer 5)
    # 6. Price Calculation (Layer 6)
    # 7. Signal Persistence (Layer 7)
    # 8. Notification & Logging

# Scheduled to run daily at 3:45 PM KST (post-market)
```

---

## Two-Layer Filtering Rationale

### Problem Statement
- **Challenge**: Analyzing 4,359 stocks daily for trading signals is computationally expensive
- **Time cost**: 4,359 stocks × 10 min per analysis = ~730 hours per day (impossible)
- **API cost**: Daily API calls for all stocks = $$$
- **Signal quality**: Diluted signals from low-quality candidates

### Solution: Two-Layer Filtering

**Layer 1 - AI-Based Semantic Filtering (4,359 → 30~40)**
- Uses external AI API (costs ~$1-5 per call)
- Analyzes high-level market context and thematic patterns
- AI evaluates: "Given current market conditions, which 30~40 stocks have highest probability of outperformance?"
- Advantages:
  - Semantic understanding of market narratives
  - Fast reduction (single API call)
  - Captures thematic momentum (AI chips, EVs, renewable energy, etc.)
  - Considers investor flow and institutional positioning

**Layer 2 - Technical Quantitative Filtering (30~40 → 3~5)**
- Uses established technical indicators (no API cost)
- Objective scoring system
- Advantages:
  - Precise entry/exit signals
  - Explainable scoring (point system)
  - Historical backtestable
  - Confirms AI selection with technical setup

### Result
- Reduces analysis scope by 99.8% (4,359 → 3~5)
- Combines semantic wisdom (AI) with quantitative precision (technical)
- Manageable computational/API cost
- High-quality signal generation

---

## Backtesting Scope (Prediction Validation)

**Important**: Backtesting in this system is NOT for strategy backtesting. Instead, it validates AI prediction model accuracy.

### Backtesting Workflow

1. **Offline Validation** (Weekly or monthly)
   - Load 1-year historical data for selected stocks
   - Train LSTM and XGBoost models
   - Generate predictions on test period
   - Validate against actual price movements

2. **Metrics Captured**
   - Directional accuracy: % of correct up/down predictions
   - Magnitude error: MAPE (Mean Absolute Percentage Error)
   - Confidence calibration: Do 70% confidence predictions actually have 70% accuracy?

3. **Output**: Model performance report
   - LSTM accuracy: 58% directional, 3.2% MAPE
   - XGBoost accuracy: 61% directional, 2.8% MAPE
   - Confidence threshold recommendations

4. **Monthly Evaluation**
   - Compare predicted vs actual returns for last month's signals
   - Identify model drift
   - Retrain models if needed

**Backtesting is NOT used for:**
- ❌ Daily trading execution
- ❌ Strategy performance measurement
- ❌ Risk management (backtesting results don't apply to real trades)

---

## Comparison: Old System vs New System

### Old System (Analysis & Backtesting Tool)
```
Purpose: Backtest trading strategies on historical data
Flow: KIS OHLCV → Indicators → Strategy signals → Backtest engine → Metrics
Output: Strategy performance report
Scope: Analysis/learning tool
Users: Quantitative researchers, strategy developers
```

### New System (AI-Based Pre-Market Analysis Tool)
```
Purpose: Generate daily trading signals for next trading day
Flow: Market data → AI screen (semantic) → Technical screen (quantitative)
      → AI predict → Calculate prices → Store signals → External trader executes
Output: TradingSignal table with 3~5 stocks, buy/target/stop-loss prices
Scope: Daily decision-support tool
Users: Traders, portfolio managers, trading desk
```

---

## Integration with External Trading Program

**Critical**: AutoQuant is the **analysis and signal generation engine**. Actual trading is done by a **separate external program**.

### Data Handoff
```
AutoQuant (3:45 PM)          External Trading Program (all day)
┌─────────────────┐         ┌──────────────────────────┐
│ Generate        │  DB     │ Read TradingSignal       │
│ TradingSignal   │────────→│ Monitor websocket prices │
│ table entries   │         │ When price hits buy/sell │
│ for next day    │         │ → Execute trade via API  │
└─────────────────┘         └──────────────────────────┘
```

### TradingSignal Table As Interface
- AutoQuant writes: stock code, buy price, target price, stop-loss, confidence
- External program reads: filters by target_trade_date, status='pending'
- External program updates: executed_price, actual_return, status='executed'

---

## Configuration & Environment

All external API keys and configuration stored in `.env` file (never committed):

```env
# Database
DB_TYPE=postgresql
DB_HOST=***
DB_PORT=5432
DB_NAME=autoquant
DB_USER=***
DB_PASSWORD=***

# External Databases
KIS_HOST=***
KIS_DB=***
KIS_USER=***
KIS_PASSWORD=***

# AI APIs (for stock screening)
OPENAI_API_KEY=***
OPENAI_MODEL=gpt-4
ANTHROPIC_API_KEY=***
ANTHROPIC_MODEL=claude-3-opus-20240229
GOOGLE_API_KEY=***

# Preferred AI provider (options: openai, anthropic, google)
AI_SCREENING_PROVIDER=openai

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/daily_analysis.log

# Scheduler
ANALYSIS_TIME=15:45  # 3:45 PM KST
```

---

## Success Metrics

**System is successful when:**

1. ✅ Daily execution completes by 4:00 PM (15 min window)
2. ✅ Generates 3~5 trading signals per day with >65% AI confidence
3. ✅ Buy prices are 0.5~2% above current price (achievable entry)
4. ✅ Risk/reward ratios >0.8 (at least 1:1)
5. ✅ Backtesting shows AI predictions ≥55% directional accuracy
6. ✅ Monthly signal review shows actual execution close to planned prices
7. ✅ External trading program successfully executes 80%+ of signals

---

## Document References

For complete implementation details, see:
- **AI_INTEGRATION.md**: External AI API integration, providers, prompts, cost optimization
- **IMPLEMENTATION_PLAN.md**: 6-phase implementation roadmap with code structure
- **CLAUDE.md**: Updated project overview with critical system notes
