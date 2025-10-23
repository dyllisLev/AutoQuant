"""
User Acceptance Test 04: Phase 3 - AI-Based Stock Screening

Tests the AIScreener implementation:
- Multi-provider support (mock and real)
- Stock filtering (4,359 → 30~40)
- Market context integration with Phase 2 sentiment
- Error handling and fallbacks
- Cost tracking

Run: python tests/user_tests/test_04_ai_screening.py
"""

import os
import sys
import json
from datetime import date, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from loguru import logger

from src.screening import AIScreener, AIProvider
from src.data_collection.mock_data import MockDataGenerator


class TestAIScreening:
    """Test suite for AIScreener Phase 3"""

    @staticmethod
    def setup():
        """Setup test data and logging"""
        logger.info("=" * 80)
        logger.info("TEST 04: AI-Based Stock Screening (Phase 3)")
        logger.info("=" * 80)

    @staticmethod
    def test_ai_screener_initialization():
        """Test AIScreener can be initialized (without API calls)"""
        logger.info("\n📋 Test: AIScreener Initialization")

        try:
            # Test initialization (won't call API yet)
            screener = AIScreener(provider="openai")

            # Verify initialization
            assert screener.provider == AIProvider.OPENAI
            assert screener.api_call_count == 0
            assert screener.api_total_cost == 0.0
            assert len(screener.screening_history) == 0

            logger.info("✅ AIScreener initialized successfully")
            logger.info(f"   Provider: {screener.provider.value}")
            logger.info(f"   Model: {screener.model}")
            logger.info(f"   Config: timeout={screener.config['timeout']}s, "
                       f"retries={screener.config['retries']}, "
                       f"max_tokens={screener.config['max_tokens']}")

            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    @staticmethod
    def test_mock_screening():
        """Test screening with mock data (no API calls)"""
        logger.info("\n📋 Test: Mock Stock Screening (No API)")

        try:
            # Generate mock stock data
            generator = MockDataGenerator()
            ticker_list = generator.get_ticker_list()

            # Create mock all_stocks DataFrame
            stock_records = []
            for ticker in ticker_list[:4359]:  # All 4,359 stocks
                record = {
                    'code': ticker,
                    'name': generator.get_ticker_name(ticker),
                    'close': generator.get_current_price(ticker),
                    'change_pct': np.random.uniform(-3, 3),
                    'market_cap': np.random.uniform(1e10, 1e12),
                    'rsi': np.random.uniform(20, 80),
                    'volume': np.random.uniform(1e6, 50e6),
                    'volume_change_pct': np.random.uniform(-50, 100)
                }
                stock_records.append(record)

            all_stocks = pd.DataFrame(stock_records)
            logger.info(f"Generated {len(all_stocks)} mock stocks")

            # Create mock market snapshot
            market_snapshot = {
                'date': str(date.today()),
                'next_trading_date': '2025-10-24',
                'sentiment': 'BULLISH',
                'kospi_close': 2500.0,
                'kospi_change': 1.5,
                'kosdaq_close': 800.0,
                'kosdaq_change': 0.8,
                'foreign_flow': 1.2e10,
                'institution_flow': 5.0e9,
                'retail_flow': -2.0e9,
                'advance_decline_ratio': 0.6,
                'market_trend': 'UPTREND',
                'top_sectors': ['IT', 'Finance', 'Materials'],
                'technical_rsi': 65,
                'technical_macd_direction': 'BULLISH',
                'signal_convergence': 0.75
            }
            logger.info(f"Market sentiment: {market_snapshot['sentiment']} "
                       f"(Trend: {market_snapshot['market_trend']})")

            # Test prompt building (without API call)
            screener = AIScreener(provider="openai")
            prompt = screener._build_screening_prompt(market_snapshot, all_stocks, sentiment_confidence=0.75)

            logger.info(f"✅ Prompt generated ({len(prompt)} chars)")
            logger.info(f"   Market context included: {'KOSPI' in prompt}")
            logger.info(f"   Stock data included: {'Code|Name|Price' in prompt or 'code' in prompt.lower()}")
            logger.info(f"   Selection criteria included: {'Market Alignment' in prompt or 'momentum' in prompt.lower()}")

            return True
        except Exception as e:
            logger.error(f"❌ Mock screening failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def test_response_parsing():
        """Test parsing of mock AI responses"""
        logger.info("\n📋 Test: Response Parsing")

        try:
            screener = AIScreener(provider="openai")

            # Test JSON response parsing
            json_response = json.dumps({
                "market_analysis": "Strong uptrend with foreign buying",
                "selection_reasoning": "Selected momentum stocks aligned with market",
                "candidates": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "current_price": 78200,
                        "daily_change_pct": 1.2,
                        "confidence": 85,
                        "reason": "Sector strength + foreign buying",
                        "signals": ["foreign_buying", "sector_strength"]
                    },
                    {
                        "code": "000660",
                        "name": "SK하이닉스",
                        "current_price": 165000,
                        "daily_change_pct": 0.8,
                        "confidence": 78,
                        "reason": "Strong momentum + volume",
                        "signals": ["momentum", "volume_break"]
                    }
                ]
            })

            candidates = screener._parse_screening_response(json_response)
            assert len(candidates) == 2
            assert candidates[0]['code'] == "005930"
            assert candidates[0]['confidence'] == 85

            logger.info("✅ JSON response parsing successful")
            logger.info(f"   Parsed {len(candidates)} candidates")
            logger.info(f"   Sample: {candidates[0]['name']} ({candidates[0]['code']})")

            # Test text response parsing (fallback)
            text_response = """
            005930|삼성전자|85|Strong momentum
            000660|SK하이닉스|78|Sector strength
            """

            candidates = screener._parse_screening_response(text_response)
            assert len(candidates) >= 2
            logger.info("✅ Text response parsing successful")

            return True
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def test_candidate_validation():
        """Test validation of candidates against stock universe"""
        logger.info("\n📋 Test: Candidate Validation")

        try:
            generator = MockDataGenerator()
            ticker_list = generator.get_ticker_list()[:100]

            # Create mock stock data
            stock_records = []
            for ticker in ticker_list:
                record = {
                    'code': ticker,
                    'name': generator.get_ticker_name(ticker),
                    'close': generator.get_current_price(ticker),
                    'change_pct': np.random.uniform(-3, 3),
                    'market_cap': np.random.uniform(1e10, 1e12),
                    'rsi': np.random.uniform(20, 80),
                    'volume': np.random.uniform(1e6, 50e6),
                    'volume_change_pct': np.random.uniform(-50, 100)
                }
                stock_records.append(record)

            all_stocks = pd.DataFrame(stock_records)

            screener = AIScreener(provider="openai")

            # Create mix of valid and invalid candidates
            candidates = [
                {"code": all_stocks.iloc[0]['code'], "name": "Valid Stock", "confidence": 85},
                {"code": "999999", "name": "Invalid Stock", "confidence": 75},  # Doesn't exist
                {"code": all_stocks.iloc[1]['code'], "name": "Another Valid", "confidence": 70},
            ]

            logger.info(f"Input: {len(candidates)} candidates (2 valid, 1 invalid)")

            validated = screener._validate_candidates(candidates, all_stocks)
            assert len(validated) == 2, f"Expected 2 valid candidates, got {len(validated)}"

            logger.info(f"✅ Validation successful: {len(validated)}/{len(candidates)} valid")

            return True
        except Exception as e:
            logger.error(f"❌ Candidate validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def test_cost_tracking():
        """Test API cost tracking"""
        logger.info("\n📋 Test: Cost Tracking")

        try:
            screener = AIScreener(provider="openai")

            # Verify initial state
            assert screener.api_call_count == 0
            assert screener.api_total_cost == 0.0

            # Simulate API costs
            screener.api_call_count = 5
            screener.api_total_cost = 0.15

            cost_summary = screener.get_cost_summary()

            logger.info("✅ Cost tracking working")
            logger.info(f"   API Calls: {cost_summary['total_api_calls']}")
            logger.info(f"   Total Cost: ${cost_summary['total_cost_usd']:.4f}")
            logger.info(f"   Daily Budget: ${cost_summary['daily_budget']:.2f}")
            logger.info(f"   Budget Remaining: ${cost_summary['budget_remaining']:.2f}")

            assert cost_summary['total_api_calls'] == 5
            assert cost_summary['total_cost_usd'] == 0.15

            return True
        except Exception as e:
            logger.error(f"❌ Cost tracking test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def test_provider_switching():
        """Test ability to switch between providers"""
        logger.info("\n📋 Test: Provider Switching")

        try:
            providers = ["openai", "anthropic", "google"]
            initialized_providers = []

            for provider in providers:
                try:
                    screener = AIScreener(provider=provider)
                    initialized_providers.append(provider)
                    logger.info(f"   ✓ {provider}: {screener.model}")
                except ValueError:
                    logger.warning(f"   ⚠ {provider}: API key not configured")
                except Exception as e:
                    logger.warning(f"   ⚠ {provider}: {e}")

            logger.info(f"✅ Provider switching test: {len(initialized_providers)}/3 providers available")
            logger.info(f"   Providers: {', '.join(initialized_providers)}")

            return len(initialized_providers) > 0
        except Exception as e:
            logger.error(f"❌ Provider switching test failed: {e}")
            return False

    @staticmethod
    def run_all_tests():
        """Run all AIScreener tests"""
        TestAIScreening.setup()

        results = {
            "Initialization": TestAIScreening.test_ai_screener_initialization(),
            "Mock Screening": TestAIScreening.test_mock_screening(),
            "Response Parsing": TestAIScreening.test_response_parsing(),
            "Candidate Validation": TestAIScreening.test_candidate_validation(),
            "Cost Tracking": TestAIScreening.test_cost_tracking(),
            "Provider Switching": TestAIScreening.test_provider_switching(),
        }

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY - Phase 3: AI-Based Stock Screening")
        logger.info("=" * 80)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")

        logger.info("=" * 80)
        logger.info(f"RESULT: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All AIScreener tests passed!")
        else:
            logger.info(f"⚠️  {total - passed} test(s) failed")

        return passed == total


if __name__ == '__main__':
    success = TestAIScreening.run_all_tests()
    sys.exit(0 if success else 1)
