# AI_INTEGRATION.md - External AI API Integration Guide

## Overview

AutoQuant uses external AI APIs for two critical functions:

1. **Stock Screening (1st Filter)**: Reduce 4,359 stocks to 30~40 candidates
2. **Portfolio Analysis**: Analyze portfolio composition and provide recommendations

This guide covers supported AI providers, API integration, prompt engineering, cost optimization, and error handling.

---

## Supported AI Providers

### 1. OpenAI (GPT-4) - PRIMARY RECOMMENDATION

**Provider**: OpenAI
**Model**: gpt-4 or gpt-4-turbo
**Cost**: ~$0.03-0.06 per screening call (depending on prompt size)
**Response Time**: ~3-5 seconds
**Quality**: Excellent market understanding, nuanced reasoning

**Advantages**:
- Mature, stable API
- Best market knowledge (trained on financial data)
- Fast response time
- Good cost-to-quality ratio
- Excellent error handling

**Setup**:
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

**Usage**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.5,
    max_tokens=2000
)
```

---

### 2. Anthropic (Claude) - ALTERNATIVE

**Provider**: Anthropic
**Model**: claude-3-opus-20240229 or claude-3-sonnet
**Cost**: ~$0.02-0.04 per screening call
**Response Time**: ~2-4 seconds
**Quality**: Very good, thoughtful analysis

**Advantages**:
- Lower cost than GPT-4
- Strong reasoning capabilities
- Good for nuanced market analysis
- Transparent token counting
- Excellent instruction following

**Setup**:
```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Usage**:
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
```

---

### 3. Google (Gemini) - EXPERIMENTAL

**Provider**: Google
**Model**: gemini-pro or gemini-pro-vision
**Cost**: ~$0.0005-0.001 per screening call (cheapest)
**Response Time**: ~3-6 seconds
**Quality**: Good, but fewer financial training examples

**Advantages**:
- Extremely low cost
- Fast API
- Multimodal capability (if needed for charts)

**Setup**:
```bash
pip install google-generativeai
export GOOGLE_API_KEY="AIza..."
```

**Usage**:
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(prompt)
```

---

## Provider Comparison Matrix

| Feature | GPT-4 | Claude 3 | Gemini |
|---------|-------|----------|--------|
| Cost per call | $0.03-0.06 | $0.02-0.04 | $0.0005-0.001 |
| Speed | 3-5s | 2-4s | 3-6s |
| Market knowledge | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Reasoning quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Stability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Error handling | Excellent | Excellent | Good |
| Token limits | High | Very high | High |
| Recommendation | ✅ Primary | ✅ Alternative | ⚠️ Experimental |

**Recommendation**: Use GPT-4 as primary, Claude as fallback, Gemini as cost-saving option for high-volume scenarios.

---

## Configuration

### .env Setup

```env
# AI Provider Selection (options: openai, anthropic, google)
AI_SCREENING_PROVIDER=openai
AI_PORTFOLIO_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.5

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_MAX_TOKENS=2000
ANTHROPIC_TEMPERATURE=0.5

# Google Configuration
GOOGLE_API_KEY=AIza...
GOOGLE_MODEL=gemini-pro
GOOGLE_MAX_TOKENS=2000
GOOGLE_TEMPERATURE=0.5

# API Settings
AI_API_TIMEOUT=30  # seconds
AI_API_RETRIES=3
AI_API_RETRY_DELAY=2  # seconds

# Cost Control
DAILY_API_BUDGET=100  # USD, daily limit
MONTHLY_API_BUDGET=3000  # USD, monthly limit
```

### Python Configuration

```python
# config.py
import os
from dataclasses import dataclass
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

@dataclass
class AIConfig:
    provider: AIProvider = AIProvider.OPENAI
    api_key: str = os.getenv("OPENAI_API_KEY")
    model: str = "gpt-4"
    temperature: float = 0.5
    max_tokens: int = 2000
    timeout: int = 30
    retries: int = 3
    retry_delay: int = 2

    @classmethod
    def from_env(cls):
        provider_name = os.getenv("AI_SCREENING_PROVIDER", "openai").lower()
        provider = AIProvider[provider_name.upper()]

        if provider == AIProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4")
        elif provider == AIProvider.ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        else:  # Google
            api_key = os.getenv("GOOGLE_API_KEY")
            model = os.getenv("GOOGLE_MODEL", "gemini-pro")

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=float(os.getenv("AI_TEMPERATURE", "0.5")),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000"))
        )
```

