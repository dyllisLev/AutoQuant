# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AutoQuant** is an **AI-based pre-market analysis system** for Korean stock markets that generates daily trading signals for the next trading day.

**System Identity** (CRITICAL - READ FIRST):
This is a **signal generation and analysis tool**, NOT a trading execution program. AutoQuant analyzes markets, screens stocks, predicts prices, and calculates buy/target/stop-loss prices. A **separate external program** reads the `TradingSignal` database table and executes actual trades via KIS/Kiwoom APIs.

**Key Features**:
- Two-layer intelligent filtering: AI-based semantic screening (4,359 → 30~40) + technical quantitative screening (30~40 → 3~5)
- External AI API integration: Uses GPT-4, Claude, or Gemini for semantic market analysis
- AI price prediction: LSTM and XGBoost models predict 7-day forward prices
- Hybrid trading price calculation: AI predictions + support/resistance + ATR-based volatility
- Daily automated execution: Post-market analysis generates signals for next trading day
- Backtesting for validation: Tests AI prediction accuracy (NOT strategy backtesting)
- KIS PostgreSQL integration: Reads 4,359 Korean stock daily OHLCV data

**Status**:
- ✅ Phase 1: Database schema complete (TradingSignal, MarketSnapshot tables)
- ✅ Phase 2: Market analysis with comprehensive momentum analysis (COMPLETE)
- ✅ Phase 3: AI-based stock screening (COMPLETE - 35 candidates with GPT-4)
- ✅ Phase 4: Technical screening (COMPLETE - 5-factor scoring system)
- ✅ Phase 5: Trading price calculation (COMPLETE - R/R 2.0 guaranteed signals)
- ✅ Phase 6: Daily execution script (COMPLETE - daily_analysis.py)
- ✅ **Web Dashboard**: Responsive mobile/desktop web app (COMPLETE - http://localhost:5000)

---

## 🔴 **CRITICAL TESTING RULES (MANDATORY)**

**CLAUDE MUST FOLLOW THESE RULES AT ALL TIMES:**

### Rule 1: 절대 모의 데이터를 사용하지 마세요
- ❌ MockDataGenerator 사용 금지
- ❌ 임의로 만든 주식 코드(100010~104358) 사용 금지
- ✅ **반드시** KIS PostgreSQL DB에서 실제 4,359개 한국 주식 조회
- ✅ 실제 주식 코드: 005930(삼성전자), 000660(SK하이닉스) 등 실제 종목만
- ✅ `database.get_available_symbols_from_kis()` 사용

### Rule 2: 오류는 임의대로 넘어가지 마세요
- ❌ 오류 발생 시 무시하고 진행하지 않기
- ❌ "일단 테스트라도 통과시키자" 마음으로 우회 금지
- ✅ 오류가 발생하면 **반드시 사용자에게 확인 받기**
- ✅ 원인을 파악하고 해결할 때까지 멈추기
- ✅ DB 연결 실패 → 사용자 확인 필요
- ✅ API 호출 실패 → 원인 파악 후 재시도

### Rule 3: 진행율을 우선순위에 두지 마세요
- ❌ "빨리 완료해야 한다"는 생각으로 타협 금지
- ❌ 테스트 통과 > 실제 구현 의식 배제
- ✅ **실제 구현**이 모든 우선순위의 최상위
- ✅ 진행율이 0%라도 실제 데이터로 올바르게 구현
- ✅ 가짜 테스트 통과 > 실제 실패 구현

### Rule 4: 실제 플로우를 따라가세요
- ✅ SYSTEM_DESIGN.md의 8-layer 플로우 정확히 따르기
- ✅ 각 phase가 실제 데이터로 작동하는지 확인
- ✅ 테스트 → 프로덕션 실제 동작 동일해야 함
- ✅ "모의 테스트에서 통과했는데 실제는 안됨" 절대 금지

---

## 📚 MANDATORY DOCUMENTATION (READ BEFORE CODING)

**YOU MUST READ AND UNDERSTAND THESE DOCUMENTS BEFORE STARTING ANY IMPLEMENTATION:**

### 1. **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)** - Complete System Architecture
   - **8-layer data flow diagram**: Data Collection → Market Analysis → AI Screening → Technical Screening → AI Prediction → Price Calculation → Signal Persistence → External Trading
   - **Daily execution example**: Step-by-step flow with actual values
   - **Database schema**: New TradingSignal and MarketSnapshot tables
   - **Module overview**: Purpose and key methods for each component
   - **Key concepts**: Two-layer filtering rationale, backtesting scope (prediction validation only)
   - **Start here to understand the complete system architecture**

### 2. **[AI_INTEGRATION.md](AI_INTEGRATION.md)** - External AI API Integration
   - **Supported providers**: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini)
   - **Setup and configuration**: .env file, API keys, cost tracking
   - **Prompt engineering**: Stock screening and portfolio analysis prompts
   - **Complete AIScreener implementation**: Multi-provider support, error handling, fallbacks
   - **Cost optimization**: Budget tracking, provider switching strategies
   - **Testing and validation**: Example prompts and test cases
   - **Essential for AI integration work**

