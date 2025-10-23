"""
Phase 3: AI-Based Stock Screening Module

Filters 4,359 Korean stocks down to 30~40 candidates using external AI APIs.
Supports multiple providers: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini).

Key responsibilities:
- Build detailed market context and stock data prompts
- Call external AI APIs with error handling and retries
- Parse AI responses (JSON or text format)
- Track API costs and usage
- Implement fallback strategies if AI unavailable
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from enum import Enum
from loguru import logger

import pandas as pd
import numpy as np


class AIProvider(Enum):
    """Supported AI providers for stock screening"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class AIScreener:
    """
    AI-based stock screener for Phase 3 of AutoQuant system.

    Filters all Korean stocks (4,359) down to 30~40 high-probability candidates
    using market context and AI analysis.

    Features:
    - Multi-provider support (OpenAI, Anthropic, Google)
    - Automatic retry with exponential backoff
    - Cost tracking and budget monitoring
    - Fallback strategies if AI unavailable
    - Market-sentiment aware analysis (uses Phase 2 sentiment confidence)
    """

    def __init__(self, provider: str = "openai"):
        """
        Initialize AIScreener with specified provider.

        Args:
            provider: "openai", "anthropic", or "google"

        Raises:
            ValueError: If provider invalid or API key missing
        """
        self.logger = logger.bind(name=self.__class__.__name__)

        try:
            self.provider = AIProvider(provider.lower())
        except ValueError:
            self.logger.error(f"Invalid provider: {provider}")
            raise ValueError(f"Provider must be openai, anthropic, or google")

        self.config = self._load_config()
        self._init_client()

        # Tracking metrics
        self.api_call_count = 0
        self.api_total_cost = 0.0
        self.screening_history: List[Dict] = []

        self.logger.info(f"AIScreener initialized with {self.provider.value} provider")

    def _load_config(self) -> Dict:
        """Load configuration from environment variables"""
        return {
            "timeout": int(os.getenv("AI_API_TIMEOUT", "30")),
            "retries": int(os.getenv("AI_API_RETRIES", "3")),
            "retry_delay": int(os.getenv("AI_API_RETRY_DELAY", "2")),
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.5")),
            "max_tokens": int(os.getenv("AI_MAX_TOKENS", "2000")),
            "daily_budget": float(os.getenv("DAILY_API_BUDGET", "100")),
            "monthly_budget": float(os.getenv("MONTHLY_API_BUDGET", "3000"))
        }

    def _init_client(self):
        """Initialize API client based on configured provider"""
        if self.provider == AIProvider.OPENAI:
            self._init_openai_client()
        elif self.provider == AIProvider.ANTHROPIC:
            self._init_anthropic_client()
        else:  # Google
            self._init_google_client()

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")

            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
            self.logger.info(f"OpenAI client initialized (model: {self.model})")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def _init_anthropic_client(self):
        """Initialize Anthropic client"""
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")

            self.client = Anthropic(api_key=api_key)
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            self.logger.info(f"Anthropic client initialized (model: {self.model})")
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

    def _init_google_client(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not set in environment")

            genai.configure(api_key=api_key)
            self.client = genai
            self.model = os.getenv("GOOGLE_MODEL", "gemini-pro")
            self.logger.info(f"Google Gemini client initialized (model: {self.model})")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google client: {e}")
            raise

    def screen_stocks(self,
                     market_snapshot: Dict,
                     all_stocks: pd.DataFrame,
                     sentiment_confidence: float = 0.5) -> Tuple[List[Dict], Dict]:
        """
        Screen all stocks and return 30~40 high-probability candidates.

        Args:
            market_snapshot: Market analysis from Phase 2 (sentiment, flows, trends)
            all_stocks: DataFrame with all 4,359 stocks (code, name, price, rsi, volume, etc.)
            sentiment_confidence: Phase 2 confidence level (0-1) - affects analysis depth

        Returns:
            (candidates, metadata) where:
            - candidates: List of Dict with code, name, confidence, reason
            - metadata: Dict with screening_date, provider, cost, num_candidates, etc.
        """
        screening_start = datetime.now()
        self.logger.info(f"Starting AI stock screening ({self.provider.value})")
        self.logger.debug(f"Market sentiment: {market_snapshot.get('sentiment', 'N/A')}, "
                         f"Confidence: {sentiment_confidence:.2f}")

        try:
            # 1. Build screening prompt with market context
            prompt = self._build_screening_prompt(market_snapshot, all_stocks, sentiment_confidence)

            # 2. Call AI API with retry logic
            response = self._call_ai_api_with_retry(prompt)

            # 3. Parse response
            candidates = self._parse_screening_response(response)

            # 4. Validate results
            candidates = self._validate_candidates(candidates, all_stocks)

            # Record metadata
            screening_duration = (datetime.now() - screening_start).total_seconds()
            metadata = {
                'screening_date': market_snapshot.get('date', str(date.today())),
                'provider': self.provider.value,
                'model': self.model,
                'api_cost': self.api_total_cost,
                'api_calls': self.api_call_count,
                'num_candidates': len(candidates),
                'screening_duration_sec': screening_duration,
                'sentiment': market_snapshot.get('sentiment', 'UNKNOWN'),
                'sentiment_confidence': sentiment_confidence
            }

            self.screening_history.append(metadata)

            self.logger.info(f"✅ AI screening complete: {len(candidates)} candidates selected "
                           f"in {screening_duration:.1f}s (Cost: ${self.api_total_cost:.4f})")

            return candidates, metadata

        except Exception as e:
            self.logger.error(f"❌ AI screening failed: {e}")
            raise

    def _build_screening_prompt(self,
                               market_snapshot: Dict,
                               all_stocks: pd.DataFrame,
                               sentiment_confidence: float) -> str:
        """
        Build detailed screening prompt with market context and stock data.

        Prompt includes:
        - Market context (KOSPI, KOSDAQ, flows, trends)
        - Top stocks by volume (reduce context size)
        - Selection criteria weighted by importance
        - Response format requirements
        """

        # Format market context section
        market_context = self._format_market_context(market_snapshot, sentiment_confidence)

        # Format stock data (top 500 by volume to reduce context size)
        stock_data = self._format_stock_data(all_stocks)

        # Build prompt based on sentiment confidence (adaptive depth)
        if sentiment_confidence > 0.7:
            # High confidence: Detailed analysis
            prompt = f"""You are an expert Korean stock market analyst with 20+ years of experience in KRX market trading.

{market_context}

SCREENING OBJECTIVE:
From 4,359 Korean stocks, identify TOP 30-40 candidates with highest probability of:
1. Positive return in next trading session ({market_snapshot.get('next_trading_date', 'tomorrow')})
2. Strong technical and fundamental setup

SELECTION CRITERIA (weighted by importance):
1. Market Alignment (30%): Stocks moving WITH the current {market_snapshot.get('sentiment', 'UNKNOWN')} trend
2. Momentum Strength (25%): RSI, volume action, price momentum
3. Investor Flow Confirmation (20%): Aligned with foreign/institutional buying/selling
4. Sector Strength (15%): In sectors outperforming the market
5. Technical Setup (10%): Bullish patterns (support breaks, moving average crosses)

STOCK DATA (Top 500 by volume - Total 4,359 stocks available):
{stock_data}

RESPONSE REQUIREMENTS:
Return a JSON object with:
{{
  "market_analysis": "Your brief market assessment (2-3 sentences)",
  "selection_reasoning": "Why these 30-40 stocks selected (3-4 sentences)",
  "candidates": [
    {{
      "code": "005930",
      "name": "삼성전자",
      "current_price": 78200,
      "daily_change_pct": 1.2,
      "confidence": 85,
      "reason": "Sector strength (IT +1.8%), foreign buying (+3.2B), RSI=58",
      "signals": ["foreign_buying", "sector_outperform", "bullish_momentum"]
    }},
    ... (continue for ~40 stocks)
  ]
}}

CRITICAL CONSTRAINTS:
- Select EXACTLY 30-40 stocks (not more, not less)
- All stock codes MUST exist in provided list
- Confidence scores must be realistic (mix of 60-90, not all 90+)
- Provide specific, actionable reasoning for EACH selection
- Focus on next trading day opportunity, not long-term value
"""
        else:
            # Low confidence: Conservative analysis, focus on safest selections
            prompt = f"""Stock analyst: Given current market ({market_snapshot.get('sentiment', 'UNKNOWN')}),
select 30-40 best trading candidates from provided stocks.

{market_context}

Criteria:
- Market aligned
- Strong volume
- Technical setup
- Foreign/Institutional buying

Stocks (Top 500):
{stock_data}

Return JSON: {{
  "analysis": "Brief assessment",
  "candidates": [{{"code": "005930", "name": "삼성전자", "confidence": 75, "reason": "Strong setup"}}...]
}}

MUST select EXACTLY 30-40 stocks from provided list."""

        return prompt

    def _format_market_context(self, market_snapshot: Dict, sentiment_confidence: float) -> str:
        """Format market context for prompt"""
        return f"""=== TODAY'S MARKET CONTEXT ({market_snapshot.get('date', 'N/A')}) ===

Market Sentiment: {market_snapshot.get('sentiment', 'UNKNOWN')} (Confidence: {sentiment_confidence:.0%})
KOSPI: {market_snapshot.get('kospi_close', 0):,.0f} ({market_snapshot.get('kospi_change', 0):+.2f}%)
KOSDAQ: {market_snapshot.get('kosdaq_close', 0):,.0f} ({market_snapshot.get('kosdaq_change', 0):+.2f}%)

Investor Flows:
- Foreign: {market_snapshot.get('foreign_flow', 0):+,.0f} KRW
- Institutional: {market_snapshot.get('institution_flow', 0):+,.0f} KRW
- Retail: {market_snapshot.get('retail_flow', 0):+,.0f} KRW

Market Indicators:
- Advance/Decline Ratio: {market_snapshot.get('advance_decline_ratio', 0.5):.2f}
- Market Trend: {market_snapshot.get('market_trend', 'NEUTRAL')}
- Top Performing Sectors: {', '.join(market_snapshot.get('top_sectors', ['N/A']))}

Technical Signals:
- RSI (Market): {market_snapshot.get('technical_rsi', 50):.0f}
- MACD: {market_snapshot.get('technical_macd_direction', 'NEUTRAL')}
- Signal Convergence: {market_snapshot.get('signal_convergence', 0.5):.2f}/1.0
"""

    def _format_stock_data(self, all_stocks: pd.DataFrame) -> str:
        """Format stock data for prompt (top 500 by volume)"""
        if all_stocks.empty:
            return "No stock data available"

        # Select top 500 by volume
        top_stocks = all_stocks.nlargest(500, 'volume') if 'volume' in all_stocks.columns else all_stocks.head(500)

        # Select relevant columns for analysis
        cols_to_use = [col for col in ['code', 'name', 'close', 'change_pct', 'market_cap', 'rsi', 'volume', 'volume_change_pct']
                       if col in top_stocks.columns]

        if not cols_to_use:
            return "No compatible columns in stock data"

        # Format as pipe-delimited for readability
        header = "Code|Name|Price|Change%|Market Cap|RSI|Volume|Vol%\n"
        lines = []

        for _, row in top_stocks.iterrows():
            try:
                code = str(row.get('code', '')).strip()
                name = str(row.get('name', '')).strip()[:15]  # Limit name length
                close = row.get('close', 0)
                change = row.get('change_pct', 0)
                market_cap = row.get('market_cap', 0)
                rsi = row.get('rsi', 50)
                volume = row.get('volume', 0)
                vol_change = row.get('volume_change_pct', 0)

                line = f"{code}|{name}|{close:,.0f}|{change:+.1f}|{market_cap:,.0f}|{rsi:.0f}|{volume:,.0f}|{vol_change:+.0f}"
                lines.append(line)
            except Exception as e:
                self.logger.debug(f"Error formatting stock row: {e}")
                continue

        return header + "\n".join(lines[:500])  # Limit to 500 lines

    def _call_ai_api_with_retry(self, prompt: str) -> str:
        """
        Call AI API with automatic retry on failure.

        Implements exponential backoff: retry_delay * (2 ** attempt)
        """
        for attempt in range(self.config['retries']):
            try:
                self.logger.info(f"Calling {self.provider.value} API "
                               f"(attempt {attempt + 1}/{self.config['retries']})")

                response = self._call_ai_api(prompt)
                self.api_call_count += 1

                self.logger.info(f"✓ API call successful (Total: {self.api_call_count})")
                return response

            except Exception as e:
                self.logger.warning(f"API call failed: {str(e)}")

                if attempt < self.config['retries'] - 1:
                    wait_time = self.config['retry_delay'] * (2 ** attempt)
                    self.logger.info(f"Retrying in {wait_time}s... (Exponential backoff)")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed after {self.config['retries']} attempts")
                    raise

        raise Exception(f"Max retries ({self.config['retries']}) exceeded")

    def _call_ai_api(self, prompt: str) -> str:
        """Route to appropriate provider-specific API call"""
        if self.provider == AIProvider.OPENAI:
            return self._call_openai(prompt)
        elif self.provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
        else:  # Google
            return self._call_google(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT-4 API"""
        # Try with max_completion_tokens first (newer models)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config['temperature'],
                max_completion_tokens=self.config['max_tokens'],
                timeout=self.config['timeout']
            )
        except Exception as e:
            error_str = str(e).lower()

            # Fallback: try without temperature (for models that don't support it)
            if "temperature" in error_str:
                self.logger.debug("Falling back: removing temperature parameter")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=self.config['max_tokens'],
                    timeout=self.config['timeout']
                )
            # Fallback: try with max_tokens for older models
            elif "max_tokens" in error_str:
                self.logger.debug("Falling back: using max_tokens instead of max_completion_tokens")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config['temperature'],
                    max_tokens=self.config['max_tokens'],
                    timeout=self.config['timeout']
                )
            else:
                raise

        # Track cost: GPT-4 pricing ($0.03/1K input, $0.06/1K output)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.03 + output_tokens * 0.06) / 1000
        self.api_total_cost += cost

        self.logger.debug(f"OpenAI: {input_tokens} input + {output_tokens} output tokens (${cost:.4f})")

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config['max_tokens'],
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config['temperature']
        )

        # Track cost: Claude 3 Opus ($0.015/1K input, $0.075/1K output)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000
        self.api_total_cost += cost

        self.logger.debug(f"Anthropic: {input_tokens} input + {output_tokens} output tokens (${cost:.4f})")

        return response.content[0].text

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API"""
        model = self.client.GenerativeModel(self.model)
        response = model.generate_content(prompt)

        # Google pricing (very low, estimate based on prompt)
        est_cost = len(prompt) / 1000 * 0.0005
        self.api_total_cost += est_cost

        self.logger.debug(f"Google Gemini response received (est. ${est_cost:.4f})")

        return response.text

    def _parse_screening_response(self, response: str) -> List[Dict]:
        """
        Parse AI response and extract stock candidates.

        Handles both JSON and text format responses.
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)

                # Try multiple possible keys for candidate list
                candidates = (data.get('candidates') or
                            data.get('selected_stocks') or
                            data.get('stocks') or
                            [])
            else:
                # Fallback: parse text response
                candidates = self._parse_text_response(response)

            # Validate count
            if len(candidates) < 30 or len(candidates) > 50:
                self.logger.warning(f"AI returned {len(candidates)} candidates (expected 30-40)")

            return candidates

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse response as JSON: {e}")
            self.logger.debug(f"Response preview: {response[:500]}")

            # Fallback to text parsing
            return self._parse_text_response(response)

    def _parse_text_response(self, response: str) -> List[Dict]:
        """Parse text-format response (fallback from JSON)"""
        candidates = []

        for line in response.split('\n'):
            if '|' in line and not line.strip().startswith('#'):
                try:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        candidates.append({
                            'code': parts[0],
                            'name': parts[1],
                            'confidence': int(float(parts[2])) if parts[2].isdigit() else 50,
                            'reason': parts[3] if len(parts) > 3 else 'Selected by AI'
                        })
                except Exception as e:
                    self.logger.debug(f"Failed to parse line: {line} ({e})")

        return candidates

    def _validate_candidates(self, candidates: List[Dict], all_stocks: pd.DataFrame) -> List[Dict]:
        """
        Validate candidates and ensure they exist in stock universe.

        Returns only valid candidates that exist in all_stocks.
        """
        if all_stocks.empty or 'code' not in all_stocks.columns:
            self.logger.warning("Cannot validate candidates: stock data empty or missing 'code' column")
            return candidates

        valid_codes = set(all_stocks['code'].astype(str))
        valid_candidates = []

        for candidate in candidates:
            code = str(candidate.get('code', '')).strip()
            if code in valid_codes:
                valid_candidates.append(candidate)
            else:
                self.logger.debug(f"Skipping invalid candidate code: {code}")

        self.logger.info(f"Validation: {len(valid_candidates)}/{len(candidates)} candidates valid")

        return valid_candidates

    def get_cost_summary(self) -> Dict:
        """Get summary of API usage and costs"""
        return {
            'total_api_calls': self.api_call_count,
            'total_cost_usd': self.api_total_cost,
            'screenings_performed': len(self.screening_history),
            'avg_cost_per_screening': self.api_total_cost / max(1, len(self.screening_history)),
            'daily_budget': self.config['daily_budget'],
            'monthly_budget': self.config['monthly_budget'],
            'budget_remaining': self.config['monthly_budget'] - self.api_total_cost
        }
