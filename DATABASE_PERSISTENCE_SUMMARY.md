# Database Persistence Implementation Summary

**Date**: 2025-10-25
**Status**: ✅ COMPLETE (Database Schema Created)
**Next**: Implement data persistence in Phase 2-5 modules

---

## Overview

사용자 요구사항에 따라 **단계별 상세 데이터 저장** 기능을 구현했습니다:

> "추후 웹앱으로 매번 계산한 과정과 모니터링을 할수 있게
> 스텝스탭별로 상세한 정보를 저장했으면 좋겠어"

### 핵심 설계 원칙

1. **Step-by-Step Tracking**: 각 Phase (2-5)의 입력/출력 데이터를 모두 저장
2. **Complete Audit Trail**: 전체 분석 과정을 추적 가능하도록 기록
3. **Web Monitoring Ready**: 웹 대시보드에서 쉽게 조회/분석 가능한 구조
4. **Performance Tracking**: 각 단계의 실행 시간, 성공/실패 추적

---

## Created Database Tables

### 1. **analysis_runs** (분석 실행 기록)
**Purpose**: 일일 분석 실행을 추적하는 마스터 테이블

**Key Fields**:
- `id`: Primary key
- `run_date`: 분석 실행 날짜 (2025-10-25)
- `target_trade_date`: 매매 대상 날짜 (2025-10-28)
- `status`: running | completed | failed
- `phase1_completed` ~ `phase5_completed`: 각 단계 완료 여부
- `total_stocks_analyzed`: 4,359
- `ai_candidates_count`: 40
- `technical_selections_count`: 4
- `final_signals_count`: 4

**Relationships**:
- Has one `market_snapshot`
- Has one `ai_screening_result`
- Has one `technical_screening_result`
- Has many `trading_signals`

---

### 2. **market_snapshots** (Phase 2: 시장 분석 결과)
**Purpose**: 시장 전체 조건 및 모멘텀 분석 저장

**Key Fields**:
- `analysis_run_id`: FK to analysis_runs
- `kospi_close`: 2467.23
- `kospi_change_pct`: 0.8
- `kospi_trend`: UPTREND | DOWNTREND | NEUTRAL
- `kosdaq_close`: 714.56
- `foreign_net_buy`: 45,200,000,000 KRW
- `institution_net_buy`: 12,300,000,000 KRW
- `momentum_score`: 65.5 (0-100)
- `market_sentiment`: BULLISH | BEARISH | NEUTRAL
- `sector_performance`: JSON [{sector, change_pct, volume_ratio}, ...]

**Use Case**:
```sql
-- 웹 대시보드에서 오늘 시장 현황 조회
SELECT * FROM market_snapshots
WHERE snapshot_date = CURRENT_DATE;
```

---

### 3. **ai_screening_results** (Phase 3: AI 스크리닝 결과)
**Purpose**: AI 스크리닝 프로세스 추적

**Key Fields**:
- `analysis_run_id`: FK to analysis_runs
- `ai_provider`: openai | anthropic | google
- `ai_model`: gpt-4 | claude-3 | gemini-pro
- `total_input_stocks`: 4,359
- `selected_count`: 40
- `execution_time_seconds`: 12.5
- `api_cost_usd`: 0.045
- `prompt_text`: Full prompt sent to AI
- `response_text`: Full AI response
- `response_summary`: Summarized reasoning

**Relationships**:
- Has many `ai_candidates` (40 stocks)

**Use Case**:
```sql
-- AI API 비용 추적
SELECT
    screening_date,
    ai_provider,
    api_cost_usd,
    selected_count
FROM ai_screening_results
WHERE screening_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
ORDER BY screening_date DESC;
```

---

### 4. **ai_candidates** (Phase 3: AI 선정 종목 상세)
**Purpose**: AI가 선정한 개별 종목의 근거 저장

