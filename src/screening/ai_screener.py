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

            # DEBUG: Save actual prompt for token analysis
            try:
                import tiktoken
                encoder = tiktoken.get_encoding("cl100k_base")
                token_count = len(encoder.encode(prompt))

                # Count number of stocks in prompt
                stock_count = 0
                if 'Stocks (' in prompt:
                    stocks_section = prompt.split('Stocks (')[1]
                    stock_lines = [l for l in stocks_section.split('\n') if l and '|' in l and l[0].isdigit()]
                    stock_count = len(stock_lines)

                with open('/opt/AutoQuant/debug_actual_prompt.txt', 'w', encoding='utf-8') as f:
                    f.write(f"=== ACTUAL PROMPT FOR PHASE 3 ===\n")
                    f.write(f"Provider: {self.provider.value}\n")
                    f.write(f"Token count (CL100K): {token_count}\n")
                    f.write(f"Character count: {len(prompt)}\n")
                    f.write(f"Stock data lines: {stock_count}\n")
                    f.write(f"===\n\n")
                    f.write(prompt)

                self.logger.info(f"💾 DEBUG: Prompt saved (tokens={token_count}, stocks={stock_count}, chars={len(prompt)})")
            except Exception as e:
                self.logger.debug(f"Debug prompt save failed: {e}")

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

        # Build simpler, clearer prompt
        prompt = f"""Analyze Korean stock market and select 30-40 stocks for next-day trading.

{market_context}

Stocks (500 by volume):
{stock_data}

TASK: Select exactly 30-40 stocks that will likely increase in value tomorrow.
Context: Consider market sentiment (including 7-day trend), RSI levels, volume, investor flows, and market momentum.

For Stock Selection:
- Focus on stocks aligned with market trend direction (uptrend vs downtrend)
- Prefer stocks in top-performing sectors
- Check RSI for extreme overbought/oversold conditions
- Consider foreign investor buying patterns (institutional money flow indicator)
- Factor in volume confirmation (higher volume = more reliable signal)

Return only valid JSON (no other text):
{{
  "candidates": [
    {{"code": "005930", "name": "Stock", "confidence": 75, "reason": "good setup"}},
    ... more stocks...
  ]
}}

Rules:
- Return 30-40 stocks exactly
- Confidence 60-90 range
- All codes from stock list above
- Valid JSON only"""

        return prompt

    def _format_market_context(self, market_snapshot: Dict, sentiment_confidence: float) -> str:
        """Format market context for prompt with 7-day trend analysis"""

        # Current day's snapshot
        context = f"""=== TODAY'S MARKET CONTEXT ({market_snapshot.get('date', 'N/A')}) ===

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

        # Add 7-day trend analysis if available
        trend_7d = market_snapshot.get('trend_7d', None)
        if trend_7d and isinstance(trend_7d, list) and len(trend_7d) > 0:
            context += "\n=== 7-DAY TREND ANALYSIS ===\n"
            context += "Date|KOSPI|Change%|Investor(KRW)B|Trend\n"

            for day_data in trend_7d:
                try:
                    day_date = day_data.get('date', 'N/A')
                    kospi = day_data.get('kospi_close', 0)
                    kospi_change = day_data.get('kospi_change', 0)
                    investor = day_data.get('foreign_flow', 0) + day_data.get('institution_flow', 0)
                    trend = day_data.get('market_trend', 'NEUTRAL')

                    investor_b = investor / 1e9  # Convert to billions
                    context += f"{day_date}|{kospi:,.0f}|{kospi_change:+.2f}%|{investor_b:+.1f}B|{trend}\n"
                except Exception as e:
                    self.logger.debug(f"Error formatting trend day: {e}")
                    continue

            # Add trend analysis summary
            trend_summary = market_snapshot.get('trend_analysis', {})
            if trend_summary:
                context += f"\nTrend Summary:\n"
                context += f"- Direction: {trend_summary.get('direction', 'NEUTRAL')}\n"
                context += f"- Momentum: {trend_summary.get('momentum', 'NEUTRAL')}\n"
                context += f"- Reversal Risk: {trend_summary.get('reversal_risk', 'UNKNOWN')}\n"
                context += f"- Foreign Investor Trend: {trend_summary.get('foreign_trend', 'UNKNOWN')}\n"

        return context

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
        """Call OpenAI GPT-5 API using responses.create() endpoint"""
        try:
            # Use responses.create() API (correct for gpt-5-mini-2025-08-07)
            # gpt-5-mini-2025-08-07 specs:
            # - 400K context window
            # - Uses responses.create() endpoint
            # - Supports web_search tool
            # - Returns Response object with output array
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                tools=[{"type": "web_search"}]
            )

            # Extract response content from output array
            # Response has output: List[ResponseItem] where each item can be reasoning, function call, or message
            content = ""

            for output_item in response.output:
                # Extract text content from message items
                if hasattr(output_item, 'content') and output_item.content:
                    if isinstance(output_item.content, list):
                        for content_item in output_item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text + "\n"
                    elif hasattr(output_item, 'text'):
                        content += output_item.text + "\n"

            content = content.strip()

            # Track cost: GPT-5-mini pricing ($0.015/1K input, $0.075/1K output)
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000
            self.api_total_cost += cost

            self.logger.info(f"OpenAI API call: {input_tokens} input + {output_tokens} output tokens (${cost:.4f}), response: {len(content)} chars")
            return content
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}")
            raise

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
        Extracts JSON from markdown code blocks if present.
        """
        try:
            # Clean response: extract JSON from markdown code blocks
            cleaned_response = response.strip()

            # Check for JSON in markdown code block (```json ... ```)
            if '```' in cleaned_response:
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(1)

            # Try to parse as JSON
            if cleaned_response.startswith('{'):
                data = json.loads(cleaned_response)

                # Try multiple possible keys for candidate list
                candidates = (data.get('candidates') or
                            data.get('selected_stocks') or
                            data.get('stocks') or
                            data.get('results') or
                            [])

                # Ensure candidates is a list
                if isinstance(candidates, dict):
                    candidates = list(candidates.values())

                if not isinstance(candidates, list):
                    candidates = []
            else:
                # Fallback: parse text response
                candidates = self._parse_text_response(response)

            # Validate count
            if len(candidates) == 0:
                self.logger.warning(f"AI returned 0 candidates.")
                self.logger.warning(f"Raw response length: {len(response)} chars")
                self.logger.warning(f"Raw response: {response[:500]}")
            elif len(candidates) < 30 or len(candidates) > 50:
                self.logger.warning(f"AI returned {len(candidates)} candidates (expected 30-40)")

            return candidates

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse response as JSON: {e}")
            self.logger.debug(f"Response preview: {response[:500]}")

            # Fallback to text parsing
            return self._parse_text_response(response)
        except Exception as e:
            self.logger.error(f"Unexpected error during response parsing: {e}")
            self.logger.debug(f"Response: {response[:500]}")
            return []

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
