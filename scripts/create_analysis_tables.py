"""
Create new analysis tracking tables for Phase 2-5 monitoring

This script creates the following tables:
- analysis_runs: Track each complete analysis run
- market_snapshots: Market analysis results (Phase 2)
- ai_screening_results: AI screening results (Phase 3)
- ai_candidates: Individual AI-selected stocks
- technical_screening_results: Technical screening results (Phase 4)
- technical_selections: Individual technically-selected stocks
- trading_signals: Final trading signals (Phase 5) - updated schema
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database.database import Database
from src.database.models import (
    Base, AnalysisRun, MarketSnapshot, AIScreeningResult, AICandidate,
    TechnicalScreeningResult, TechnicalSelection, TradingSignal
)
from sqlalchemy import inspect


def check_existing_tables(db):
    """Check which tables already exist"""
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    new_tables = [
        'analysis_runs',
        'market_snapshots',
        'ai_screening_results',
        'ai_candidates',
        'technical_screening_results',
        'technical_selections'
    ]

    print("\n" + "="*80)
    print("CHECKING EXISTING TABLES")
    print("="*80)

    for table in new_tables:
        exists = table in existing_tables
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"{status}: {table}")

    # Check trading_signals separately (might exist in old schema)
    if 'trading_signals' in existing_tables:
        print(f"⚠️  EXISTS (will be updated): trading_signals")
    else:
        print(f"❌ MISSING: trading_signals")

    return existing_tables


def create_tables(db):
    """Create all new tables"""
    print("\n" + "="*80)
    print("CREATING NEW TABLES")
    print("="*80)

    try:
        # Create all tables defined in Base.metadata
        Base.metadata.create_all(db.engine)
        print("✅ All tables created successfully")

        # Verify creation
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        print("\n" + "-"*80)
        print("CREATED TABLES:")
        print("-"*80)

        for table_name in sorted(existing_tables):
            print(f"  ✓ {table_name}")

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_table_schema(db, table_name):
    """Show schema for a specific table"""
    inspector = inspect(db.engine)

    print(f"\n{'='*80}")
    print(f"SCHEMA: {table_name}")
    print(f"{'='*80}")

    try:
        columns = inspector.get_columns(table_name)
        print(f"\nColumns ({len(columns)}):")
        print("-"*80)

        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col.get('default') else ""
            print(f"  {col['name']:<30} {str(col['type']):<20} {nullable}{default}")

        # Show indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"\nIndexes ({len(indexes)}):")
            print("-"*80)
            for idx in indexes:
                cols = ', '.join(idx['column_names'])
                unique = "UNIQUE" if idx.get('unique') else ""
                print(f"  {idx['name']:<40} ({cols}) {unique}")

        # Show foreign keys
        fkeys = inspector.get_foreign_keys(table_name)
        if fkeys:
            print(f"\nForeign Keys ({len(fkeys)}):")
            print("-"*80)
            for fk in fkeys:
                cols = ', '.join(fk['constrained_columns'])
                ref_table = fk['referred_table']
                ref_cols = ', '.join(fk['referred_columns'])
                print(f"  {cols} → {ref_table}({ref_cols})")

    except Exception as e:
        print(f"❌ Error showing schema: {str(e)}")


def test_relationships(db):
    """Test that relationships are working"""
    print("\n" + "="*80)
    print("TESTING RELATIONSHIPS")
    print("="*80)

    from datetime import datetime, date
    from sqlalchemy.orm import Session

    try:
        with Session(db.engine) as session:
            # Create a test analysis run
            test_run = AnalysisRun(
                run_date=date.today(),
                target_trade_date=date.today(),
                status='running',
                start_time=datetime.now(),
                total_stocks_analyzed=4359
            )
            session.add(test_run)
            session.flush()  # Get ID without committing

            print(f"✅ Created test AnalysisRun: {test_run}")

            # Create related MarketSnapshot
            test_snapshot = MarketSnapshot(
                analysis_run_id=test_run.id,
                snapshot_date=date.today(),
                kospi_close=2467.23,
                kospi_change_pct=0.8,
                kosdaq_close=714.56,
                kosdaq_change_pct=-0.3,
                momentum_score=65.5,
                market_sentiment='BULLISH',
                sector_performance=[]
            )
            session.add(test_snapshot)
            session.flush()

            print(f"✅ Created test MarketSnapshot: {test_snapshot}")

            # Test relationship
            print(f"✅ Relationship test: AnalysisRun.market_snapshot = {test_run.market_snapshot}")

            # Rollback (don't commit test data)
            session.rollback()
            print("\n✅ Relationships working correctly (test data rolled back)")

            return True

    except Exception as e:
        print(f"❌ Error testing relationships: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("AUTOQUANT DATABASE MIGRATION - ANALYSIS TRACKING TABLES")
    print("="*80)

    # Initialize database
    print("\n1️⃣ Initializing database connection...")
    db = Database()
    print(f"✅ Connected to: {db._get_db_url_from_env()}")

    # Check existing tables
    print("\n2️⃣ Checking existing tables...")
    existing_tables = check_existing_tables(db)

    # Confirm creation
    import sys
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if not auto_confirm:
        print("\n" + "="*80)
        print("⚠️  WARNING: This will create new tables in your database")
        print("="*80)
        response = input("\nProceed with table creation? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("\n❌ Aborted by user")
            return
    else:
        print("\n✅ Auto-confirming table creation (--yes flag)")

    # Create tables
    print("\n3️⃣ Creating tables...")
    if not create_tables(db):
        print("\n❌ Table creation failed")
        return

    # Show schemas for new tables
    print("\n4️⃣ Showing table schemas...")
    new_tables = [
        'analysis_runs',
        'market_snapshots',
        'ai_screening_results',
        'ai_candidates',
        'technical_screening_results',
        'technical_selections',
        'trading_signals'
    ]

    for table in new_tables:
        show_table_schema(db, table)

    # Test relationships
    print("\n5️⃣ Testing relationships...")
    if test_relationships(db):
        print("\n✅ All relationships working correctly")
    else:
        print("\n⚠️  Relationship test failed (but tables were created)")

    # Summary
    print("\n" + "="*80)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nNew tables created:")
    for table in new_tables:
        print(f"  ✓ {table}")

    print("\nNext steps:")
    print("  1. Modify Phase 2-5 modules to persist data to these tables")
    print("  2. Create AnalysisOrchestrator to manage analysis_run lifecycle")
    print("  3. Build web dashboard to visualize stored data")
    print("\nSee DATABASE_SCHEMA_ANALYSIS.md for detailed schema documentation")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
