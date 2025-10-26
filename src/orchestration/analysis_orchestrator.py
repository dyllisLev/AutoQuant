"""
AnalysisOrchestrator - Manages complete analysis workflow from Phase 2 to Phase 5

This orchestrator:
1. Creates and manages analysis_run records
2. Executes phases in order with error handling
3. Persists all intermediate results to database
4. Tracks execution times and completion status
5. Provides rollback on failure
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import time
from loguru import logger
from sqlalchemy.orm import Session

from src.database import Database
from src.database.models import (
    AnalysisRun, MarketSnapshot, AIScreeningResult, AICandidate,
    TechnicalScreeningResult, TechnicalSelection, TradingSignal
)
from src.screening.market_analyzer import MarketAnalyzer
from src.screening.ai_screener import AIScreener
from src.analysis.technical_screener import TechnicalScreener
from src.pricing.price_calculator import PriceCalculator


class AnalysisOrchestrator:
    """
    Orchestrates complete daily analysis workflow with database persistence
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize orchestrator

        Args:
            db: Database instance (creates new if not provided)
        """
        self.db = db or Database()
        self.market_analyzer = MarketAnalyzer()
        self.ai_screener = AIScreener()
        self.technical_screener = TechnicalScreener()
        self.price_calculator = PriceCalculator(db=self.db)

    def run_daily_analysis(
        self,
        analysis_date: Optional[date] = None,
        target_trade_date: Optional[date] = None
    ) -> Dict:
        """
        Run complete daily analysis workflow

        Args:
            analysis_date: Date of analysis (default: today)
            target_trade_date: Target trading date (default: next business day)

        Returns:
            Dict with analysis results and database IDs
        """
        analysis_date = analysis_date or date.today()
        target_trade_date = target_trade_date or self._get_next_business_day(analysis_date)

        logger.info(f"🚀 Starting daily analysis for {analysis_date}")
        logger.info(f"   Target trade date: {target_trade_date}")

        # Create analysis run record
        session = self.db.get_session()
        analysis_run = None

        try:
            # Initialize analysis run
            analysis_run = AnalysisRun(
                run_date=analysis_date,
                target_trade_date=target_trade_date,
                status='running',
                start_time=datetime.now()
            )
            session.add(analysis_run)
            session.commit()
            logger.info(f"✅ Created analysis_run (ID: {analysis_run.id})")

            # Phase 1: Data Collection (already done by KIS DB)
            logger.info(f"\n{'='*80}")
            logger.info("PHASE 1: DATA COLLECTION")
            logger.info(f"{'='*80}")
            stocks_count = self.db.get_available_symbols_count_from_kis()
            analysis_run.total_stocks_analyzed = stocks_count
            analysis_run.phase1_completed = True
            session.commit()
            logger.info(f"✅ Phase 1 complete: {stocks_count} stocks available")

            # Phase 2: Market Analysis
            logger.info(f"\n{'='*80}")
            logger.info("PHASE 2: MARKET ANALYSIS")
            logger.info(f"{'='*80}")
            phase2_start = time.time()
            market_data = self._run_phase2_market_analysis(session, analysis_run, analysis_date)
            phase2_duration = time.time() - phase2_start
            analysis_run.phase2_completed = True
            session.commit()
            logger.info(f"✅ Phase 2 complete ({phase2_duration:.2f}s)")

            # Phase 3: AI Screening
            logger.info(f"\n{'='*80}")
            logger.info("PHASE 3: AI SCREENING")
            logger.info(f"{'='*80}")
            phase3_start = time.time()
            ai_data = self._run_phase3_ai_screening(session, analysis_run, analysis_date, market_data)
            phase3_duration = time.time() - phase3_start
            analysis_run.ai_candidates_count = len(ai_data['candidates'])
            analysis_run.phase3_completed = True
            session.commit()
            logger.info(f"✅ Phase 3 complete ({phase3_duration:.2f}s): {len(ai_data['candidates'])} candidates")

            # Phase 4: Technical Screening
            logger.info(f"\n{'='*80}")
            logger.info("PHASE 4: TECHNICAL SCREENING")
            logger.info(f"{'='*80}")
            phase4_start = time.time()
            tech_data = self._run_phase4_technical_screening(session, analysis_run, analysis_date, ai_data['candidates'])
            phase4_duration = time.time() - phase4_start
            analysis_run.technical_selections_count = len(tech_data['selections'])
            analysis_run.phase4_completed = True
            session.commit()
            logger.info(f"✅ Phase 4 complete ({phase4_duration:.2f}s): {len(tech_data['selections'])} selections")

            # Phase 5: Price Calculation & Signal Generation
            logger.info(f"\n{'='*80}")
            logger.info("PHASE 5: PRICE CALCULATION")
            logger.info(f"{'='*80}")
            phase5_start = time.time()
            signals = self._run_phase5_price_calculation(
                session, analysis_run, analysis_date, target_trade_date,
                tech_data['selections'], tech_data['selection_records']
            )
            phase5_duration = time.time() - phase5_start
            analysis_run.final_signals_count = len(signals)
            analysis_run.phase5_completed = True
            session.commit()
            logger.info(f"✅ Phase 5 complete ({phase5_duration:.2f}s): {len(signals)} signals")

            # Complete analysis run
            analysis_run.status = 'completed'
            analysis_run.end_time = datetime.now()
            analysis_run.total_duration_seconds = (analysis_run.end_time - analysis_run.start_time).total_seconds()
            session.commit()

            logger.info(f"\n{'='*80}")
            logger.info("✅ ANALYSIS COMPLETED SUCCESSFULLY")
            logger.info(f"{'='*80}")
            logger.info(f"Total duration: {analysis_run.total_duration_seconds:.2f}s")
            logger.info(f"Stocks analyzed: {analysis_run.total_stocks_analyzed}")
            logger.info(f"AI candidates: {analysis_run.ai_candidates_count}")
            logger.info(f"Technical selections: {analysis_run.technical_selections_count}")
            logger.info(f"Final signals: {analysis_run.final_signals_count}")

            return {
                'success': True,
                'analysis_run_id': analysis_run.id,
                'run_date': str(analysis_date),
                'target_trade_date': str(target_trade_date),
                'total_duration': analysis_run.total_duration_seconds,
                'stocks_analyzed': analysis_run.total_stocks_analyzed,
                'ai_candidates': analysis_run.ai_candidates_count,
                'technical_selections': analysis_run.technical_selections_count,
                'final_signals': analysis_run.final_signals_count,
                'market_sentiment': market_data.get('market_sentiment'),
                'signals': signals
            }

        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()

            if analysis_run:
                analysis_run.status = 'failed'
                analysis_run.error_message = str(e)
                analysis_run.error_phase = self._get_current_phase(analysis_run)
                analysis_run.end_time = datetime.now()
                if analysis_run.start_time:
                    analysis_run.total_duration_seconds = (analysis_run.end_time - analysis_run.start_time).total_seconds()
                session.commit()

            return {
                'success': False,
                'error': str(e),
                'analysis_run_id': analysis_run.id if analysis_run else None
            }

        finally:
            session.close()

    def _run_phase2_market_analysis(
        self,
        session: Session,
        analysis_run: AnalysisRun,
        analysis_date: date
    ) -> Dict:
        """Phase 2: Market Analysis with persistence"""

        # Run market analysis
        market_data = self.market_analyzer.analyze_market(target_date=analysis_date)

        # Save to database (market_data has flat structure)
        snapshot = MarketSnapshot(
            analysis_run_id=analysis_run.id,
            snapshot_date=analysis_date,
            kospi_close=market_data['kospi_close'],
            kospi_change_pct=market_data['kospi_change'],
            kospi_volume=market_data.get('kospi_volume'),
            kospi_trend=market_data.get('market_trend', 'NEUTRAL'),
            kosdaq_close=market_data['kosdaq_close'],
            kosdaq_change_pct=market_data['kosdaq_change'],
            kosdaq_volume=market_data.get('kosdaq_volume'),
            kosdaq_trend=market_data.get('market_trend', 'NEUTRAL'),  # Same trend for both
            foreign_net_buy=market_data.get('foreign_flow'),
            institution_net_buy=market_data.get('institution_flow'),
            retail_net_buy=market_data.get('retail_flow'),
            momentum_score=market_data.get('momentum_score', 50.0),
            market_sentiment=market_data.get('market_sentiment', 'NEUTRAL'),
            sector_performance=market_data.get('sector_performance', {})
        )
        session.add(snapshot)
        session.commit()

        logger.info(f"   💾 Saved market snapshot (ID: {snapshot.id})")
        logger.info(f"   KOSPI: {snapshot.kospi_close} ({snapshot.kospi_change_pct:+.2f}%)")
        logger.info(f"   Sentiment: {snapshot.market_sentiment}, Momentum: {snapshot.momentum_score:.1f}")

        return market_data

    def _run_phase3_ai_screening(
        self,
        session: Session,
        analysis_run: AnalysisRun,
        analysis_date: date,
        market_data: Dict
    ) -> Dict:
        """Phase 3: AI Screening with persistence - OPTIMIZED with sector info and korean names"""

        phase_start = time.time()

        # Get available stocks from KIS DB
        available_stock_codes = self.db.get_available_symbols_from_kis()
        logger.info(f"   Total stocks from KIS DB: {len(available_stock_codes)}")

        # Prepare stock data DataFrame for AIScreener
        import pandas as pd
        import os
        from src.utils import SectorMapper
        from sqlalchemy import text

        # Initialize sector mapper
        sector_mapper = SectorMapper()

        # Build comprehensive stock data with OPTIMIZED query (2 days only, no RSI)
        stocks_data = []

        # Get stock info (korean_name, sector) in batch
        logger.info(f"   📋 Loading stock info (korean_name, sector) from stock_info tables...")

        # Query KOSPI stock info
        kospi_info_query = text("""
            SELECT short_code, korean_name, index_sector_large_code, index_sector_medium_code
            FROM kospi_stock_info
        """)
        kospi_info_result = session.execute(kospi_info_query)
        kospi_info_dict = {
            row[0]: {
                'korean_name': row[1],
                'sector_large': row[2],
                'sector_medium': row[3]
            }
            for row in kospi_info_result
        }

        # Query KOSDAQ stock info
        kosdaq_info_query = text("""
            SELECT short_code, korean_name, index_sector_large_code, index_sector_medium_code
            FROM kosdaq_stock_info
        """)
        kosdaq_info_result = session.execute(kosdaq_info_query)
        kosdaq_info_dict = {
            row[0]: {
                'korean_name': row[1],
                'sector_large': row[2],
                'sector_medium': row[3]
            }
            for row in kosdaq_info_result
        }

        # Merge KOSPI and KOSDAQ info
        all_stock_info = {**kospi_info_dict, **kosdaq_info_dict}
        logger.info(f"   ✅ Loaded stock info for {len(all_stock_info)} stocks")

        # FULLY OPTIMIZED: Batch query for ONLY latest day (2760개 쿼리 → 1개 쿼리)
        logger.info(f"   📊 Batch querying latest day OHLCV data for ALL stocks...")

        # ONE database query for all stocks on analysis_date
        all_ohlcv_df = self.db.get_daily_ohlcv_batch_from_kis(
            start_date=analysis_date,
            end_date=analysis_date
        )

        if all_ohlcv_df.empty:
            logger.error("   ❌ No OHLCV data retrieved from batch query!")
            return {'ai_result_id': None, 'candidates': []}

        logger.info(f"   ✅ Retrieved {len(all_ohlcv_df)} records from batch query")

        # Process each stock from batch results
        for _, row in all_ohlcv_df.iterrows():
            try:
                stock_code = row['symbol_code']

                # Get korean_name and sector from stock_info
                stock_info = all_stock_info.get(stock_code, {})
                korean_name = stock_info.get('korean_name', f'종목_{stock_code}')
                sector_large = stock_info.get('sector_large')
                sector_medium = stock_info.get('sector_medium')
                sector_display = sector_mapper.format_sector_display(sector_large, sector_medium)

                # Build stock record (NO RSI - that's for Phase 4 technical screening)
                # AI doesn't need change_pct - it analyzes absolute values
                stocks_data.append({
                    'code': stock_code,
                    'name': korean_name,
                    'sector': sector_display,
                    'close': float(row['close']),
                    'market_cap': float(row['close'] * row['volume']),  # Approximate
                    'volume': int(row['volume'])
                })

            except Exception as e:
                logger.debug(f"Skipping {row.get('symbol_code', 'unknown')}: {e}")
                continue

        all_stocks_df = pd.DataFrame(stocks_data)
        logger.info(f"   ✅ Prepared stock data: {len(all_stocks_df)} stocks with korean_name + sector (배치 조회)")

        # Initialize AIScreener with provider from environment
        ai_provider = os.getenv("AI_SCREENING_PROVIDER", "openai")
        ai_screener = AIScreener(provider=ai_provider)

        # Call real AI screening
        logger.info(f"   🤖 Calling AI screening API ({ai_provider})...")
        candidates_list, metadata = ai_screener.screen_stocks(
            market_snapshot=market_data,
            all_stocks=all_stocks_df,
            sentiment_confidence=market_data.get('sentiment_confidence', 0.5)
        )

        logger.info(f"   ✅ AI returned {len(candidates_list)} candidates")

        # Create AI screening result with real data
        ai_result = AIScreeningResult(
            analysis_run_id=analysis_run.id,
            screening_date=analysis_date,
            ai_provider=metadata.get('provider', 'unknown'),
            ai_model=metadata.get('model', 'unknown'),
            total_input_stocks=len(all_stocks_df),
            selected_count=len(candidates_list),
            execution_time_seconds=metadata.get('screening_duration_sec', time.time() - phase_start),
            api_cost_usd=metadata.get('api_cost', 0.0),
            prompt_text='Full prompt saved in debug_actual_prompt.txt',  # Saved by AIScreener
            response_text=f"AI selected {len(candidates_list)} stocks based on market conditions",
            response_summary=f"{metadata.get('sentiment', 'UNKNOWN')} market - selected {len(candidates_list)} candidates"
        )
        session.add(ai_result)
        session.flush()  # Get ID

        logger.info(f"   💾 Saved AI screening result (ID: {ai_result.id})")

        # Save individual candidates from AI response
        candidate_records = []
        for candidate_dict in candidates_list:
            stock_code = candidate_dict.get('code', '')
            confidence = candidate_dict.get('confidence', 50)
            reason = candidate_dict.get('reason', 'AI selected')

            # Get stock details from all_stocks_df
            stock_row = all_stocks_df[all_stocks_df['code'] == stock_code]
            if stock_row.empty:
                logger.warning(f"   Candidate {stock_code} not in stock data, skipping")
                continue

            stock_info = stock_row.iloc[0]

            candidate = AICandidate(
                ai_screening_id=ai_result.id,
                stock_code=stock_code,
                company_name=stock_info.get('name', f"Stock_{stock_code}"),
                ai_score=float(confidence),
                ai_reasoning=reason,
                rank_in_batch=len(candidate_records) + 1,
                mentioned_factors=candidate_dict.get('key_indicators', []),
                current_price=float(stock_info['close']),
                sector=stock_info.get('sector', 'Unknown')
            )
            session.add(candidate)
            candidate_records.append(stock_code)

        session.commit()
        logger.info(f"   💾 Saved {len(candidate_records)} AI candidates to database")

        return {
            'ai_result_id': ai_result.id,
            'candidates': candidate_records
        }

    def _run_phase4_technical_screening(
        self,
        session: Session,
        analysis_run: AnalysisRun,
        analysis_date: date,
        ai_candidates: List[str]
    ) -> Dict:
        """Phase 4: Technical Screening with persistence"""

        phase_start = time.time()

        # Run technical screening
        # First convert stock codes to DataFrame format expected by screen()
        import pandas as pd
        candidates_df = pd.DataFrame({
            'stock_code': ai_candidates,
            'company_name': [f"Company {code}" for code in ai_candidates]  # Placeholder names
        })

        selected_stocks = self.technical_screener.screen(
            ai_candidates=candidates_df,
            trading_date=str(analysis_date)
        )

        # Create technical screening result
        tech_result = TechnicalScreeningResult(
            analysis_run_id=analysis_run.id,
            screening_date=analysis_date,
            input_candidates_count=len(ai_candidates),
            final_selections_count=len(selected_stocks),
            execution_time_seconds=time.time() - phase_start,
            min_final_score=50.0,
            max_selections=5
        )
        session.add(tech_result)
        session.flush()  # Get ID

        logger.info(f"   💾 Saved technical screening result (ID: {tech_result.id})")

        # Save individual selections
        selection_records = []
        for _, row in selected_stocks.iterrows():
            selection = TechnicalSelection(
                tech_screening_id=tech_result.id,
                stock_code=row['stock_code'],
                company_name=row.get('company_name', f"Company {row['stock_code']}"),
                current_price=row['current_price'],
                sma_score=row['sma_score'],
                rsi_score=row['rsi_score'],
                macd_score=row['macd_score'],
                bb_score=row['bb_score'],
                volume_score=row['volume_score'],
                final_score=row['final_score'],
                indicators=row.get('indicators', {}),
                rank_in_batch=row.get('rank', 0),
                selection_reason=f"Technical score: {row['final_score']:.1f}/70"
            )
            session.add(selection)
            selection_records.append(selection)

        session.commit()
        logger.info(f"   💾 Saved {len(selection_records)} technical selections")

        return {
            'tech_result_id': tech_result.id,
            'selections': selected_stocks,
            'selection_records': selection_records
        }

    def _run_phase5_price_calculation(
        self,
        session: Session,
        analysis_run: AnalysisRun,
        analysis_date: date,
        target_trade_date: date,
        selected_stocks: 'DataFrame',
        tech_selection_records: List[TechnicalSelection]
    ) -> List[Dict]:
        """Phase 5: Price Calculation with persistence"""

        # Calculate prices for all selected stocks
        signals_data = []

        for idx, row in selected_stocks.iterrows():
            try:
                stock_code = row['stock_code']
                current_price = row['current_price']

                # Get OHLCV data for price calculation
                ohlcv_df = self.db.get_daily_ohlcv_from_kis(
                    stock_code,
                    start_date=datetime.now() - timedelta(days=200),
                    end_date=datetime.now()
                )

                if ohlcv_df is None or len(ohlcv_df) < 60:
                    logger.warning(f"   ⚠️  Insufficient data for {stock_code}, skipping")
                    continue

                # Rename columns to match TechnicalIndicators expectations (KIS DB uses lowercase)
                ohlcv_df = ohlcv_df.copy()
                ohlcv_df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)

                # Convert Decimal to float
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in ohlcv_df.columns:
                        ohlcv_df[col] = ohlcv_df[col].astype(float)

                # Add technical indicators
                from src.analysis.technical_indicators import TechnicalIndicators
                tech_indicators = TechnicalIndicators()
                ohlcv_with_indicators = tech_indicators.add_all_indicators(ohlcv_df)

                # Calculate prices
                prices = self.price_calculator.calculate_prices(
                    stock_code=stock_code,
                    current_price=current_price,
                    technical_data=ohlcv_with_indicators,
                    prediction_days=7
                )

                # Find corresponding tech_selection record
                tech_selection_id = None
                for selection in tech_selection_records:
                    if selection.stock_code == stock_code:
                        tech_selection_id = selection.id
                        break

                # Helper function to convert numpy types to Python types
                def to_python_type(value):
                    """Convert numpy types to Python native types for database storage"""
                    import numpy as np
                    if isinstance(value, (np.integer, np.floating)):
                        return float(value)
                    return value

                # Create trading signal (convert numpy types to Python floats)
                signal = TradingSignal(
                    analysis_run_id=analysis_run.id,
                    tech_selection_id=tech_selection_id,
                    stock_id=None,  # Would link to stocks table if exists
                    stock_code=stock_code,
                    company_name=row.get('company_name', f"Company {stock_code}"),
                    analysis_date=analysis_date,
                    target_trade_date=target_trade_date,
                    current_price=to_python_type(prices['current_price']),
                    buy_price=to_python_type(prices['buy_price']),
                    target_price=to_python_type(prices['target_price']),
                    stop_loss_price=to_python_type(prices['stop_loss_price']),
                    predicted_return=to_python_type(prices['predicted_return']),
                    risk_reward_ratio=to_python_type(prices['risk_reward_ratio']),
                    ai_confidence=to_python_type(prices['ai_confidence']),
                    support_level=to_python_type(prices['support_level']),
                    resistance_level=to_python_type(prices['resistance_level']),
                    pivot_point=to_python_type(prices['pivot_point']),
                    atr=to_python_type(prices['atr']),
                    calculation_details=prices.get('calculation_details', {}),
                    status='pending'
                )
                session.add(signal)

                signals_data.append({
                    'stock_code': stock_code,
                    'company_name': signal.company_name,
                    'buy_price': signal.buy_price,
                    'target_price': signal.target_price,
                    'stop_loss_price': signal.stop_loss_price,
                    'predicted_return': signal.predicted_return,
                    'risk_reward_ratio': signal.risk_reward_ratio
                })

                logger.info(f"   💾 Created signal for {stock_code}: Buy {signal.buy_price:,.0f} → Target {signal.target_price:,.0f}")

            except Exception as e:
                logger.error(f"   ❌ Failed to calculate prices for {stock_code}: {str(e)}")
                continue

        session.commit()
        logger.info(f"   💾 Saved {len(signals_data)} trading signals")

        return signals_data

    def _get_current_phase(self, analysis_run: AnalysisRun) -> str:
        """Determine current phase from completion flags"""
        if not analysis_run.phase1_completed:
            return 'phase1_data_collection'
        elif not analysis_run.phase2_completed:
            return 'phase2_market_analysis'
        elif not analysis_run.phase3_completed:
            return 'phase3_ai_screening'
        elif not analysis_run.phase4_completed:
            return 'phase4_technical_screening'
        elif not analysis_run.phase5_completed:
            return 'phase5_price_calculation'
        return 'unknown'

    def _get_next_business_day(self, from_date: date) -> date:
        """Get next business day (skip weekends)"""
        next_day = from_date + timedelta(days=1)
        # Skip Saturday (5) and Sunday (6)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    def get_latest_signals(self, limit: int = 10) -> List[Dict]:
        """
        Get latest trading signals

        Args:
            limit: Maximum number of signals to return

        Returns:
            List of signal dictionaries
        """
        session = self.db.get_session()
        try:
            signals = session.query(TradingSignal).filter(
                TradingSignal.status == 'pending'
            ).order_by(
                TradingSignal.created_at.desc()
            ).limit(limit).all()

            return [{
                'id': s.id,
                'stock_code': s.stock_code,
                'company_name': s.company_name,
                'analysis_date': str(s.analysis_date),
                'target_trade_date': str(s.target_trade_date),
                'buy_price': s.buy_price,
                'target_price': s.target_price,
                'stop_loss_price': s.stop_loss_price,
                'predicted_return': s.predicted_return,
                'risk_reward_ratio': s.risk_reward_ratio,
                'ai_confidence': s.ai_confidence,
                'status': s.status
            } for s in signals]

        finally:
            session.close()
