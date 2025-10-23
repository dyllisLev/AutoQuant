# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AutoQuant** is an AI-powered automated trading system for Korean stock markets, featuring:
- Data collection from Korean Exchange (pykrx) and global sources
- PostgreSQL database integration with KIS system (4,359 Korean stocks)
- Technical analysis with 10+ indicators
- AI predictions using LSTM and XGBoost models
- Trading strategies (SMA crossover, RSI)
- Backtesting engine with performance metrics
- Portfolio management
- Flask web dashboard

**Status**: Production-ready. All core modules implemented and tested.

## Development Commands

### Environment Setup
```bash
# IMPORTANT: Always use virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run all module integration tests
python tests/test_all_modules.py

# Test database connectivity (PostgreSQL/KIS)
python tests/test_db_connection.py

# Test web app
python tests/test_webapp.py

# Test database operations
python tests/test_database.py

# Quick test
python tests/test_quick.py

# API access test
python tests/test_api_access.py

# User acceptance tests (based on USER_TEST_CHECKLIST.md)
python tests/user_tests/test_01_kis_data_collection.py
python tests/user_tests/test_02_daily_ohlcv.py
# See tests/user_tests/README.md for full list
```

### Running the Application
```bash
# Start web dashboard
cd webapp
python app.py
# Access at http://localhost:5000

# Collect real data (requires network access)
python scripts/collect_data.py

# Demo with mock data
python scripts/demo_with_mock_data.py

# Check network connectivity
python scripts/check_required_domains.py
```

## Architecture

### Database Layer (`src/database/`)
- **Two-database architecture**:
  - **KIS PostgreSQL** (read-only): `daily_ohlcv` table with 4,359 Korean stocks
  - **AutoQuant tables** (read/write): Stock, StockPrice, Prediction, Trade, Portfolio, BacktestResult
- **Configuration**: `.env` file controls database type (`DB_TYPE=postgresql` or `sqlite`)
- **SQLAlchemy ORM**: All models defined in `models.py`
- **Key methods**:
  - `get_available_symbols_from_kis()`: Query KIS database for available stocks
  - `get_daily_ohlcv_from_kis(symbol, start_date, end_date)`: Fetch KIS OHLCV data
  - Standard CRUD operations for AutoQuant tables

**Important**: KIS database is at ***REDACTED_HOST***. Credentials in `.env` (never commit).

### Data Collection (`src/data_collection/`)
- **Collectors**:
  - `stock_collector.py`: pykrx for Korean stocks
  - `financial_collector.py`: FinanceDataReader for global data
  - `market_collector.py`: Market indices
- **Mock data**: `mock_data.py` generates realistic test data (OHLCV with random walks)
- **Network requirements**: Requires access to krx.co.kr, finance.yahoo.com, finance.naver.com

### Analysis Layer (`src/analysis/`)
- **Technical indicators** (`technical_indicators.py`):
  - Moving averages: SMA, EMA
  - Momentum: RSI, Stochastic, MACD
  - Volatility: Bollinger Bands, ATR
  - Volume: OBV
  - Use `TechnicalIndicators.add_all_indicators(df)` to compute all at once

- **AI Models** (`prediction_models.py`):
  - `LSTMPredictor`: Deep learning time-series predictor
  - `XGBoostPredictor`: Gradient boosting model
  - Both follow pattern: `prepare_data()` → `train()` → `predict_future()`

### Strategy Layer (`src/strategy/`)
- **Base class**: `BaseStrategy` (abstract) - all strategies inherit from this
- **Implemented strategies**:
  - `SMAStrategy`: Golden/death cross (short/long period crossover)
  - `RSIStrategy`: Overbought (>70) / oversold (<30) levels
- **Signal format**: Adds 'Signal' column with values: 'BUY', 'SELL', 'HOLD'

### Execution Layer (`src/execution/`)
- **BacktestEngine**:
  - Simulates historical trading
  - Tracks equity curve, trades, positions
  - Returns metrics: total_return, sharpe_ratio, max_drawdown, win_rate
  - Handles multiple stocks simultaneously

### Portfolio Layer (`src/portfolio/`)
- **PortfolioManager**:
  - Tracks positions (quantity, avg_buy_price)
  - Calculates P&L
  - Manages capital allocation
  - Records trade history

### Web Dashboard (`webapp/`)
- **Flask app** (`app.py`):
  - Routes: `/`, `/api/stock/<ticker>`, `/api/analysis/<ticker>`, `/api/predict/<ticker>`, `/api/backtest`, `/api/portfolio`
  - Templates in `templates/`
  - Uses mock data by default for demo purposes
  - Real-time stock queries, technical analysis, AI predictions, backtesting

## Key Patterns

### Data Flow
1. **Collection**: Data collectors → pandas DataFrame (OHLCV format)
2. **Storage**: DataFrame → Database (via SQLAlchemy models)
3. **Analysis**: DataFrame → Technical indicators → Enhanced DataFrame
4. **Prediction**: Enhanced DataFrame → AI models → Future predictions
5. **Strategy**: Enhanced DataFrame → Strategy → Signals DataFrame
6. **Execution**: Signals + Historical data → BacktestEngine → Performance metrics

