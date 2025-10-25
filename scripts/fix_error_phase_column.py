#!/usr/bin/env python3
"""
Fix error_phase column size in analysis_runs table
Increase from VARCHAR(20) to VARCHAR(50)
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database import Database
from loguru import logger
from sqlalchemy import text

def main():
    logger.info("Fixing error_phase column size...")

    db = Database()

    # Run ALTER TABLE
    sql = text("ALTER TABLE analysis_runs ALTER COLUMN error_phase TYPE VARCHAR(50)")

    try:
        with db.engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        logger.info("✅ Successfully increased error_phase column to VARCHAR(50)")
        return 0
    except Exception as e:
        logger.error(f"❌ Failed to alter column: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