**Key Fields**:
- `ai_screening_id`: FK to ai_screening_results
- `stock_code`: 005930
- `company_name`: 삼성전자
- `ai_score`: 92.5 (0-100)
- `ai_reasoning`: "Strong momentum in semiconductor sector..."
- `rank_in_batch`: 1
- `mentioned_factors`: JSON ['sector_strength', 'foreign_buying', ...]
- `current_price`: 98,800
- `sector`: Technology

**Use Case**:
```sql
-- 특정 종목이 AI에 의해 선정된 이력 조회
SELECT
    ac.*,
    asr.screening_date,
    asr.ai_provider
FROM ai_candidates ac
JOIN ai_screening_results asr ON ac.ai_screening_id = asr.id
WHERE ac.stock_code = '005930'
ORDER BY asr.screening_date DESC
LIMIT 10;
```

---

### 5. **technical_screening_results** (Phase 4: 기술적 스크리닝 결과)
**Purpose**: 기술적 분석 프로세스 추적

**Key Fields**:
- `analysis_run_id`: FK to analysis_runs
- `input_candidates_count`: 40 (from AI)
- `final_selections_count`: 4
- `execution_time_seconds`: 2.3
- `min_final_score`: 50.0 (threshold)
- `max_selections`: 5

**Relationships**:
- Has many `technical_selections` (4 stocks)

---

### 6. **technical_selections** (Phase 4: 기술적 선정 종목 상세)
**Purpose**: 기술적 분석으로 선정된 개별 종목의 점수 및 지표

**Key Fields**:
- `tech_screening_id`: FK to technical_screening_results
- `stock_code`: 018000
- `company_name`: 유니슨
- `current_price`: 1,210
- `sma_score`: 20 (out of 20)
- `rsi_score`: 13 (out of 15)
- `macd_score`: 15 (out of 15)
- `bb_score`: 8 (out of 10)
- `volume_score`: 8 (out of 10)
- `final_score`: 64 (out of 70)
- `indicators`: JSON {SMA_5: 1091, SMA_20: 1085, RSI_14: 65.39, ...}
- `rank_in_batch`: 1
- `selection_reason`: "Strong technical setup..."

**Use Case**:
```sql
-- 특정 종목의 기술적 점수 변화 추적
SELECT
    ts.*,
    tsr.screening_date
FROM technical_selections ts
JOIN technical_screening_results tsr ON ts.tech_screening_id = tsr.id
WHERE ts.stock_code = '018000'
ORDER BY tsr.screening_date DESC
LIMIT 10;
```

---

### 7. **trading_signals** (Phase 5: 최종 매매 신호)
**Purpose**: 계산된 매수/목표/손절가 및 모든 상세 정보

**Key Fields** (42 columns total):

**Identification**:
- `analysis_run_id`: FK to analysis_runs
- `tech_selection_id`: FK to technical_selections
- `stock_id`: FK to stocks
- `stock_code`: 018000
- `company_name`: 유니슨

**Dates**:
- `analysis_date`: 2025-10-25
- `target_trade_date`: 2025-10-28

**Prices**:
- `current_price`: 1,210
- `buy_price`: 1,220 (+0.83%)
- `target_price`: 1,360 (+11.48%)
- `stop_loss_price`: 1,090 (-10.66%)

**Metrics**:
- `predicted_return`: 11.25%
- `risk_reward_ratio`: 1.0
- `ai_confidence`: 60

**Support/Resistance**:
- `support_level`: 1,000
- `resistance_level`: 1,300
- `pivot_point`: 1,184
- `r1_level`, `s1_level`, `high_60d`, `low_60d`

**Volatility**:
- `atr`: 62
- `atr_percent`: 5.12
- `volatility_rank`: MEDIUM | LOW | HIGH

**Technical Indicators**:
- `current_rsi`: 65.39
- `current_macd`: 15.23
- `current_bollinger_position`: middle | upper | lower

**Market Context**:
- `market_trend`: UPTREND
- `investor_flow`: positive | negative | neutral
- `sector_momentum`: strong | moderate | weak
- `ai_reasoning`: Full AI explanation text

