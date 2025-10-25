# Database Schema Analysis for Step-by-Step Monitoring

**Date**: 2025-10-25
**Purpose**: Design comprehensive database schema to capture all analysis steps for web monitoring

---

## Current Data Flow Analysis

### Phase 1: Data Collection (LAYER 1)
**Input**: KIS PostgreSQL (4,359 stocks)
**Output Data**:
```python
{
    'date': '2025-10-25',
    'total_stocks': 4359,
    'stocks_with_data': 4359,
    'data_quality': {
        'missing_ohlcv': 0,
        'invalid_prices': 0,
        'zero_volume': 15
    }
}
```

### Phase 2: Market Analysis (LAYER 2)
**Output Data** (MarketAnalyzer):
```python
{
    'analysis_date': '2025-10-25',
    'kospi': {
        'close': 2467.23,
        'change_pct': 0.8,
        'volume': 542000000,
        'trend': 'UPTREND'
    },
    'kosdaq': {
        'close': 714.56,
        'change_pct': -0.3,
        'volume': 892000000,
        'trend': 'NEUTRAL'
    },
    'investor_flow': {
        'foreign': {'net_buy': 45200000000, 'buy_ratio': 42.3},
        'institution': {'net_buy': 12300000000, 'buy_ratio': 35.7},
        'retail': {'net_buy': -57500000000, 'buy_ratio': 22.0}
    },
    'sector_performance': [
        {'sector': 'Technology', 'change_pct': 1.2, 'volume_ratio': 1.5},
        {'sector': 'Finance', 'change_pct': -0.3, 'volume_ratio': 0.8},
        # ... 10 sectors total
    ],
    'momentum_score': 65.5,
    'market_sentiment': 'BULLISH',
    'breadth': {
        'advancing': 1234,
        'declining': 987,
        'unchanged': 234,
        'new_highs': 45,
        'new_lows': 12
    }
}
```

### Phase 3: AI Screening (LAYER 3)
**Input**: 4,359 stocks + market analysis
**Output Data** (AIScreener):
```python
{
    'screening_date': '2025-10-25',
    'ai_provider': 'openai',
    'model': 'gpt-4',
    'total_input_stocks': 4359,
    'selected_candidates': 40,
    'execution_time': 12.5,  # seconds
    'api_cost': 0.045,  # USD
    'candidates': [
        {
            'stock_code': '005930',
            'company_name': '삼성전자',
            'ai_score': 92.5,
            'ai_reasoning': 'Strong momentum in semiconductor sector...',
            'rank': 1,
            'mentioned_factors': ['sector_strength', 'foreign_buying', 'technical_setup']
        },
        # ... 40 candidates total
    ],
    'prompt_used': 'Analyze Korean stock market...',
    'response_summary': 'Selected 40 stocks based on...'
}
```

### Phase 4: Technical Screening (LAYER 4)
**Input**: 40 AI candidates
**Output Data** (TechnicalScreener):
```python
{
    'screening_date': '2025-10-25',
    'input_candidates': 40,
    'final_selections': 4,
    'execution_time': 2.3,  # seconds
    'selections': [
        {
            'stock_code': '018000',
            'company_name': '유니슨',
            'current_price': 1210,
            'technical_scores': {
                'sma_score': 20,  # out of 20
                'rsi_score': 13,  # out of 15
                'macd_score': 15,  # out of 15
                'bb_score': 8,    # out of 10
                'volume_score': 8, # out of 10
                'final_score': 64  # out of 70
            },
            'indicators': {
                'SMA_5': 1091,
                'SMA_20': 1085,
                'SMA_60': 980,
                'RSI_14': 65.39,
                'MACD': 15.23,
                'MACD_Signal': 12.45,
                'MACD_Histogram': 2.78,
                'BB_Upper': 1350,
                'BB_Middle': 1200,
                'BB_Lower': 1050,
                'Volume_Ratio': 1.25,
                'ATR': 62
            },
            'rank': 1,
            'selection_reason': 'Strong technical setup with all indicators aligned'
        },
        # ... 4 selections total
    ]
}
```