---

## Prompt Engineering for Stock Screening

### Context and Goal

**Screening Goal**: AI analyzes 4,359 Korean stocks and market conditions to identify 30~40 candidates with highest probability of outperformance in next trading day.

**Key Factors AI Should Consider**:
1. Current market regime (uptrend/downtrend/consolidation)
2. Investor flows (foreign buying/selling, institutional momentum)
3. Sector performance and rotation patterns
4. Individual stock momentum and technical setups
5. Thematic/narrative trends (AI, EVs, semiconductors, etc.)
6. Relative strength vs market indices

### Prompt Template 1: Comprehensive Market Analysis Screening

**Use Case**: Full market analysis with detailed context

```
You are an expert Korean stock market analyst with 20+ years of experience.

TODAY'S MARKET CONTEXT:
- Date: {date}
- KOSPI Close: {kospi_price} ({kospi_change_pct}%)
- KOSDAQ Close: {kosdaq_price} ({kosdaq_change_pct}%)
- Market Trend: {market_trend}
- Investor Flows: Foreign {foreign_flow}, Institutional {inst_flow}, Retail {retail_flow}
- Top Sectors: {top_sectors}
- Market Sentiment: {sentiment}

OBJECTIVE:
From the following 4,359 Korean stocks, identify the TOP 30-40 CANDIDATES with the highest
probability of positive return or strong technical setup for trading in the next session
({next_trading_date}).

SELECTION CRITERIA (in order of importance):
1. Market Momentum Alignment: Stocks aligned with current market direction
2. Investor Flow Confirmation: Stocks with positive foreign/institutional buying
3. Sector Strength: Stocks in outperforming sectors
4. Technical Setup: Stocks with bullish patterns (support breaks, crossovers)
5. Thematic Strength: Stocks participating in current market narratives

STOCK DATA:
{all_stocks_data}
(Format: Code | Name | Current Price | Daily Change % | Market Cap | RSI | Volume Change | Sector)

RESPONSE FORMAT:
Provide your analysis in the following JSON structure:
{
  "market_analysis": "Brief market assessment (2-3 sentences)",
  "reasoning": "Why these stocks were selected (3-4 sentences)",
  "selected_stocks": [
    {
      "code": "005930",
      "name": "삼성전자",
      "reason": "Strong sector momentum + positive foreign flow",
      "confidence": 85,
      "key_indicators": ["volume break", "foreign buying", "sector strength"]
    },
    ...
  ]
}

IMPORTANT:
- Return EXACTLY 30-40 stocks
- Provide confidence score (0-100) for each
- All stocks must exist in provided list
- Explain reasoning for each selection
```

### Prompt Template 2: Quick Screening (Lower Cost)

**Use Case**: Fast screening with limited context (saves tokens/cost)

```
Korean stock analyst: Analyze market {date} and pick 30-40 best trading candidates.

Market: {market_trend} | Flows: Foreign {foreign_flow}, Sector leaders: {top_sectors}

From this list, select top 30-40 with best momentum/setup:
{top_500_stocks_by_volume}

Format:
Code | Name | Confidence %
Return only stock codes and confidence scores. Briefly explain selection logic.
```

### Prompt Template 3: Thematic Screening

**Use Case**: Focus on current investment themes

```
Market date: {date}
Theme focus: {current_themes}

Given current themes ({themes}), which 30-40 Korean stocks have best positioning?

Stocks: {all_stocks_data}

Return: Code, Name, Theme relevance score (0-100), Why selected
```

### Example Full Prompt (Production Use)