**Calculation Details** (JSON):
```json
{
    "buy_premium_pct": 0.83,
    "buy_premium_reason": "Neutral RSI (65.39)",
    "target_method": "Conservative (min of AI/Resistance/Technical)",
    "stop_method": "ATR-based (2*ATR below buy)",
    "rr_adjustment": "Auto-adjusted from 0.55 to 1.0"
}
```

**Execution Tracking**:
- `status`: pending | executed | cancelled | expired
- `executed_price`: Actual fill price
- `executed_date`: Execution timestamp

**Performance Tracking**:
- `actual_return`: Real return %
- `exit_price`: Actual exit price
- `exit_time`: Exit timestamp
- `exit_reason`: target_hit | stop_hit | manual | timeout

**Use Cases**:

```sql
-- 1. 오늘 생성된 신호 조회 (외부 매매 프로그램용)
SELECT * FROM trading_signals
WHERE analysis_date = CURRENT_DATE
AND status = 'pending'
ORDER BY predicted_return DESC;

-- 2. 특정 종목의 과거 신호 및 성과
SELECT
    analysis_date,
    buy_price,
    target_price,
    stop_loss_price,
    predicted_return,
    actual_return,
    status,
    exit_reason
FROM trading_signals
WHERE stock_code = '018000'
ORDER BY analysis_date DESC;

-- 3. AI 신뢰도별 성과 분석
SELECT
    CASE
        WHEN ai_confidence >= 80 THEN 'High (80+)'
        WHEN ai_confidence >= 60 THEN 'Medium (60-79)'
        ELSE 'Low (<60)'
    END as confidence_level,
    COUNT(*) as signal_count,
    AVG(predicted_return) as avg_predicted,
    AVG(actual_return) as avg_actual,
    AVG(actual_return - predicted_return) as avg_error
FROM trading_signals
WHERE actual_return IS NOT NULL
GROUP BY
    CASE
        WHEN ai_confidence >= 80 THEN 'High (80+)'
        WHEN ai_confidence >= 60 THEN 'Medium (60-79)'
        ELSE 'Low (<60)'
    END;
```

---

## Data Relationships Diagram

```
analysis_runs (1 run per day)
│
├─► market_snapshot (1:1)
│   └─ Market conditions, momentum, sentiment
│
├─► ai_screening_result (1:1)
│   └─► ai_candidates (1:many, ~40 stocks)
│       └─ AI scores, reasoning, mentioned factors
│
├─► technical_screening_result (1:1)
│   └─► technical_selections (1:many, ~4 stocks)
│       └─ Technical scores, indicators, selection reason
│
└─► trading_signals (1:many, ~4 signals)
    ├─ References technical_selection
    ├─ Calculated prices (buy/target/stop)
    ├─ Support/resistance levels
    ├─ Calculation details (JSON)
    └─ Execution & performance tracking
```

---

## Web Dashboard Queries

### 1. Today's Analysis Dashboard

```sql
-- Get complete analysis for today
SELECT
    ar.id,
    ar.run_date,
    ar.status,
    ar.total_duration_seconds,
    ar.total_stocks_analyzed,
    ar.ai_candidates_count,
    ar.technical_selections_count,
    ar.final_signals_count,
    ms.kospi_close,
    ms.market_sentiment,
    ms.momentum_score,
    asr.ai_provider,
    asr.api_cost_usd,
    tsr.execution_time_seconds as tech_screening_time
FROM analysis_runs ar
LEFT JOIN market_snapshots ms ON ar.id = ms.analysis_run_id
LEFT JOIN ai_screening_results asr ON ar.id = asr.analysis_run_id
LEFT JOIN technical_screening_results tsr ON ar.id = tsr.analysis_run_id
WHERE ar.run_date = CURRENT_DATE;
```

### 2. AI Candidates Detail View

```sql
-- Show all AI-selected stocks for today
SELECT
    ac.rank_in_batch,
    ac.stock_code,
    ac.company_name,
    ac.ai_score,
    ac.ai_reasoning,
    ac.current_price,
    ac.sector,
    ac.mentioned_factors
FROM ai_candidates ac
JOIN ai_screening_results asr ON ac.ai_screening_id = asr.id
JOIN analysis_runs ar ON asr.analysis_run_id = ar.id
WHERE ar.run_date = CURRENT_DATE
ORDER BY ac.rank_in_batch;
```

