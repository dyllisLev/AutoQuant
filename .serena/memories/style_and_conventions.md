# AutoQuant Code Style & Conventions

## Python Style (PEP 8)
- Naming: snake_case for functions/variables, PascalCase for classes
- Type hints: Required for function signatures
- Docstrings: Korean or English, describe purpose and parameters
- Line length: 88 characters (black formatter)

## Database & ORM
- Use SQLAlchemy ORM models in src/database/models.py
- All models inherit from Base (declarative_base())
- Relationships use relationship() with back_populates
- Timestamps: created_at, updated_at (DateTime with default=datetime.utcnow)

## Data & DataFrame
- Index: Always DatetimeIndex for time series
- Columns: Consistent naming (Open, High, Low, Close, Volume - capitalized)
- Missing data: Handle with dropna() or fillna() explicitly
- Stock tickers: 6-digit Korean codes (e.g., '005930')

## Logging
- Import: from loguru import logger
- Levels: logger.info(), logger.debug(), logger.warning(), logger.error()
- Format: "[MODULE_NAME] message with context"
- No print() statements - always use logger

## Error Handling
- Always use try-except for external API calls
- Collector classes auto-retry with exponential backoff
- Default values: Return sensible defaults on error (don't raise)
- Logging: Always log error with context before returning default

## Configurations
- Environment variables in .env (never commit)
- Use os.getenv('VAR_NAME', default_value)
- Template: .env.example shows all required variables
- Secrets: DB passwords, API keys NEVER in code

## Testing
- All test functions: def test_xxx():
- Arrange-Act-Assert pattern
- Mock data: Use MockDataGenerator for offline testing
- Database: Use sqlite for testing (set DB_TYPE=sqlite in .env)

## Documentation
- README.md: High-level overview
- SYSTEM_DESIGN.md: Architecture and data flow
- AI_INTEGRATION.md: AI API setup and usage
- IMPLEMENTATION_PLAN.md: 6-phase roadmap
- USER_TEST_CHECKLIST.md: Testing procedures
- Each CLAUDE.md section: Detailed project guidance

## Naming Conventions

### Variables
- Market sentiment: market_sentiment, sentiment (str: 'BULLISH', 'BEARISH', 'NEUTRAL')
- Scores: xxx_score, xxx_signal (int 0-100)
- DataFrames: df, history_df, ohlcv_df
- Dates: target_date, start_date, end_date (datetime.date)

### Functions
- Calculators: calculate_xxx(), compute_xxx()
- Getters: get_xxx(), fetch_xxx()
- Predictors: predict_xxx()
- Validators: is_xxx(), has_xxx()
- Private methods: _xxx()

### Classes
- Managers: XxxManager (PortfolioManager, DatabaseManager)
- Calculators: XxxCalculator
- Screeners: XxxScreener (AIScreener, TechnicalScreener)
- Analyzers: XxxAnalyzer (MarketAnalyzer)
- Predictors: XxxPredictor (LSTMPredictor, XGBoostPredictor)

## Code Organization

### Module Structure
```python
# Imports: standard lib → third-party → local
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
from loguru import logger

from src.database import Database
from src.analysis import TechnicalIndicators

# Constants (UPPERCASE)
DEFAULT_RSI_PERIOD = 14
MOMENTUM_WEIGHTS = {'factor1': 0.4, 'factor2': 0.2, ...}

# Classes
class XxxClass:
    def __init__(self, ...):
        self.logger = logger.bind(name=self.__class__.__name__)
    
    def public_method(self):
        ...
    
    def _private_method(self):
        ...

# Module-level functions
def helper_function():
    ...

# Main execution
if __name__ == '__main__':
    ...
```

## Comments
- Code should be self-documenting (good names > comments)
- Use comments for WHY, not WHAT
- Korean or English, be consistent
- TODO/FIXME: Use if necessary, but prefer fixing immediately

## Import Organization
```python
# 1. Standard library
import os, sys, json
from datetime import datetime, timedelta

# 2. Third-party
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# 3. Local modules
from src.database import Database
from src.analysis import TechnicalIndicators
```

## Type Hints Examples
```python
def analyze_market(self, target_date: date) -> Tuple[str, Dict]:
    """시장 분석 및 심리 판단
    
    Args:
        target_date: 분석 대상 날짜
    
    Returns:
        (sentiment: BULLISH/BEARISH/NEUTRAL, detail: 상세 분석 정보)
    """
    ...

def calculate_momentum_score(
    momentum_components: Dict[str, float],
    weights: Dict[str, float]
) -> int:
    ...
```