```
You are an expert Korean stock market analyst with deep understanding of KRX market dynamics.

=== MARKET CONTEXT (2024-10-25) ===
KOSPI: 2,467 (+0.8%) | KOSDAQ: 778 (-0.3%)
Market Trend: UPTREND (3-day higher highs confirmed)
Investor Flows: Foreign +45.2B KRW, Institutional +12.3B KRW, Retail -8.1B KRW
→ Strong foreign institutional buying, typical bull market signal

Sector Performance:
- IT/Semiconductors: +1.8% (strongest)
- Finance: +0.5%
- Materials: +1.2%
- Healthcare: -0.2%
→ Growth sector outperformance, flight to quality tech

Market Breadth: 2:1 Advance/Decline ratio (strong bullish)
Volatility: KOSPI VIX equivalent = 16.2 (moderate, healthy)

=== STOCK UNIVERSE ===
Total stocks analyzed: 4,359 Korean equities
(Attached: CSV with all stocks - Code, Name, Price, Daily%, Market Cap, RSI, Volume%)

=== SCREENING TASK ===
Identify 30-40 stocks with HIGHEST PROBABILITY of:
1. Positive return in next trading session (2024-10-28)
2. Strong technical/fundamental setup for trading

=== SELECTION CRITERIA ===
Weight by importance:
- Market alignment (30%): Stock moving WITH market trend
- Momentum (25%): RSI, volume, price action
- Investor flows (20%): Foreign/institutional positioning
- Sector strength (15%): In outperforming sectors
- Valuation (10%): Not extended on daily chart

=== RESPONSE FORMAT ===
Return as JSON:
{
  "analysis": "Brief market assessment and selection logic",
  "candidates": [
    {
      "code": "005930",
      "name": "삼성전자",
      "current_price": 78200,
      "daily_change": 1.2,
      "reason": "Sector strength (IT +1.8%), foreign buying (+3.2B), RSI=58 (momentum)",
      "confidence": 82,
      "signals": ["foreign_buying", "sector_outperform", "bullish_rsi"]
    },
    ... (continue for ~40 stocks)
  ]
}

CRITICAL CONSTRAINTS:
- Select EXACTLY 30-40 stocks
- Confidence scores must reflect actual probability (avoid all 90+)
- All codes must exist in provided universe
- Provide specific reasoning for EACH stock
```

---

## Prompt Engineering for Portfolio Analysis

### Goal

Analyze current portfolio holdings and provide AI-driven recommendations for:
1. Sector diversification assessment
2. Risk distribution analysis
3. Individual stock ratings (KEEP/REDUCE/EXIT)
4. Portfolio rebalancing suggestions
5. Capital allocation recommendations

### Portfolio Analysis Prompt Template

```
You are a portfolio manager with 30+ years of experience in Korean equities.

=== CURRENT PORTFOLIO ===
Total Value: {portfolio_value:,.0f} KRW
Holdings: {num_holdings} stocks
{portfolio_holdings_table}

=== MARKET CONTEXT ===
Date: {date}
Market Trend: {market_trend}
Sector Outlook: {sector_outlook}
Volatility: {volatility_level}

=== ANALYSIS REQUESTED ===
Provide comprehensive portfolio analysis:

1. DIVERSIFICATION ASSESSMENT
   - Current sector allocation vs optimal
   - Concentration risk analysis
   - Geographic exposure (if applicable)

2. INDIVIDUAL STOCK RATINGS
   For each holding:
   - Rating: STRONG BUY / BUY / HOLD / REDUCE / SELL
   - 1-year target price
   - Key risks and catalysts

3. REBALANCING RECOMMENDATIONS
   - What to increase / decrease / exit
   - Specific allocation percentages
   - Timeline for rebalancing

4. CAPITAL ALLOCATION STRATEGY
   - How to deploy new capital
   - Hedging considerations (if needed)
   - Risk management positioning

=== RESPONSE FORMAT ===
Return as structured JSON with:
{
  "portfolio_summary": {...},
  "sector_analysis": {...},
  "stock_ratings": [...],
  "rebalancing_plan": {...},
  "capital_deployment": {...},
  "risk_assessment": {...}
}
```

---

## API Implementation Class

### AIScreener Implementation