### DataFrame Schema
All stock data follows this schema:
```python
Index: DatetimeIndex
Columns: ['Open', 'High', 'Low', 'Close', 'Volume']
# After technical indicators:
+ ['SMA_5', 'SMA_20', 'RSI_14', 'MACD', 'Signal_Line', 'MACD_Histogram',
   'BB_Upper', 'BB_Middle', 'BB_Lower', 'Stochastic_K', 'Stochastic_D', ...]
# After strategy:
+ ['Signal']  # 'BUY', 'SELL', or 'HOLD'
```

### Environment Variables (.env)
Critical configuration in `.env`:
- `DB_TYPE`: postgresql or sqlite
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials
- `DB_PATH`: SQLite file path (if using SQLite)
- `LOG_LEVEL`: Logging verbosity

**Security**: Never commit `.env`. Use `.env.example` as template.

### Testing Philosophy
- Each module has standalone tests in `tests/`
- `test_all_modules.py` runs full integration test
- Mock data used when network unavailable
- Tests verify: data generation, indicators, predictions, strategies, backtesting, database

## Common Workflows

### Adding a New Strategy
1. Create new file in `src/strategy/` (e.g., `my_strategy.py`)
2. Inherit from `BaseStrategy`
3. Implement `generate_signals(df)` method
4. Return DataFrame with 'Signal' column added
5. Export in `src/strategy/__init__.py`
6. Test with BacktestEngine

### Adding a New Technical Indicator
1. Add static method to `TechnicalIndicators` class
2. Follow pattern: `calculate_xxx(df, column='Close', period=N)`
3. Return pd.Series
4. Add to `add_all_indicators()` if should be included by default

### Database Migration (SQLite ↔ PostgreSQL)
- Change `DB_TYPE` in `.env`
- Run `db.create_tables()` to initialize new schema
- Data migration: Query from old DB, insert into new DB via Database class methods

## Important Notes

- **Korean stock tickers**: 6-digit codes (e.g., '005930' for Samsung)
- **Date format**: Use datetime objects or 'YYYY-MM-DD' strings
- **Logging**: Uses `loguru` - all modules import and use logger
- **Error handling**: Collectors have auto-retry logic for network failures
- **Capital**: Default initial capital is 10,000,000 KRW in backtesting
- **KIS data update**: Daily after market close (15:30 KST)

## File Organization

```
AutoQuant/
├── src/                          # Core modules
│   ├── data_collection/          # Data fetching and mock generation
│   ├── database/                 # ORM models and DB manager
│   ├── analysis/                 # Technical indicators and AI models
│   ├── strategy/                 # Trading strategies
│   ├── execution/                # Backtesting engine
│   └── portfolio/                # Portfolio manager
├── webapp/                       # Flask web dashboard
│   ├── app.py                    # Main Flask application
│   └── templates/                # HTML templates
├── tests/                        # Test suites
│   ├── user_tests/               # User acceptance tests (USER_TEST_CHECKLIST.md)
│   ├── test_all_modules.py       # Integration tests
│   ├── test_db_connection.py     # Database connectivity test
│   ├── test_quick.py             # Quick test
│   └── ...                       # Other test files
├── scripts/                      # Utility scripts and demos
│   ├── collect_data.py           # Real data collection
│   ├── demo_with_mock_data.py    # Demo with mock data
│   └── check_required_domains.py # Network connectivity check
├── config/                       # Configuration files
├── examples/                     # Usage examples
├── .env                          # Environment variables (DO NOT COMMIT)
└── requirements.txt              # Python dependencies
```

## External Dependencies

**Critical**:
- `pykrx`: Korean Exchange data (requires network access to krx.co.kr)
- `psycopg2-binary`: PostgreSQL driver (for KIS database)
- `sqlalchemy`: ORM layer
- `pandas`, `numpy`: Data manipulation
- `scikit-learn`, `xgboost`: ML models
- `flask`: Web framework

**Optional** (for real-time trading):
- Exchange API integration (future roadmap)

## Debugging Tips

- **Database connection issues**: Run `python test_db_connection.py` to verify connectivity
- **Missing indicators**: Ensure `TechnicalIndicators.add_all_indicators()` called before strategy
- **No signals generated**: Check if DataFrame has enough data (strategies need minimum periods)
- **Network errors in data collection**: Use `MockDataGenerator` for testing without network
- **Import errors**: Verify `sys.path` includes project root (tests do this automatically)

## Documentation References

- USER_TEST_CHECKLIST.md: Comprehensive testing guide for all features
- DATABASE_SETUP.md: PostgreSQL setup and KIS data access
- INTEGRATION_SUMMARY.md: PostgreSQL integration details
- USER_GUIDE.md: Detailed usage guide
- NETWORK_REQUIREMENTS.md: Required network access for data collection
- TESTING_RESULTS.md: Test results and performance benchmarks
