#!/usr/bin/env python3
"""
Daily Analysis Script - Main entry point for AutoQuant system

This script runs the complete analysis workflow:
1. Market Analysis (Phase 2)
2. AI Screening (Phase 3)
3. Technical Screening (Phase 4)
4. Price Calculation (Phase 5)
5. Trading Signal Generation

All results are saved to database for web monitoring and external trading execution.

Usage:
    # Run for today
    python scripts/daily_analysis.py

    # Run for specific date
    python scripts/daily_analysis.py --date 2025-10-25

    # Dry run (no database save)
    python scripts/daily_analysis.py --dry-run

Scheduling:
    # Add to crontab for daily 3:45 PM KST execution
    45 15 * * 1-5 cd /opt/AutoQuant && /opt/AutoQuant/venv/bin/python scripts/daily_analysis.py

SSH Execution:
    ssh user@host "cd /opt/AutoQuant && source venv/bin/activate && python scripts/daily_analysis.py"
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

import argparse
from datetime import datetime, date
from loguru import logger
import json

from src.orchestration.analysis_orchestrator import AnalysisOrchestrator
from src.database import Database


def setup_logging(log_file: str = None):
    """Setup logging configuration"""
    logger.remove()  # Remove default handler

    # Console handler (INFO level)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # File handler (DEBUG level) if specified
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days"
        )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='AutoQuant Daily Analysis - AI-based Stock Signal Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--date',
        type=str,
        help='Analysis date (YYYY-MM-DD format, default: today)',
        default=None
    )

    parser.add_argument(
        '--target-date',
        type=str,
        help='Target trade date (YYYY-MM-DD format, default: next business day)',
        default=None
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no database save)',
        default=False
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path (default: logs/daily_analysis_YYYYMMDD.log)',
        default=None
    )

    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results as JSON',
        default=False
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging',
        default=False
    )

    return parser.parse_args()


def print_banner():
    """Print startup banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     █████╗ ██╗   ██╗████████╗ ██████╗  ██████╗ ██╗   ██╗ █████╗     ║
║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔═══██╗██║   ██║██╔══██╗    ║
║    ███████║██║   ██║   ██║   ██║   ██║██║   ██║██║   ██║███████║    ║
║    ██╔══██║██║   ██║   ██║   ██║   ██║██║   ██║██║   ██║██╔══██║    ║
║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║    ║
║    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ║
║                                                                       ║
║                AI-Based Pre-Market Analysis System                   ║
║                    Daily Signal Generation                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_results(results: dict, json_output: bool = False):
    """Print analysis results"""

    if json_output:
        # JSON output for programmatic consumption
        print(json.dumps(results, indent=2, default=str))
        return

    # Human-readable output
    print("\n" + "=" * 80)
    print("DAILY ANALYSIS RESULTS")
    print("=" * 80)

    if results['success']:
        print(f"\n✅ Analysis completed successfully")
        print(f"\nRun Information:")
        print(f"  Analysis Date:       {results['run_date']}")
        print(f"  Target Trade Date:   {results['target_trade_date']}")
        print(f"  Total Duration:      {results['total_duration']:.2f} seconds")
        print(f"  Database Run ID:     {results['analysis_run_id']}")

        print(f"\nAnalysis Summary:")
        print(f"  Stocks Analyzed:     {results['stocks_analyzed']:,}")
        print(f"  AI Candidates:       {results['ai_candidates']}")
        print(f"  Technical Selections: {results['technical_selections']}")
        print(f"  Final Signals:       {results['final_signals']}")
        print(f"  Market Sentiment:    {results.get('market_sentiment', 'N/A')}")

        if results.get('signals'):
            print(f"\n📊 Generated Trading Signals:")
            print("-" * 80)
            for i, signal in enumerate(results['signals'], 1):
                print(f"\n{i}. {signal['company_name']} ({signal['stock_code']})")
                print(f"   Buy:    {signal['buy_price']:>10,.0f} KRW")
                print(f"   Target: {signal['target_price']:>10,.0f} KRW  (+{signal['predicted_return']:>5.2f}%)")
                print(f"   Stop:   {signal['stop_loss_price']:>10,.0f} KRW")
                print(f"   R/R:    {signal['risk_reward_ratio']:>5.2f}:1")

        print("\n" + "=" * 80)
        print("✅ Signals saved to database and ready for trading execution")
        print("=" * 80)

    else:
        print(f"\n❌ Analysis failed")
        print(f"Error: {results.get('error', 'Unknown error')}")
        if results.get('analysis_run_id'):
            print(f"Run ID: {results['analysis_run_id']} (marked as failed in database)")


def main():
    """Main execution function"""

    # Parse arguments
    args = parse_args()

    # Setup logging
    log_file = args.log_file
    if not log_file and not args.dry_run:
        from pathlib import Path
        log_dir = Path('/opt/AutoQuant/logs')
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"daily_analysis_{datetime.now().strftime('%Y%m%d')}.log"

    setup_logging(log_file=str(log_file) if log_file else None)

    # Print banner
    if not args.json_output:
        print_banner()

    # Check database connection FIRST (needed for auto-date detection)
    try:
        db = Database()
        logger.info(f"Database connected: {db._get_db_url_from_env()}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        sys.exit(1)

    # Parse dates
    analysis_date = None
    if args.date:
        try:
            analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        # AUTO-DETECT: Use latest available trading date from DB
        from sqlalchemy import text
        session = db.get_session()
        try:
            result = session.execute(text('SELECT MAX(trade_date) FROM daily_ohlcv'))
            max_date = result.scalar()
            if max_date:
                analysis_date = max_date
                logger.info(f"📅 Auto-detected latest trading date from DB: {analysis_date}")
            else:
                logger.error("No trading data found in database!")
                sys.exit(1)
        finally:
            session.close()

    target_trade_date = None
    if args.target_date:
        try:
            target_trade_date = datetime.strptime(args.target_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid target date format: {args.target_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Log execution info
    logger.info(f"Execution mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    logger.info(f"Analysis date: {analysis_date}")
    logger.info(f"Target trade date: {target_trade_date or 'AUTO (next business day)'}")
    if log_file:
        logger.info(f"Log file: {log_file}")

    # Run analysis
    try:
        logger.info("Starting analysis orchestration...")
        orchestrator = AnalysisOrchestrator(db=db)

        if args.dry_run:
            logger.warning("DRY RUN MODE - No database save")
            # In dry run, would run analysis but not save to DB
            # For now, just exit
            logger.info("Dry run mode not fully implemented yet")
            sys.exit(0)

        # Run actual analysis
        results = orchestrator.run_daily_analysis(
            analysis_date=analysis_date,
            target_trade_date=target_trade_date
        )

        # Print results
        print_results(results, json_output=args.json_output)

        # Exit code
        sys.exit(0 if results['success'] else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Analysis interrupted by user (Ctrl+C)")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