```python
# src/screening/ai_screener.py
import os
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
from loguru import logger
import pandas as pd

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class AIScreener:
    """Screen 4,359 stocks down to 30~40 candidates using external AI API"""

    def __init__(self, provider: str = "openai"):
        self.provider = AIProvider(provider.lower())
        self.config = self._load_config()
        self._init_client()
        self.api_call_count = 0
        self.api_cost = 0.0

    def _load_config(self) -> Dict:
        """Load configuration from environment"""
        return {
            "timeout": int(os.getenv("AI_API_TIMEOUT", "30")),
            "retries": int(os.getenv("AI_API_RETRIES", "3")),
            "retry_delay": int(os.getenv("AI_API_RETRY_DELAY", "2")),
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.5")),
            "max_tokens": int(os.getenv("AI_MAX_TOKENS", "2000"))
        }

    def _init_client(self):
        """Initialize API client based on provider"""
        if self.provider == AIProvider.OPENAI:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        elif self.provider == AIProvider.ANTHROPIC:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        else:  # Google
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.client = genai
            self.model = os.getenv("GOOGLE_MODEL", "gemini-pro")

    def screen_stocks(self,
                      market_snapshot: Dict,
                      all_stocks: pd.DataFrame) -> List[Dict]:
        """Screen stocks and return 30~40 candidates with AI reasoning"""

        logger.info(f"Starting AI stock screening with {self.provider.value} API")

        # Build prompt
        prompt = self._build_screening_prompt(market_snapshot, all_stocks)

        # Call API with retry logic
        response = self._call_ai_api_with_retry(prompt)

        # Parse response
        candidates = self._parse_screening_response(response)

        logger.info(f"AI screening complete: {len(candidates)} candidates selected")

        return candidates

    def _build_screening_prompt(self, market_snapshot: Dict,
                                all_stocks: pd.DataFrame) -> str:
        """Build detailed prompt for AI screening"""

        # Format market context
        market_text = f"""
TODAY'S MARKET CONTEXT ({market_snapshot['date']}):
- KOSPI: {market_snapshot['kospi_close']:,.0f} ({market_snapshot['kospi_change']:+.2f}%)
- KOSDAQ: {market_snapshot['kosdaq_close']:,.0f} ({market_snapshot['kosdaq_change']:+.2f}%)
- Advance/Decline: {market_snapshot['advance_decline_ratio']:.2f}
- Foreign Flow: {market_snapshot['foreign_flow']:+,.0f} KRW
- Institutional Flow: {market_snapshot['institution_flow']:+,.0f} KRW
- Market Trend: {market_snapshot['market_trend']}
- Top Sectors: {', '.join(market_snapshot['top_sectors'])}
"""

        # Format stock data (top 500 by volume for context)
        top_stocks = all_stocks.nlargest(500, 'volume')[
            ['code', 'name', 'close', 'change_pct', 'market_cap', 'rsi_14', 'volume_change_pct']
        ]

        stocks_text = "TOP 500 STOCKS (by volume):\n"
        stocks_text += "Code|Name|Price|Change%|Market Cap|RSI|Vol%\n"
        for _, row in top_stocks.iterrows():
            stocks_text += f"{row['code']}|{row['name']}|{row['close']:,.0f}|{row['change_pct']:+.1f}|{row['market_cap']:,.0f}|{row['rsi_14']:.0f}|{row['volume_change_pct']:+.0f}\n"

        prompt = f"""You are an expert Korean stock market analyst with 20+ years of experience.

{market_text}

OBJECTIVE:
From 4,359 Korean stocks, identify TOP 30-40 candidates with highest probability of positive
return or strong technical setup for next trading session ({market_snapshot.get('next_trading_date', 'tomorrow')}).

SELECTION CRITERIA (by importance):
1. Market alignment: Moving WITH current trend
2. Investor flows: Positive foreign/institutional buying
3. Sector strength: In outperforming sectors
4. Technical momentum: RSI, volume, price action

{stocks_text}

RESPONSE: Return as JSON with selected_stocks list (Code, Name, Confidence 0-100, Reason)
Select EXACTLY 30-40 stocks. All codes must be from provided list.
"""

        return prompt

    def _call_ai_api_with_retry(self, prompt: str) -> str:
        """Call AI API with automatic retry on failure"""

        for attempt in range(self.config['retries']):
            try:
                logger.info(f"Calling {self.provider.value} API (attempt {attempt+1}/{self.config['retries']})")

                response = self._call_ai_api(prompt)

                self.api_call_count += 1
                logger.info(f"API call successful. Total calls: {self.api_call_count}")

                return response

            except Exception as e:
                logger.warning(f"API call failed: {str(e)}")

                if attempt < self.config['retries'] - 1:
                    wait_time = self.config['retry_delay'] * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {self.config['retries']} attempts")
                    raise

        raise Exception("Max retries exceeded")

    def _call_ai_api(self, prompt: str) -> str:
        """Call external AI API based on configured provider"""

        if self.provider == AIProvider.OPENAI:
            return self._call_openai(prompt)
        elif self.provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
        else:
            return self._call_google(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens'],
            timeout=self.config['timeout']
        )

        # Calculate cost (GPT-4: $0.03/1K input, $0.06/1K output)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.03 + output_tokens * 0.06) / 1000
        self.api_cost += cost

        logger.info(f"OpenAI usage: {input_tokens} input, {output_tokens} output (${cost:.4f})")

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config['max_tokens'],
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config['temperature']
        )

        # Calculate cost (Claude 3 Opus: $0.015/1K input, $0.075/1K output)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000
        self.api_cost += cost

        logger.info(f"Anthropic usage: {input_tokens} input, {output_tokens} output (${cost:.4f})")

        return response.content[0].text

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API"""
        model = self.client.GenerativeModel(self.model)
        response = model.generate_content(prompt)

        # Google pricing (very low cost)
        # For simplicity, estimate based on prompt length
        est_cost = len(prompt) / 1000 * 0.0005  # Rough estimate
        self.api_cost += est_cost

        logger.info(f"Google Gemini response received (est. ${est_cost:.4f})")

        return response.text

    def _parse_screening_response(self, response: str) -> List[Dict]:
        """Parse AI response and extract stock candidates"""

        try:
            # Try to parse as JSON
            if response.startswith('{'):
                data = json.loads(response)
                candidates = data.get('candidates', data.get('selected_stocks', []))
            else:
                # Fallback: parse text response
                candidates = self._parse_text_response(response)

            # Validate we have 30-40 candidates
            if not (30 <= len(candidates) <= 50):
                logger.warning(f"AI returned {len(candidates)} candidates (expected 30-40)")

            return candidates

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            raise

    def _parse_text_response(self, response: str) -> List[Dict]:
        """Parse text-format response (fallback)"""
        candidates = []
        for line in response.split('\n'):
            if '|' in line and len(line.split('|')) >= 3:
                parts = line.split('|')
                candidates.append({
                    'code': parts[0].strip(),
                    'name': parts[1].strip(),
                    'confidence': int(float(parts[2].strip())) if len(parts) > 2 else 50,
                    'reason': parts[3].strip() if len(parts) > 3 else ''
                })
        return candidates

```