### 3. **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 6-Phase Implementation Roadmap
   - **Phase 1 (1 day)**: Database schema extension (TradingSignal, MarketSnapshot models) ✅
   - **Phase 2 (2 days)**: Market analysis module (MarketAnalyzer) ✅
   - **Phase 3 (3 days)**: AI-based stock screening (AIScreener with multi-provider support)
   - **Phase 4 (2 days)**: Technical analysis screening (TechnicalScreener with 5-factor scoring)
   - **Phase 5 (3 days)**: Trading price calculation (PriceCalculator with hybrid pricing)
   - **Phase 6 (2 days)**: Daily execution script (daily_analysis.py orchestrator)
   - **Estimated total**: 13 working days (~2-3 weeks)
   - **Follow this plan sequentially for implementation**

### 4. **[MOMENTUM_ANALYSIS_IMPROVEMENTS.md](MOMENTUM_ANALYSIS_IMPROVEMENTS.md)** - Phase 2 Comprehensive Analysis
   - **Problem analysis**: Why original 3-factor momentum was insufficient
   - **5-factor momentum model**: Index trend, investor flows, investor balance, sector momentum, market breadth
   - **4-signal sentiment judgment**: Momentum + investor flow + market trend + KOSPI technical signals
   - **Test results**: Phase 2 complete with 100% success on 5 historical dates
   - **Key improvements**: Multi-investor analysis, reverse signals for retail investors, market structure analysis

---

## ⚠️ CRITICAL SYSTEM NOTES (REMEMBER THESE)

**1. System Scope: PRE-MARKET ANALYSIS ONLY**
   - ✅ Analyzes markets and generates trading signals
   - ✅ Stores signals in TradingSignal database table
   - ❌ Does NOT execute trades (external program does this)
   - ❌ Does NOT manage real portfolio (external program does this)

**2. Two-Layer Filtering Architecture (MUST UNDERSTAND)**
   - **Layer 1 (AI-Based, 4,359 → 30~40)**: External AI API analyzes market context + all stocks, returns 30~40 semantic candidates
   - **Layer 2 (Technical Quantitative, 30~40 → 3~5)**: TechnicalIndicators scores each candidate, returns top 3~5 with highest technical setup
   - **Why two layers?**: Reduces computational cost by 99.8%, combines semantic wisdom (AI) with quantitative precision (technical)