### Phase 5: Price Calculation (LAYER 5-6)
**Input**: 4 final selections
**Output Data** (PriceCalculator):
```python
{
    'calculation_date': '2025-10-25',
    'target_trade_date': '2025-10-28',
    'total_signals': 4,
    'execution_time': 0.8,  # seconds
    'signals': [
        {
            'stock_code': '018000',
            'company_name': '유니슨',
            'current_price': 1210,
            'buy_price': 1220,
            'target_price': 1360,
            'stop_loss_price': 1090,
            'predicted_return': 11.25,
            'risk_reward_ratio': 1.0,
            'ai_confidence': 60,
            'support_resistance': {
                'support': 1000,
                'resistance': 1300,
                'pivot': 1184,
                'r1': 1250,
                's1': 1100,
                'high_60d': 1321,
                'low_60d': 931
            },
            'volatility': {
                'atr': 62,
                'atr_percent': 5.12,
                'volatility_rank': 'MEDIUM'
            },
            'calculation_details': {
                'buy_premium_pct': 0.83,
                'buy_premium_reason': 'Neutral RSI (65.39)',
                'target_method': 'Conservative (min of AI/Resistance/Technical)',
                'stop_method': 'ATR-based (2*ATR below buy)',
                'rr_adjustment': 'Auto-adjusted from 0.55 to 1.0'
            }
        },
        # ... 4 signals total
    ]
}
```

---

## Proposed Database Schema

### 1. **AnalysisRun** (분석 실행 기록)
**Purpose**: Track each complete analysis run (daily execution)

```sql
CREATE TABLE analysis_run (
    id SERIAL PRIMARY KEY,
    run_date DATE NOT NULL,
    target_trade_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',  -- running, completed, failed
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_duration_seconds DECIMAL,

    -- Phase completion tracking
    phase1_completed BOOLEAN DEFAULT FALSE,
    phase2_completed BOOLEAN DEFAULT FALSE,
    phase3_completed BOOLEAN DEFAULT FALSE,
    phase4_completed BOOLEAN DEFAULT FALSE,
    phase5_completed BOOLEAN DEFAULT FALSE,

    -- Error tracking
    error_message TEXT,
    error_phase VARCHAR(20),

    -- Summary metrics
    total_stocks_analyzed INTEGER,
    ai_candidates_count INTEGER,
    technical_selections_count INTEGER,
    final_signals_count INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analysis_run_date ON analysis_run(run_date);
CREATE INDEX idx_analysis_run_status ON analysis_run(status);
```

### 2. **MarketSnapshot** (시장 분석 결과 - Phase 2)
**Purpose**: Daily market condition analysis

```sql
CREATE TABLE market_snapshot (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,

    -- KOSPI/KOSDAQ
    kospi_close DECIMAL NOT NULL,
    kospi_change_pct DECIMAL NOT NULL,
    kospi_volume BIGINT,
    kospi_trend VARCHAR(20),  -- UPTREND, DOWNTREND, NEUTRAL

    kosdaq_close DECIMAL NOT NULL,
    kosdaq_change_pct DECIMAL NOT NULL,
    kosdaq_volume BIGINT,
    kosdaq_trend VARCHAR(20),

    -- Investor flows (KRW)
    foreign_net_buy BIGINT,
    foreign_buy_ratio DECIMAL,
    institution_net_buy BIGINT,
    institution_buy_ratio DECIMAL,
    retail_net_buy BIGINT,
    retail_buy_ratio DECIMAL,

    -- Market breadth
    advancing_count INTEGER,
    declining_count INTEGER,
    unchanged_count INTEGER,
    new_highs_52w INTEGER,
    new_lows_52w INTEGER,

    -- Momentum & Sentiment
    momentum_score DECIMAL,  -- 0-100
    market_sentiment VARCHAR(20),  -- BULLISH, BEARISH, NEUTRAL

    -- Sector performance (JSON)
    sector_performance JSON,  -- [{sector, change_pct, volume_ratio}, ...]

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_market_snapshot_date ON market_snapshot(snapshot_date);
CREATE INDEX idx_market_snapshot_run ON market_snapshot(analysis_run_id);
```

### 3. **AIScreeningResult** (AI 스크리닝 결과 - Phase 3)
**Purpose**: Track AI screening process and selected candidates