---

## Error Handling and Fallbacks

### Common Errors and Solutions

```python
# Handle API key errors
try:
    screener = AIScreener(provider="openai")
except ValueError as e:
    logger.error(f"Invalid API key: {str(e)}")
    # Fallback: use technical-only screening (no AI)
    screener = TechnicalScreener()  # 1st filter skipped

# Handle timeout
try:
    candidates = screener.screen_stocks(market_snapshot, all_stocks)
except TimeoutError:
    logger.warning("AI API timeout, using fallback selection")
    candidates = self._fallback_selection(all_stocks)

# Handle rate limiting
except RateLimitError:
    logger.warning("API rate limit hit, waiting before retry")
    time.sleep(60)
    candidates = screener.screen_stocks(market_snapshot, all_stocks)

# Handle invalid response
except json.JSONDecodeError:
    logger.warning("Invalid AI response format, using text parsing")
    candidates = self._parse_text_response(raw_response)
```

### Fallback Strategies

**Strategy 1: Technical-Only Screening** (no AI)
```python
def fallback_selection_technical_only(all_stocks: pd.DataFrame) -> List[str]:
    """If AI API unavailable, use technical indicators for 1st filter"""
    # Add technical indicators
    all_stocks = TechnicalIndicators.add_all_indicators(all_stocks)

    # Score all stocks
    scores = all_stocks.apply(
        lambda row: score_technical(row),
        axis=1
    )

    # Return top 40
    return all_stocks.nlargest(40, scores).index.tolist()
```

**Strategy 2: Volume + Momentum** (simplest)
```python
def fallback_selection_simple(all_stocks: pd.DataFrame) -> List[str]:
    """Simple fallback: top volume + positive momentum"""
    all_stocks['score'] = (
        all_stocks['volume_change_pct'] * 0.6 +
        all_stocks['change_pct'] * 0.4
    )
    return all_stocks.nlargest(40, 'score').index.tolist()
```