### 3. Technical Analysis Comparison

```sql
-- Compare technical scores across all candidates
SELECT
    ts.rank_in_batch,
    ts.stock_code,
    ts.company_name,
    ts.final_score,
    ts.sma_score,
    ts.rsi_score,
    ts.macd_score,
    ts.bb_score,
    ts.volume_score,
    ts.indicators->>'RSI_14' as rsi,
    ts.indicators->>'MACD' as macd
FROM technical_selections ts
JOIN technical_screening_results tsr ON ts.tech_screening_id = tsr.id
JOIN analysis_runs ar ON tsr.analysis_run_id = ar.id
WHERE ar.run_date = CURRENT_DATE
ORDER BY ts.final_score DESC;
```

### 4. Final Signals Dashboard

```sql
-- Show today's trading signals with complete context
SELECT
    ts.stock_code,
    ts.company_name,
    ts.current_price,
    ts.buy_price,
    ts.target_price,
    ts.stop_loss_price,
    ts.predicted_return,
    ts.risk_reward_ratio,
    ts.ai_confidence,
    ts.support_level,
    ts.resistance_level,
    ts.atr,
    ts.volatility_rank,
    ts.market_trend,
    ts.sector_momentum,
    ts.status
FROM trading_signals ts
JOIN analysis_runs ar ON ts.analysis_run_id = ar.id
WHERE ar.run_date = CURRENT_DATE
ORDER BY ts.predicted_return DESC;
```

### 5. Historical Performance Analysis

```sql
-- Analyze prediction accuracy over time
SELECT
    DATE_TRUNC('week', analysis_date) as week,
    COUNT(*) as total_signals,
    AVG(predicted_return) as avg_predicted,
    AVG(actual_return) as avg_actual,
    AVG(ABS(actual_return - predicted_return)) as avg_error,
    COUNT(CASE WHEN exit_reason = 'target_hit' THEN 1 END) as targets_hit,
    COUNT(CASE WHEN exit_reason = 'stop_hit' THEN 1 END) as stops_hit,
    AVG(actual_return) FILTER (WHERE actual_return > 0) as avg_win,
    AVG(actual_return) FILTER (WHERE actual_return < 0) as avg_loss
FROM trading_signals
WHERE actual_return IS NOT NULL
GROUP BY DATE_TRUNC('week', analysis_date)
ORDER BY week DESC
LIMIT 12;
```

### 6. Phase-by-Phase Execution Times

```sql
-- Monitor performance of each analysis phase
SELECT
    run_date,
    total_duration_seconds,
    (SELECT execution_time_seconds FROM ai_screening_results WHERE analysis_run_id = ar.id) as ai_time,
    (SELECT execution_time_seconds FROM technical_screening_results WHERE analysis_run_id = ar.id) as tech_time,
    phase1_completed,
    phase2_completed,
    phase3_completed,
    phase4_completed,
    phase5_completed,
    status
FROM analysis_runs ar
WHERE run_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY run_date DESC;
```

---

## Migration Status

### ✅ Completed

1. **Schema Design**: 상세한 단계별 추적 스키마 설계 완료
2. **Database Models**: SQLAlchemy 모델 생성 (`src/database/models.py`)
3. **Table Creation**: PostgreSQL에 7개 새 테이블 생성
4. **Relationships**: 테이블 간 관계 설정 및 테스트 완료
5. **Indexes**: 성능 최적화를 위한 인덱스 생성
6. **Documentation**: `DATABASE_SCHEMA_ANALYSIS.md` 생성

### ⏳ Next Steps

1. **Phase 2 Persistence**: MarketAnalyzer → Save to `market_snapshots`
2. **Phase 3 Persistence**: AIScreener → Save to `ai_screening_results` + `ai_candidates`
3. **Phase 4 Persistence**: TechnicalScreener → Save to `technical_screening_results` + `technical_selections`
4. **Phase 5 Persistence**: PriceCalculator → Save to `trading_signals`
5. **AnalysisOrchestrator**: Create orchestrator to manage `analysis_run` lifecycle
6. **Web Dashboard**: Build Flask views to visualize stored data