```sql
CREATE TABLE ai_screening_result (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,
    screening_date DATE NOT NULL,

    -- AI provider info
    ai_provider VARCHAR(50),  -- openai, anthropic, google
    ai_model VARCHAR(50),     -- gpt-4, claude-3, gemini-pro

    -- Execution metrics
    total_input_stocks INTEGER NOT NULL,
    selected_count INTEGER NOT NULL,
    execution_time_seconds DECIMAL,
    api_cost_usd DECIMAL,

    -- Prompt & Response
    prompt_text TEXT,
    response_text TEXT,
    response_summary TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_screening_run ON ai_screening_result(analysis_run_id);
```

### 4. **AICandidate** (AI 선정 종목 상세 - Phase 3)
**Purpose**: Individual stock candidates selected by AI

```sql
CREATE TABLE ai_candidate (
    id SERIAL PRIMARY KEY,
    ai_screening_id INTEGER REFERENCES ai_screening_result(id) ON DELETE CASCADE,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,

    stock_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(100),

    -- AI evaluation
    ai_score DECIMAL,  -- 0-100
    ai_reasoning TEXT,
    rank_in_batch INTEGER,

    -- Mentioned factors (JSON array)
    mentioned_factors JSON,  -- ['sector_strength', 'foreign_buying', ...]

    -- Stock data at screening time
    current_price DECIMAL,
    market_cap BIGINT,
    volume BIGINT,
    sector VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_candidate_screening ON ai_candidate(ai_screening_id);
CREATE INDEX idx_ai_candidate_stock ON ai_candidate(stock_code);
```

### 5. **TechnicalScreeningResult** (기술적 스크리닝 결과 - Phase 4)
**Purpose**: Track technical analysis screening process

```sql
CREATE TABLE technical_screening_result (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,
    screening_date DATE NOT NULL,

    input_candidates_count INTEGER NOT NULL,
    final_selections_count INTEGER NOT NULL,
    execution_time_seconds DECIMAL,

    -- Scoring thresholds used
    min_final_score DECIMAL,  -- Minimum score to pass (e.g., 50)
    max_selections INTEGER,   -- Maximum stocks to select (e.g., 5)

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tech_screening_run ON technical_screening_result(analysis_run_id);
```

### 6. **TechnicalSelection** (기술적 선정 종목 상세 - Phase 4)
**Purpose**: Individual stocks selected by technical screening

```sql
CREATE TABLE technical_selection (
    id SERIAL PRIMARY KEY,
    tech_screening_id INTEGER REFERENCES technical_screening_result(id) ON DELETE CASCADE,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,

    stock_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(100),
    current_price DECIMAL NOT NULL,

    -- Technical scores (5-factor system)
    sma_score DECIMAL,      -- out of 20
    rsi_score DECIMAL,      -- out of 15
    macd_score DECIMAL,     -- out of 15
    bb_score DECIMAL,       -- out of 10
    volume_score DECIMAL,   -- out of 10
    final_score DECIMAL,    -- out of 70

    -- Technical indicators (JSON for all 16 indicators)
    indicators JSON,  -- {SMA_5, SMA_20, RSI_14, MACD, ...}

    rank_in_batch INTEGER,
    selection_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tech_selection_screening ON technical_selection(tech_screening_id);
CREATE INDEX idx_tech_selection_stock ON technical_selection(stock_code);
```

### 7. **TradingSignal** (최종 매매 신호 - Phase 5)
**Purpose**: Final trading signals with calculated prices

