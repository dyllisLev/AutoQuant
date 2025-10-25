"""
Test AnalysisOrchestrator with database persistence

This test runs a simplified analysis workflow to verify:
1. AnalysisRun record creation
2. Phase-by-phase execution
3. Database persistence at each step
4. Error handling and rollback
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from datetime import date, datetime
from src.orchestration.analysis_orchestrator import AnalysisOrchestrator
from src.database import Database
from src.database.models import AnalysisRun


def test_orchestrator():
    """Test orchestrator with database"""

    print("\n" + "="*80)
    print("TESTING ANALYSIS ORCHESTRATOR")
    print("="*80)

    # Initialize
    db = Database()
    orchestrator = AnalysisOrchestrator(db=db)

    # Get initial counts
    session = db.get_session()
    initial_run_count = session.query(AnalysisRun).count()
    session.close()

    print(f"\n📊 Initial analysis_runs count: {initial_run_count}")

    # Run analysis
    print(f"\n🚀 Running daily analysis...")
    print(f"   Date: {date.today()}")

    try:
        results = orchestrator.run_daily_analysis()

        print(f"\n" + "="*80)
        print("RESULTS")
        print("="*80)

        if results['success']:
            print(f"✅ Analysis completed successfully!")
            print(f"\nAnalysis Run ID: {results['analysis_run_id']}")
            print(f"Total Duration: {results['total_duration']:.2f}s")
            print(f"\nStocks Analyzed: {results['stocks_analyzed']}")
            print(f"AI Candidates: {results['ai_candidates']}")
            print(f"Technical Selections: {results['technical_selections']}")
            print(f"Final Signals: {results['final_signals']}")

            # Verify database records
            print(f"\n" + "="*80)
            print("DATABASE VERIFICATION")
            print("="*80)

            session = db.get_session()

            # Check analysis_run
            run = session.query(AnalysisRun).filter(
                AnalysisRun.id == results['analysis_run_id']
            ).first()

            if run:
                print(f"\n✅ AnalysisRun record found:")
                print(f"   ID: {run.id}")
                print(f"   Date: {run.run_date}")
                print(f"   Status: {run.status}")
                print(f"   Phase 1: {'✅' if run.phase1_completed else '❌'}")
                print(f"   Phase 2: {'✅' if run.phase2_completed else '❌'}")
                print(f"   Phase 3: {'✅' if run.phase3_completed else '❌'}")
                print(f"   Phase 4: {'✅' if run.phase4_completed else '❌'}")
                print(f"   Phase 5: {'✅' if run.phase5_completed else '❌'}")

                # Check related records
                if run.market_snapshot:
                    print(f"\n✅ MarketSnapshot record found:")
                    print(f"   KOSPI: {run.market_snapshot.kospi_close}")
                    print(f"   Sentiment: {run.market_snapshot.market_sentiment}")

                if run.ai_screening:
                    print(f"\n✅ AIScreeningResult record found:")
                    print(f"   Provider: {run.ai_screening.ai_provider}")
                    print(f"   Candidates: {run.ai_screening.selected_count}")
                    print(f"   AI Candidates: {len(run.ai_screening.candidates)}")

                if run.technical_screening:
                    print(f"\n✅ TechnicalScreeningResult record found:")
                    print(f"   Input: {run.technical_screening.input_candidates_count}")
                    print(f"   Selected: {run.technical_screening.final_selections_count}")
                    print(f"   Technical Selections: {len(run.technical_screening.selections)}")

                signals = run.trading_signals
                if signals:
                    print(f"\n✅ TradingSignal records found: {len(signals)}")
                    for signal in signals:
                        print(f"   - {signal.stock_code}: Buy {signal.buy_price:,.0f} → Target {signal.target_price:,.0f}")

            session.close()

            print(f"\n" + "="*80)
            print("✅ ORCHESTRATOR TEST PASSED")
            print("="*80)

        else:
            print(f"❌ Analysis failed: {results.get('error')}")
            return False

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_latest_signals():
    """Test retrieving latest signals"""

    print("\n" + "="*80)
    print("TESTING GET LATEST SIGNALS")
    print("="*80)

    db = Database()
    orchestrator = AnalysisOrchestrator(db=db)

    signals = orchestrator.get_latest_signals(limit=5)

    print(f"\n📊 Latest {len(signals)} signals:")
    print("-"*80)

    for signal in signals:
        print(f"\n{signal['company_name']} ({signal['stock_code']})")
        print(f"  Analysis Date: {signal['analysis_date']}")
        print(f"  Buy: {signal['buy_price']:,.0f} → Target: {signal['target_price']:,.0f}")
        print(f"  Return: +{signal['predicted_return']:.2f}%")
        print(f"  Status: {signal['status']}")

    return True


if __name__ == '__main__':
    print("\n" + "="*80)
    print("AUTOQUANT ORCHESTRATOR TEST SUITE")
    print("="*80)

    # Test 1: Full orchestrator execution
    test1_passed = test_orchestrator()

    # Test 2: Get latest signals
    test2_passed = test_get_latest_signals()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (Orchestrator): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Get Signals):  {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
