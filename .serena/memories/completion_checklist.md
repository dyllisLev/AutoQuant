# Task Completion Checklist

When completing a task, ensure the following before marking as complete:

## Code Quality
- [ ] Type hints: All function signatures have type hints
- [ ] Docstrings: All public functions/classes have docstrings
- [ ] Logging: Uses loguru, no print() statements
- [ ] Error handling: try-except blocks with sensible defaults
- [ ] No TODOs: No unfinished comments in implementation

## Testing
- [ ] Unit tests: New code has unit tests
- [ ] Integration test: Passes python tests/test_all_modules.py
- [ ] Manual testing: Tested with real scenarios or mock data
- [ ] Edge cases: Handle empty data, None values, zero divisions

## Documentation
- [ ] Code comments: Clear WHY not WHAT
- [ ] Function docstrings: Parameters, return values, examples
- [ ] Module-level: Comment explaining purpose
- [ ] External docs: Update CLAUDE.md or relevant guide if needed

## Git & Version Control
- [ ] Committed: Changes committed with meaningful message
- [ ] Feature branch: Work on feature branches, not main/master
- [ ] Clean history: Logical, atomic commits (not giant dumps)
- [ ] No secrets: .env never committed, use .env.example instead

## Database
- [ ] Schema: If new tables, added to models.py
- [ ] Migrations: If schema changes, update database.py
- [ ] Testing: Tested with both SQLite (dev) and PostgreSQL (prod config)
- [ ] Backwards compatible: Old data works with new code

## Performance
- [ ] No N+1 queries: Batch queries when possible
- [ ] Reasonable latency: Operations complete in expected time
- [ ] Memory efficient: Don't load entire datasets unnecessarily
- [ ] Logged slow operations: DEBUG log for slow calculations

## Code Organization
- [ ] Single responsibility: Each function/class has one purpose
- [ ] DRY principle: No duplicate code (reuse functions)
- [ ] Naming: Clear, descriptive names (no x, y, temp)
- [ ] Imports: Organized (stdlib → third-party → local)

## Configuration
- [ ] Environment variables: Uses .env, no hardcoded values
- [ ] Defaults: Sensible defaults when env vars missing
- [ ] Security: No secrets in code, logs, or documentation
- [ ] Documentation: .env.example updated with new variables

## Phase-Specific Checklists

### Market Analysis (Phase 2 - COMPLETE)
- [x] Technical signals (RSI + MACD): Implemented and tested
- [x] Volume strength: Implemented and tested
- [x] Signal convergence: Implemented and tested
- [x] Enhanced sentiment: _judge_sentiment_v2() working
- [x] All 5 historical dates pass test

### AI Screening (Phase 3 - NEXT)
- [ ] AIScreener class: Created in src/screening/ai_screener.py
- [ ] Multi-provider support: OpenAI, Anthropic, Google
- [ ] Error handling: Graceful fallback if API fails
- [ ] Prompt engineering: Effective stock selection prompts
- [ ] Cost tracking: Budget monitoring, provider switching
- [ ] Integration: Uses Phase 2 sentiment confidence
- [ ] Testing: Filters 4,359 → 30~40 candidates correctly

### Technical Screening (Phase 4)
- [ ] TechnicalScreener: Created in src/screening/technical_screener.py
- [ ] 5-factor scoring: RSI, MACD, volume, momentum, trend
- [ ] Ranking: Returns top 3~5 sorted by score
- [ ] Integration: Receives Phase 3 candidates
- [ ] Testing: Rank candidates correctly

### AI Prediction (Phase 5)
- [ ] LSTM model: Training on historical data
- [ ] XGBoost model: Gradient boosting baseline
- [ ] Backtesting: Validate prediction accuracy (not strategy)
- [ ] Confidence scoring: Calibrated to actual accuracy
- [ ] Integration: Feeds into price calculation

### Price Calculation (Phase 5)
- [ ] Buy price: Conservative entry signal
- [ ] Target price: Upside projection from AI + technical
- [ ] Stop-loss: Risk management based on ATR volatility
- [ ] Integration: Works with predictions
- [ ] Testing: Reasonable buy/target/stop levels

### Daily Execution (Phase 6)
- [ ] daily_analysis.py: Orchestrates phases 1-5
- [ ] Timing: Runs 3:45 PM KST post-market
- [ ] TradingSignal: Writes buy/target/stop-loss to database
- [ ] Error recovery: Handles API failures, missing data
- [ ] Logging: Full trace of execution for debugging
- [ ] External ready: Separate trader reads signals and executes