**3. Backtesting Scope: PREDICTION VALIDATION ONLY**
   - ✅ Use backtesting to validate LSTM/XGBoost prediction accuracy
   - ✅ Measure directional accuracy % and MAPE (error magnitude)
   - ✅ Validate confidence score calibration
   - ❌ Do NOT use backtesting for daily strategy execution
   - ❌ Do NOT measure strategy performance metrics (this system doesn't execute)
   - ❌ Backtesting results don't apply to real trading (separate concern)

**4. External AI APIs (MANDATORY FOR SCREENING)**
   - Each screening call uses external AI (costs ~$0.01-0.06 per call)
   - Typical costs: ~$0.03-0.90 per month (1 call/day)
   - Configure preferred provider in .env: `AI_SCREENING_PROVIDER=openai|anthropic|google`
   - API keys required: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY

**5. Daily Execution (3:45 PM KST POST-MARKET)**
   - Script: `scripts/daily_analysis.py`
   - Runs daily after market close (3:30 PM) → 3:45 PM start
   - Generates 3~5 trading signals for next trading day
   - Stores in TradingSignal table with: buy price, target price, stop-loss, confidence, prediction
   - External trader reads signals and executes trades

**6. Database Extensions (Phase 1 COMPLETE)**
   - ✅ TradingSignal table (stock_id, buy_price, target_price, stop_loss_price, ai_confidence, predicted_return, status, ...)
   - ✅ MarketSnapshot table (date, kospi_close, investor_flows, sector_performance, market_trend, sentiment, ...)
   - ✅ Both tables operational and integrated

**7. Web Dashboard (COMPLETE)**
   - **URL**: http://localhost:5000 (http://192.168.0.77:5000 for network access)
   - **Backend**: Flask 3.1.2 with 6 API endpoints
   - **Frontend**: Responsive design (Tailwind CSS + Alpine.js)
   - **Features**:
     - 6 pages: Dashboard, Trading Signals, AI Screening, Technical Analysis, Market Analysis, History
     - Mobile-responsive (< 1024px: bottom nav, >= 1024px: top menu)
     - Real-time data from PostgreSQL
     - Glass morphism UI design
   - **Access**: Mobile and desktop browsers
   - **Server**: `python3 webapp/app_new.py` (runs on port 5000)

---

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
# Start web dashboard (NEW - responsive mobile/desktop UI)
cd webapp
python app_new.py
# Access at http://localhost:5000 (local) or http://192.168.0.77:5000 (network)

# Or use the startup script
./webapp/start_webapp.sh

# Run daily analysis (Phase 1-5: generates 3-5 trading signals)
python scripts/daily_analysis.py

# Collect real data (requires network access)
python scripts/collect_data.py

# Check network connectivity
python scripts/check_required_domains.py

# Restart web server
./restart_webapp.sh
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

## ⚠️ **CRITICAL INSTRUCTION RULES**

### Rule 1: Follow Explicit Instructions Only
**DO NOT**:
- Assume or infer what the user wants beyond what was explicitly stated
- Run different tests/commands than what was specifically requested
- Execute "comprehensive" or "full" operations unless explicitly asked
- Make assumptions about scope (e.g., "they probably want everything")

**DO**:
- Execute ONLY what was explicitly requested
- Ask for clarification if instructions are ambiguous
- Read IDE selections and context clues carefully
- Honor the specific test/file mentioned by the user

**Example of Violation**:
- User: "Run test_05_trading_signals.py"
- Wrong Response: Running test_all_modules.py instead
- Correct Response: Running only test_05_trading_signals.py

### Rule 2: Pay Attention to IDE Selection Context
When user highlights/selects a specific section (e.g., "2.3 매매 신호 생성"), that IS the instruction
**DO**:
- Check the `<ide_selection>` tags in system reminders
- Use IDE selection as the primary guide for what to execute
- Read the selected content carefully before taking action

**Example of Violation**:
- IDE Selection: "2.3 매매 신호 생성"
- Wrong: Concluding this means run test_quick.py
- Correct: Find and run the specific test for section 2.3

### Rule 3: Understand "Last Test Executed"
When asked "run the last test", identify it from:
1. IDE selection context (highest priority)
2. Document's "실제 결과" section showing most recent completion
3. Timestamped entries (latest date = most recent)

**DO NOT** guess or assume what the "last test" was

### Rule 4: Request Clarification When Ambiguous
If instructions could mean multiple things:
- Stop and ask for clarification
- Don't proceed with guesses
- Show the user what you understood from their request

---

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
