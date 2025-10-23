#!/usr/bin/env python3
"""
데이터 수집 실행 스크립트
매일 자동으로 실행하여 주가 데이터를 수집합니다.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_collection.data_manager import DataCollectionManager


def setup_logger():
    """로거 설정"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"data_collection_{datetime.now().strftime('%Y%m%d')}.log"

    logger.add(
        log_file,
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='주식 데이터 수집 프로그램')

    parser.add_argument(
        '--market',
        type=str,
        default='KOSPI',
        choices=['KOSPI', 'KOSDAQ', 'KONEX', 'ALL'],
        help='시장 선택 (기본값: KOSPI)'
    )

    parser.add_argument(
        '--top-n',
        type=int,
        default=100,
        help='수집할 상위 종목 수 (기본값: 100)'
    )

    parser.add_argument(
        '--tickers',
        type=str,
        nargs='+',
        help='특정 종목코드 리스트 (예: 005930 035720)'
    )

    parser.add_argument(
        '--mode',
        type=str,
        default='daily',
        choices=['daily', 'history', 'overview'],
        help='실행 모드 (daily: 일일수집, history: 히스토리, overview: 시장개요)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=365,
        help='히스토리 모드: 수집할 과거 일수 (기본값: 365)'
    )

    args = parser.parse_args()

    # 로거 설정
    setup_logger()

    logger.info("=" * 60)
    logger.info("주식 데이터 수집 프로그램 시작")
    logger.info(f"실행 시간: {datetime.now()}")
    logger.info(f"모드: {args.mode}")
    logger.info("=" * 60)

    # 데이터 수집 매니저 생성
    manager = DataCollectionManager()

    try:
        if args.mode == 'daily':
            # 일일 데이터 수집
            logger.info("일일 데이터 수집 모드")
            result = manager.collect_daily_data(
                tickers=args.tickers,
                market=args.market,
                top_n=args.top_n
            )

            if result:
                logger.info("데이터 수집 성공")
                # 여기서 데이터베이스에 저장하는 로직 추가 예정
            else:
                logger.error("데이터 수집 실패")

        elif args.mode == 'history':
            # 히스토리 수집
            logger.info("히스토리 수집 모드")

            if not args.tickers:
                logger.error("히스토리 모드는 --tickers 옵션이 필요합니다")
                return

            for ticker in args.tickers:
                logger.info(f"종목 {ticker} 히스토리 수집 중...")
                df = manager.collect_stock_history(ticker, days=args.days)

                if df is not None and not df.empty:
                    logger.info(f"{ticker}: {len(df)} 건 수집")
                else:
                    logger.warning(f"{ticker}: 데이터 없음")

        elif args.mode == 'overview':
            # 시장 개요
            logger.info("시장 개요 모드")
            overview = manager.collect_market_overview(market=args.market)

            logger.info("=" * 60)
            logger.info(f"{args.market} 시장 개요")
            logger.info("-" * 60)
            for key, value in overview.items():
                logger.info(f"{key}: {value}")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        raise

    logger.info("=" * 60)
    logger.info("프로그램 종료")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