---

## Key Design Decisions

### 1. **One Analysis Run = One Row**
- Each daily analysis creates ONE row in `analysis_runs`
- All related data links to this single master record
- Cascading deletes clean up all related data

### 2. **Complete Audit Trail**
- Every intermediate result is saved (40 AI candidates, 4 technical selections)
- Prompts and responses stored for reproducibility
- Execution times tracked for performance monitoring

### 3. **JSON for Flexible Data**
- `sector_performance`: Array of sector data
- `mentioned_factors`: AI's reasoning factors
- `indicators`: All 16 technical indicators
- `calculation_details`: Price calculation methodology

### 4. **Performance Tracking Built-in**
- `actual_return` vs `predicted_return` comparison
- `exit_reason` categorization
- `status` lifecycle tracking

### 5. **Web-Ready Structure**
- Indexed columns for fast queries
- Foreign keys for JOIN optimization
- Date ranges for historical analysis
- Status fields for filtering

---

## File Summary

### Created/Modified Files

1. **`src/database/models.py`** (MODIFIED)
   - Added 6 new model classes
   - Updated TradingSignal with extended fields
   - Total: +300 lines

2. **`src/database/__init__.py`** (MODIFIED)
   - Exported new models
   - Total: +8 models

3. **`scripts/create_analysis_tables.py`** (NEW)
   - Migration script with auto-confirm option
   - Schema display functionality
   - Relationship testing
   - Total: 257 lines

4. **`DATABASE_SCHEMA_ANALYSIS.md`** (NEW)
   - Complete schema documentation
   - Data flow analysis
   - Query examples
   - Total: 500+ lines

5. **`DATABASE_PERSISTENCE_SUMMARY.md`** (NEW - this file)
   - Implementation summary
   - Use cases and queries
   - Next steps guide

---

## Tables Overview

| Table | Purpose | Row Count (Est.) | Key Fields |
|-------|---------|------------------|------------|
| analysis_runs | Master run tracking | 1 per day | run_date, status, phase completion |
| market_snapshots | Market analysis | 1 per run | kospi, momentum, sentiment |
| ai_screening_results | AI process | 1 per run | provider, cost, execution time |
| ai_candidates | AI selections | ~40 per run | stock_code, ai_score, reasoning |
| technical_screening_results | Tech process | 1 per run | input_count, final_count |
| technical_selections | Tech selections | ~4 per run | stock_code, scores, indicators |
| trading_signals | Final signals | ~4 per run | prices, S/R, performance |

**Total rows per day**: ~52 rows (1 + 1 + 1 + 40 + 1 + 4 + 4)
**Storage estimate**: ~500KB per day (~15MB per month)

---

## Next Immediate Action

**Implement data persistence in Phase 2 (MarketAnalyzer)**:

```python
# Example implementation pattern
def analyze_market(self, analysis_run_id: int) -> Dict:
    # 1. Perform analysis
    market_data = self._analyze_market_conditions()

    # 2. Save to database
    from src.database import Database, MarketSnapshot
    db = Database()
    session = db.Session()

    snapshot = MarketSnapshot(
        analysis_run_id=analysis_run_id,
        snapshot_date=date.today(),
        kospi_close=market_data['kospi']['close'],
        kospi_change_pct=market_data['kospi']['change_pct'],
        # ... all other fields
    )
    session.add(snapshot)
    session.commit()
    session.close()

    return market_data
```

이 패턴을 Phase 3, 4, 5에도 적용하면 완전한 추적 시스템이 완성됩니다.

---

**Summary**: 데이터베이스 스키마가 완성되었습니다. 이제 각 Phase 모듈에 데이터 저장 로직을 추가하면 웹 대시보드에서 전체 분석 과정을 실시간으로 모니터링할 수 있습니다!