```sql
CREATE TABLE trading_signal (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER REFERENCES analysis_run(id) ON DELETE CASCADE,
    tech_selection_id INTEGER REFERENCES technical_selection(id),

    stock_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(100),

    -- Analysis & Trade dates
    analysis_date DATE NOT NULL,
    target_trade_date DATE NOT NULL,

    -- Prices
    current_price DECIMAL NOT NULL,
    buy_price DECIMAL NOT NULL,
    target_price DECIMAL NOT NULL,
    stop_loss_price DECIMAL NOT NULL,

    -- Performance metrics
    predicted_return DECIMAL,      -- Expected profit %
    risk_reward_ratio DECIMAL,     -- Target profit / Stop loss
    ai_confidence INTEGER,         -- 0-100

    -- Support/Resistance levels
    support_level DECIMAL,
    resistance_level DECIMAL,
    pivot_point DECIMAL,
    r1_level DECIMAL,
    s1_level DECIMAL,
    high_60d DECIMAL,
    low_60d DECIMAL,

    -- Volatility
    atr DECIMAL,
    atr_percent DECIMAL,
    volatility_rank VARCHAR(20),  -- LOW, MEDIUM, HIGH

    -- Calculation details (JSON)
    calculation_details JSON,  -- {buy_premium_pct, target_method, stop_method, ...}

    -- Execution tracking
    status VARCHAR(20) DEFAULT 'pending',  -- pending, executed, cancelled, expired
    execution_price DECIMAL,
    execution_time TIMESTAMP,

    -- Performance tracking (filled after trade)
    actual_return DECIMAL,
    exit_price DECIMAL,
    exit_time TIMESTAMP,
    exit_reason VARCHAR(50),  -- target_hit, stop_hit, manual, timeout

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trading_signal_run ON trading_signal(analysis_run_id);
CREATE INDEX idx_trading_signal_stock ON trading_signal(stock_code);
CREATE INDEX idx_trading_signal_status ON trading_signal(status);
CREATE INDEX idx_trading_signal_date ON trading_signal(analysis_date, target_trade_date);
```

---

## Data Relationships

```
analysis_run (1 run per day)
    ├── market_snapshot (1 snapshot per run)
    ├── ai_screening_result (1 screening per run)
    │       └── ai_candidate (40 candidates per screening)
    ├── technical_screening_result (1 screening per run)
    │       └── technical_selection (3-5 selections per screening)
    └── trading_signal (3-5 signals per run)
            └── references technical_selection
```

---

## Web Monitoring Dashboard Views

### Dashboard Home (Today's Analysis)
```sql
-- Get latest analysis run
SELECT * FROM analysis_run
WHERE run_date = CURRENT_DATE
ORDER BY start_time DESC LIMIT 1;

-- Get market snapshot
SELECT * FROM market_snapshot
WHERE analysis_run_id = ?;

-- Get final signals
SELECT * FROM trading_signal
WHERE analysis_run_id = ? AND status = 'pending';
```

### AI Screening Details
```sql
-- Get AI screening summary
SELECT * FROM ai_screening_result WHERE analysis_run_id = ?;

-- Get all AI candidates
SELECT * FROM ai_candidate
WHERE ai_screening_id = ?
ORDER BY rank_in_batch;
```

### Technical Analysis Details
```sql
-- Get technical screening summary
SELECT * FROM technical_screening_result WHERE analysis_run_id = ?;

-- Get all technical selections
SELECT * FROM technical_selection
WHERE tech_screening_id = ?
ORDER BY final_score DESC;
```

### Historical Performance
```sql
-- Get all past signals with actual results
SELECT
    ts.*,
    ar.run_date,
    ar.status as run_status
FROM trading_signal ts
JOIN analysis_run ar ON ts.analysis_run_id = ar.id
WHERE ts.status IN ('executed', 'cancelled', 'expired')
ORDER BY ts.analysis_date DESC
LIMIT 100;
```

### Analysis Run History
```sql
-- Get all analysis runs with metrics
SELECT
    ar.*,
    COUNT(DISTINCT ts.id) as signals_count,
    AVG(ts.predicted_return) as avg_predicted_return,
    AVG(ts.actual_return) as avg_actual_return
FROM analysis_run ar
LEFT JOIN trading_signal ts ON ar.id = ts.analysis_run_id
GROUP BY ar.id
ORDER BY ar.run_date DESC;
```

---

## Next Steps

1. **Create database models** in `src/database/models.py`
2. **Add migration script** to create new tables
3. **Modify each phase** to persist data:
   - MarketAnalyzer → Save to market_snapshot
   - AIScreener → Save to ai_screening_result + ai_candidate
   - TechnicalScreener → Save to technical_screening_result + technical_selection
   - PriceCalculator → Save to trading_signal
4. **Create AnalysisOrchestrator** to manage analysis_run lifecycle
5. **Test end-to-end** data flow with persistence
6. **Build web dashboard** views to visualize stored data
