#!/usr/bin/env python3
"""
Fix stock_id column in trading_signals table to allow NULL values
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database import Database
from loguru import logger
from sqlalchemy import text

def main():
    logger.info("Making stock_id nullable in trading_signals table...")

    db = Database()

    # Run ALTER TABLE
    sql = text("ALTER TABLE trading_signals ALTER COLUMN stock_id DROP NOT NULL")

    try:
        with db.engine.connect() as conn:
            conn.execute(sql)
            conn.commit()
        logger.info("✅ Successfully made stock_id nullable in trading_signals")
        return 0
    except Exception as e:
        logger.error(f"❌ Failed to alter column: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
