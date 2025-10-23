# AutoQuant Development Commands

## Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Minimal install (if needed)
pip install -r requirements_minimal.txt
```

## Testing Commands

### Integration & Module Tests
```bash
# Run all module integration tests (MOST COMMON)
python tests/test_all_modules.py

# Quick test (basic functionality)
python tests/test_quick.py

# Database connectivity test
python tests/test_db_connection.py

# Web app test
python tests/test_webapp.py

# Database operations test
python tests/test_database.py

# API access test
python tests/test_api_access.py
```

### User Acceptance Tests (Detailed in USER_TEST_CHECKLIST.md)
```bash
# KIS data collection test
python tests/user_tests/test_01_kis_data_collection.py

# Daily OHLCV test
python tests/user_tests/test_02_daily_ohlcv.py

# Market analysis test (Phase 2 - JUST COMPLETED)
python tests/user_tests/test_03_market_analysis.py

# See tests/user_tests/README.md for full list
```

## Running the Application

### Web Dashboard (Flask)
```bash
cd webapp
python app.py
# Access: http://localhost:5000
```

### Scripts

#### Real Data Collection
```bash
python scripts/collect_data.py
# Requires: pykrx network access
```

#### Demo with Mock Data
```bash
python scripts/demo_with_mock_data.py
# No network required - good for testing
```

#### Check Network Connectivity
```bash
python scripts/check_required_domains.py
# Verifies access to: krx.co.kr, finance.naver.com, yahoo.com
```

#### Daily Analysis (Post-Market)
```bash
python scripts/daily_analysis.py
# Generates trading signals for next trading day
# Typically runs 3:45 PM KST
```

## Development Workflows

### Add New Technical Indicator
```bash
# 1. Edit src/analysis/technical_indicators.py
# 2. Add method: calculate_xxx(df, **kwargs)
# 3. Add to add_all_indicators() if should be default
# 4. Test: python tests/test_quick.py
```

### Add New Strategy
```bash
# 1. Create src/strategy/my_strategy.py
# 2. Inherit from BaseStrategy
# 3. Implement generate_signals(df) method
# 4. Export in src/strategy/__init__.py
# 5. Test with BacktestEngine
```

### Database Migration (SQLite ↔ PostgreSQL)
```bash
# 1. Edit .env: DB_TYPE=postgresql (or sqlite)
# 2. Update DB credentials
# 3. Run: python tests/test_db_connection.py
# 4. Data transfer: Query old DB → Insert new DB
```

## Git Workflow
```bash
# Check status
git status

# Create feature branch (for new work)
git checkout -b feature/phase-3-ai-screening

# Commit with meaningful message
git add src/
git commit -m "Implement Phase 3: AIScreener with multi-provider support"

# Push feature branch
git push origin feature/phase-3-ai-screening
```

## Debugging Commands

### Check Database Connection
```bash
python tests/test_db_connection.py
```

### Test with Mock Data
```bash
python scripts/demo_with_mock_data.py
```

### Quick Smoke Test
```bash
python tests/test_quick.py
```

### View Logs
```bash
# Logs are output to console by loguru
# Search logs in terminal output for errors
```

## Common Development Tasks

### Phase 2: Market Analysis (COMPLETE)
```bash
# Test market analysis improvements
python tests/user_tests/test_03_market_analysis.py

# View results
python tests/test_all_modules.py
```

### Phase 3: AI Screening (NEXT)
```bash
# First: Ensure .env has AI_SCREENING_PROVIDER set
# Implementation: src/screening/ai_screener.py
# Test: python tests/test_quick.py
```

### Phase 4: Technical Screening
```bash
# Implementation: src/screening/technical_screener.py
# Should rank Phase 3 candidates by technical setup
```

### Phase 5: Price Calculation & AI Prediction
```bash
# Prediction: src/analysis/prediction_models.py
# Pricing: src/analysis/price_calculator.py (to create)
# Backtesting: python tests/test_quick.py
```

### Phase 6: Daily Execution
```bash
# Script: scripts/daily_analysis.py
# Orchestrates all 5 previous phases
# Generates TradingSignal table entries
```

## Environment Variables (.env)

Essential variables:
```bash
# Database
DB_TYPE=postgresql  # or sqlite
DB_HOST=REDACTED_HOST
DB_PORT=5432
DB_NAME=kis_data
DB_USER=***
DB_PASSWORD=***

# AI Screening (Phase 3)
AI_SCREENING_PROVIDER=openai  # or anthropic, google
OPENAI_API_KEY=sk-***
ANTHROPIC_API_KEY=sk-ant-***
GOOGLE_API_KEY=***

# Logging
LOG_LEVEL=INFO  # or DEBUG, WARNING, ERROR

# App
FLASK_ENV=development
FLASK_DEBUG=True
```

## Performance Tips

- Use MockDataGenerator for offline development (no network delays)
- Run test_quick.py for fast feedback (not full integration)
- Use sqlite in .env for testing (faster than PostgreSQL)
- Batch operations: collect 30+ days at once, not daily

## Reset & Cleanup

```bash
# Clear .serena cache (project memories)
rm -rf .serena/

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Reset database (careful!)
# Edit .env to point to new db, run tests to recreate schema
```