# AutoQuant Code Structure

## Directory Layout

```
AutoQuant/
├── src/
│   ├── database/              # ORM models and database manager
│   │   ├── models.py          # SQLAlchemy models (Stock, StockPrice, Prediction, TradingSignal, MarketSnapshot, etc.)
│   │   ├── database.py        # Database class (CRUD operations, KIS connection)
│   │   └── __init__.py
│   ├── data_collection/       # Data fetching
│   │   ├── stock_collector.py # pykrx for Korean stocks
│   │   ├── financial_collector.py # FinanceDataReader
│   │   ├── market_collector.py    # Market indices
│   │   ├── mock_data.py       # Realistic test data generation
│   │   └── __init__.py
│   ├── analysis/              # Technical & prediction analysis
│   │   ├── technical_indicators.py # TechnicalIndicators class (RSI, MACD, BB, etc.)
│   │   ├── prediction_models.py    # LSTMPredictor, XGBoostPredictor
│   │   └── __init__.py
│   ├── screening/             # Market analysis (Phase 2)
│   │   ├── market_analyzer.py      # MarketAnalyzer (sentiment, momentum, 3 improvements)
│   │   ├── ai_screener.py          # AIScreener (Phase 3) - NOT YET IMPLEMENTED
│   │   ├── technical_screener.py   # TechnicalScreener (Phase 4) - NOT YET
│   │   └── __init__.py
│   ├── strategy/              # Trading strategies
│   │   ├── base_strategy.py        # BaseStrategy (abstract)
│   │   ├── sma_strategy.py         # SMAStrategy
│   │   ├── rsi_strategy.py         # RSIStrategy
│   │   └── __init__.py
│   ├── execution/             # Backtesting
│   │   ├── backtest_engine.py      # BacktestEngine (simulate historical trading)
│   │   └── __init__.py
│   ├── portfolio/             # Portfolio management
│   │   ├── portfolio_manager.py    # PortfolioManager (positions, P&L, trades)
│   │   └── __init__.py
│   └── __init__.py
├── webapp/
│   ├── app.py                 # Flask application
│   ├── templates/             # HTML templates
│   └── static/                # CSS/JS
├── tests/
│   ├── test_all_modules.py    # Integration test (all 5 historical dates)
│   ├── test_db_connection.py  # Database connectivity
│   ├── test_quick.py          # Quick test
│   ├── test_api_access.py     # API access test
│   ├── test_database.py       # Database operations
│   ├── test_webapp.py         # Web app test
│   └── user_tests/            # User acceptance tests (see USER_TEST_CHECKLIST.md)
├── scripts/
│   ├── collect_data.py        # Real data collection
│   ├── demo_with_mock_data.py # Demo
│   ├── daily_analysis.py      # Daily execution (Phase 6)
│   └── check_required_domains.py # Network check
├── config/                    # Configuration files
├── examples/                  # Usage examples
├── CLAUDE.md                  # THIS FILE - Project instructions
├── SYSTEM_DESIGN.md           # Complete 8-layer architecture
├── AI_INTEGRATION.md          # AI API setup and integration
├── IMPLEMENTATION_PLAN.md     # 6-phase roadmap
├── MARKET_ANALYSIS_IMPROVEMENTS.md # Phase 2 analysis document
├── IMPROVED_MARKET_ANALYSIS_V2.md  # Phase 2 implementation results
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables (never commit)
```

## Key Classes

### MarketAnalyzer (src/screening/market_analyzer.py)
**Purpose**: Daily market sentiment analysis (Phase 2 - COMPLETE)

Key methods:
- `analyze_market(target_date)` → MarketSnapshot (sentiment + 100+ detail fields)
- `_calculate_momentum_score()` → 5-factor momentum (0-100)
- `_judge_sentiment_v2()` → sentiment + confidence (NEW in Phase 2)
- `_calculate_technical_signals()` → RSI+MACD score (NEW)
- `_calculate_volume_strength()` → volume confidence (NEW)
- `_calculate_signal_convergence()` → signal alignment (NEW)

Output: MarketSnapshot with sentiment, confidence_level, signal_breakdown, RSI, MACD, etc.

### AIScreener (src/screening/ai_screener.py)
**Purpose**: AI-based semantic stock screening (Phase 3 - TO BE IMPLEMENTED)

Should filter 4,359 stocks → 30~40 candidates using external AI API.

Methods to implement:
- `screen_stocks(market_sentiment, stocks_df)` → List[StockCandidate]
- Uses market sentiment confidence to adjust AI analysis depth
- Integrates with OpenAI/Anthropic/Google APIs

### TechnicalScreener (src/screening/technical_screener.py)
**Purpose**: Quantitative technical scoring (Phase 4 - TO BE IMPLEMENTED)

Should rank candidates by technical setup:
- 5-factor scoring system
- Returns top 3~5 stocks

### PriceCalculator
**Purpose**: Hybrid pricing (Phase 5 - TO BE IMPLEMENTED)

Calculate for each stock:
- Buy price
- Target price (upside)
- Stop-loss price (downside)

Uses: AI predictions + support/resistance + ATR volatility

## DataFrame Schema

Standard format for all stock data:

```python
Index: DatetimeIndex
Columns: ['Open', 'High', 'Low', 'Close', 'Volume']

# After TechnicalIndicators.add_all_indicators():
+ ['SMA_5', 'SMA_20', 'RSI_14', 'MACD', 'Signal_Line', 'MACD_Histogram',
   'BB_Upper', 'BB_Middle', 'BB_Lower', 'Stochastic_K', 'Stochastic_D', ...]

# After Strategy.generate_signals():
+ ['Signal']  # 'BUY', 'SELL', 'HOLD'
```

## Data Models (SQLAlchemy ORM)

Key tables:
- **Stock**: ticker, name, sector, market_cap
- **StockPrice**: date, ticker, OHLCV
- **MarketSnapshot**: date, sentiment, momentum, kospi, investor_flows, market_trend, etc.
- **Prediction**: ticker, predict_date, lstm_target, xgboost_target, confidence
- **TradingSignal**: ticker, buy_price, target_price, stop_loss_price, ai_confidence, signal_date, status
- **BacktestResult**: strategy, ticker, return %, sharpe_ratio, max_drawdown

## Important Patterns

### Data Flow
Collection → DataFrame → Technical Analysis → Prediction/Strategy → Execution → Database

### Testing
- Unit tests in tests/
- Integration test: test_all_modules.py
- User acceptance tests: user_tests/ (see USER_TEST_CHECKLIST.md)
- Mock data: MockDataGenerator for offline testing

### Configuration
All settings in .env:
- DB_TYPE (postgresql/sqlite)
- DB credentials for KIS and AutoQuant
- AI_SCREENING_PROVIDER (openai/anthropic/google)
- API keys