**Strategy 3: Switch AI Provider**
```python
# Try primary provider
try:
    screener = AIScreener(provider="openai")
    candidates = screener.screen_stocks(...)
except Exception as e:
    logger.warning(f"OpenAI failed: {str(e)}, switching to Anthropic")
    screener = AIScreener(provider="anthropic")
    candidates = screener.screen_stocks(...)
```

---

## Cost Optimization

### Daily Cost Estimates

**Assuming 1 stock screening call per day:**

| Provider | Cost per call | Monthly cost | Annual cost |
|----------|--------------|--------------|------------|
| GPT-4 | $0.04 | $1.20 | $14.40 |
| Claude 3 | $0.03 | $0.90 | $10.80 |
| Gemini | $0.0005 | $0.015 | $0.18 |

**Optimization strategies:**

1. **Batch processing**: Send all stocks in single API call (cheaper than multiple calls)
2. **Provider switching**: Use Gemini for high-volume days, GPT-4 for quality days
3. **Cached responses**: Cache good results for market-flat days
4. **Off-peak calling**: Call API during off-peak hours (lower rates if available)
5. **Prompt optimization**: Remove unnecessary context to reduce token count

### Cost Tracking

```python
# Track daily API costs
class CostTracker:
    def __init__(self):
        self.daily_cost = 0
        self.monthly_cost = 0
        self.daily_budget = float(os.getenv("DAILY_API_BUDGET", "100"))
        self.monthly_budget = float(os.getenv("MONTHLY_API_BUDGET", "3000"))

    def log_api_call(self, cost: float):
        """Log API call and check budgets"""
        self.daily_cost += cost
        self.monthly_cost += cost

        if self.daily_cost > self.daily_budget:
            logger.warning(f"Daily budget exceeded: ${self.daily_cost:.2f}")

        if self.monthly_cost > self.monthly_budget:
            logger.error(f"Monthly budget exceeded: ${self.monthly_cost:.2f}")
            # Fallback to technical-only screening
            return False

        return True
```

---

## Testing and Validation

### Test Prompts

```python
# Test 1: Simple screening prompt
test_market = {
    "date": "2024-10-25",
    "kospi_price": 2467,
    "kospi_change_pct": 0.8,
    "market_trend": "UPTREND",
    "top_sectors": ["IT", "Semiconductors"]
}

screener = AIScreener(provider="openai")
candidates = screener.screen_stocks(test_market, test_stocks_df)
assert len(candidates) >= 30
assert all('code' in c and 'confidence' in c for c in candidates)

# Test 2: Response parsing
response = '{"candidates": [{"code": "005930", "confidence": 85, "reason": "test"}]}'
parsed = screener._parse_screening_response(response)
assert len(parsed) == 1
assert parsed[0]['code'] == "005930"

# Test 3: API retry logic
# Simulate failure then success
with patch('openai.OpenAI.chat.completions.create') as mock:
    mock.side_effect = [TimeoutError(), response_success]
    result = screener._call_ai_api_with_retry(prompt)
    assert mock.call_count == 2  # Should retry once
```

---

## Monitoring and Logging

### Log Example

```
2024-10-25 15:45:00 | INFO | Starting AI stock screening with openai API
2024-10-25 15:45:02 | INFO | Built screening prompt (2,847 tokens)
2024-10-25 15:45:03 | INFO | Calling openai API (attempt 1/3)
2024-10-25 15:45:07 | INFO | OpenAI usage: 2847 input, 1283 output ($0.1145)
2024-10-25 15:45:07 | INFO | Parsed response: 35 candidates
2024-10-25 15:45:07 | INFO | AI screening complete: 35 candidates selected

Selected candidates:
- 005930 (삼성전자): 85% confidence
- 000660 (SK하이닉스): 82% confidence
- 035720 (카카오): 78% confidence
... (32 more)

Daily API Cost: $0.1145
Monthly API Cost: $2.87
```

---

## Document References

For complete system overview, see:
- **SYSTEM_DESIGN.md**: Full architecture and data flow
- **IMPLEMENTATION_PLAN.md**: 6-phase implementation roadmap
- **CLAUDE.md**: Updated project documentation
