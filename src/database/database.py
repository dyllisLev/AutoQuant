"""
데이터베이스 관리 클래스
PostgreSQL과 SQLite 지원
"""

import os
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
from dotenv import load_dotenv

from .models import Base, Stock, StockPrice, MarketData, Prediction, Trade, Portfolio, BacktestResult

# .env 파일 로드
load_dotenv()


class Database:
    """데이터베이스 관리 클래스 (PostgreSQL & SQLite 지원)"""

    def __init__(self, db_url: str = None, echo: bool = False):
        """
        Args:
            db_url: 데이터베이스 URL (None이면 .env에서 읽음)
            echo: SQL 로그 출력 여부
        """
        # .env에서 DB 설정 읽기
        if db_url is None:
            db_url = self._get_db_url_from_env()

        self.db_url = db_url

        # PostgreSQL 연결 처리
        if db_url.startswith("postgresql"):
            self.engine = create_engine(db_url, echo=echo, pool_pre_ping=True)
        # SQLite 메모리 DB의 경우 특별 처리
        elif ":memory:" in db_url:
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo
            )
        # SQLite 파일 DB
        else:
            self.engine = create_engine(db_url, echo=echo)

        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"데이터베이스 초기화: {db_url}")

    @staticmethod
    def _get_db_url_from_env() -> str:
        """환경변수에서 데이터베이스 URL 구성"""
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

        if db_type == "postgresql":
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "postgres")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")

            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            logger.info(f"PostgreSQL 연결: {db_host}:{db_port}/{db_name}")
            return db_url
        else:
            # SQLite 기본값
            db_path = os.getenv("DB_PATH", "sqlite:///data/autoquant.db")
            logger.info(f"SQLite 연결: {db_path}")
            return db_path

    def create_tables(self):
        """테이블 생성"""
        Base.metadata.create_all(self.engine)
        logger.info("데이터베이스 테이블 생성 완료")

    def drop_tables(self):
        """테이블 삭제"""
        Base.metadata.drop_all(self.engine)
        logger.info("데이터베이스 테이블 삭제 완료")

    def get_session(self) -> Session:
        """세션 반환"""
        return self.SessionLocal()

    # ==================== Stock CRUD ====================

    def add_stock(self, ticker: str, name: str, market: str = None, sector: str = None) -> Stock:
        """종목 추가"""
        session = self.get_session()
        try:
            # 기존 종목 확인
            existing = session.query(Stock).filter(Stock.ticker == ticker).first()
            if existing:
                logger.info(f"종목이 이미 존재합니다: {ticker}")
                return existing

            stock = Stock(ticker=ticker, name=name, market=market, sector=sector)
            session.add(stock)
            session.commit()
            session.refresh(stock)
            logger.info(f"종목 추가: {ticker} - {name}")
            return stock
        except Exception as e:
            session.rollback()
            logger.error(f"종목 추가 실패: {e}")
            raise
        finally:
            session.close()

    def get_stock(self, ticker: str) -> Optional[Stock]:
        """종목 조회"""
        session = self.get_session()
        try:
            return session.query(Stock).filter(Stock.ticker == ticker).first()
        finally:
            session.close()

    def get_all_stocks(self) -> List[Stock]:
        """전체 종목 조회"""
        session = self.get_session()
        try:
            return session.query(Stock).all()
        finally:
            session.close()

    # ==================== StockPrice CRUD ====================

    def add_stock_prices(self, ticker: str, df: pd.DataFrame) -> int:
        """주가 데이터 추가 (DataFrame)"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                logger.error(f"종목을 찾을 수 없습니다: {ticker}")
                return 0

            count = 0
            for idx, row in df.iterrows():
                date = idx if isinstance(idx, datetime) else pd.to_datetime(idx)

                # 중복 체크
                existing = session.query(StockPrice).filter(
                    and_(StockPrice.stock_id == stock.id, StockPrice.date == date)
                ).first()

                if existing:
                    continue

                price = StockPrice(
                    stock_id=stock.id,
                    date=date,
                    open=float(row.get('Open', row.get('시가', 0))),
                    high=float(row.get('High', row.get('고가', 0))),
                    low=float(row.get('Low', row.get('저가', 0))),
                    close=float(row.get('Close', row.get('종가', 0))),
                    volume=int(row.get('Volume', row.get('거래량', 0))),
                    amount=float(row.get('Amount', row.get('거래대금', 0))) if 'Amount' in row or '거래대금' in row else None
                )
                session.add(price)
                count += 1

            session.commit()
            logger.info(f"{ticker} 주가 데이터 {count}건 추가")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"주가 데이터 추가 실패: {e}")
            raise
        finally:
            session.close()

    def get_stock_prices(self, ticker: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """주가 데이터 조회"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                logger.warning(f"종목을 찾을 수 없습니다: {ticker}")
                return pd.DataFrame()

            query = session.query(StockPrice).filter(StockPrice.stock_id == stock.id)

            if start_date:
                query = query.filter(StockPrice.date >= start_date)
            if end_date:
                query = query.filter(StockPrice.date <= end_date)

            prices = query.order_by(StockPrice.date).all()

            if not prices:
                return pd.DataFrame()

            data = [{
                'Date': p.date,
                'Open': p.open,
                'High': p.high,
                'Low': p.low,
                'Close': p.close,
                'Volume': p.volume,
                'Amount': p.amount
            } for p in prices]

            df = pd.DataFrame(data)
            df.set_index('Date', inplace=True)
            return df
        finally:
            session.close()

    # ==================== Prediction CRUD ====================

    def add_prediction(self, ticker: str, target_date: datetime, model_name: str,
                      predicted_price: float, confidence: float = None) -> Prediction:
        """예측 결과 추가"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                raise ValueError(f"종목을 찾을 수 없습니다: {ticker}")

            prediction = Prediction(
                stock_id=stock.id,
                prediction_date=datetime.now(),
                target_date=target_date,
                model_name=model_name,
                predicted_price=predicted_price,
                confidence=confidence
            )
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            logger.info(f"예측 추가: {ticker}, 모델: {model_name}, 가격: {predicted_price}")
            return prediction
        except Exception as e:
            session.rollback()
            logger.error(f"예측 추가 실패: {e}")
            raise
        finally:
            session.close()

    def get_predictions(self, ticker: str, model_name: str = None) -> List[Prediction]:
        """예측 결과 조회"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                return []

            query = session.query(Prediction).filter(Prediction.stock_id == stock.id)
            if model_name:
                query = query.filter(Prediction.model_name == model_name)

            return query.order_by(Prediction.prediction_date.desc()).all()
        finally:
            session.close()

    # ==================== Trade CRUD ====================

    def add_trade(self, ticker: str, trade_type: str, quantity: int, price: float,
                  strategy: str = None, signal_strength: float = None) -> Trade:
        """거래 추가"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                raise ValueError(f"종목을 찾을 수 없습니다: {ticker}")

            amount = quantity * price
            commission = amount * 0.00015  # 0.015% 수수료 가정

            trade = Trade(
                stock_id=stock.id,
                trade_date=datetime.now(),
                trade_type=trade_type.upper(),
                quantity=quantity,
                price=price,
                amount=amount,
                commission=commission,
                strategy=strategy,
                signal_strength=signal_strength
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            logger.info(f"거래 추가: {ticker} {trade_type} {quantity}주 @ {price}원")
            return trade
        except Exception as e:
            session.rollback()
            logger.error(f"거래 추가 실패: {e}")
            raise
        finally:
            session.close()

    def get_trades(self, ticker: str = None, start_date: datetime = None, end_date: datetime = None) -> List[Trade]:
        """거래 내역 조회"""
        session = self.get_session()
        try:
            query = session.query(Trade)

            if ticker:
                stock = session.query(Stock).filter(Stock.ticker == ticker).first()
                if stock:
                    query = query.filter(Trade.stock_id == stock.id)

            if start_date:
                query = query.filter(Trade.trade_date >= start_date)
            if end_date:
                query = query.filter(Trade.trade_date <= end_date)

            return query.order_by(Trade.trade_date.desc()).all()
        finally:
            session.close()

    # ==================== Portfolio CRUD ====================

    def update_portfolio(self, ticker: str, quantity: int, avg_buy_price: float) -> Portfolio:
        """포트폴리오 업데이트"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter(Stock.ticker == ticker).first()
            if not stock:
                raise ValueError(f"종목을 찾을 수 없습니다: {ticker}")

            portfolio = session.query(Portfolio).filter(Portfolio.stock_id == stock.id).first()

            if portfolio:
                portfolio.quantity = quantity
                portfolio.avg_buy_price = avg_buy_price
                portfolio.updated_at = datetime.now()
            else:
                portfolio = Portfolio(
                    stock_id=stock.id,
                    quantity=quantity,
                    avg_buy_price=avg_buy_price
                )
                session.add(portfolio)

            session.commit()
            session.refresh(portfolio)
            logger.info(f"포트폴리오 업데이트: {ticker}")
            return portfolio
        except Exception as e:
            session.rollback()
            logger.error(f"포트폴리오 업데이트 실패: {e}")
            raise
        finally:
            session.close()

    def get_portfolio(self) -> List[Portfolio]:
        """현재 포트폴리오 조회"""
        session = self.get_session()
        try:
            return session.query(Portfolio).filter(Portfolio.quantity > 0).all()
        finally:
            session.close()

    # ==================== BacktestResult CRUD ====================

    def add_backtest_result(self, strategy_name: str, start_date: datetime, end_date: datetime,
                           initial_capital: float, final_capital: float, metrics: Dict[str, Any]) -> BacktestResult:
        """백테스트 결과 추가"""
        session = self.get_session()
        try:
            result = BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=metrics.get('total_return'),
                annual_return=metrics.get('annual_return'),
                sharpe_ratio=metrics.get('sharpe_ratio'),
                max_drawdown=metrics.get('max_drawdown'),
                win_rate=metrics.get('win_rate'),
                total_trades=metrics.get('total_trades'),
                profitable_trades=metrics.get('profitable_trades'),
                parameters=str(metrics.get('parameters', {}))
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            logger.info(f"백테스트 결과 추가: {strategy_name}")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"백테스트 결과 추가 실패: {e}")
            raise
        finally:
            session.close()

    def get_backtest_results(self, strategy_name: str = None) -> List[BacktestResult]:
        """백테스트 결과 조회"""
        session = self.get_session()
        try:
            query = session.query(BacktestResult)
            if strategy_name:
                query = query.filter(BacktestResult.strategy_name == strategy_name)
            return query.order_by(BacktestResult.created_at.desc()).all()
        finally:
            session.close()

    # ==================== KIS Daily OHLCV Data ====================
    # PostgreSQL의 daily_ohlcv 테이블에서 직접 데이터 조회

    def get_daily_ohlcv_from_kis(self, symbol_code: str, start_date: datetime = None,
                                 end_date: datetime = None) -> pd.DataFrame:
        """
        KIS 시스템의 daily_ohlcv 테이블에서 일봉 데이터 조회

        Args:
            symbol_code: 종목코드 (예: '005930' - 삼성전자)
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            pandas.DataFrame: OHLCV 데이터
        """
        from sqlalchemy import text

        session = self.get_session()
        try:
            query = """
                SELECT
                    trade_date,
                    open_price as open,
                    high_price as high,
                    low_price as low,
                    close_price as close,
                    volume,
                    trade_amount as amount
                FROM daily_ohlcv
                WHERE symbol_code = :symbol_code
            """

            params = {'symbol_code': symbol_code}

            if start_date:
                query += " AND trade_date >= :start_date"
                params['start_date'] = start_date

            if end_date:
                query += " AND trade_date <= :end_date"
                params['end_date'] = end_date

            query += " ORDER BY trade_date ASC"

            result = session.execute(text(query), params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            if not df.empty:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
                logger.info(f"KIS daily_ohlcv 조회 성공: {symbol_code}, {len(df)}건")
            else:
                logger.warning(f"KIS daily_ohlcv 데이터 없음: {symbol_code}")

            return df

        except Exception as e:
            logger.error(f"KIS daily_ohlcv 조회 실패: {symbol_code} - {e}")
            return pd.DataFrame()
        finally:
            session.close()

    def get_available_symbols_from_kis(self) -> pd.DataFrame:
        """
        KIS 시스템에서 사용 가능한 종목 목록 조회

        Returns:
            pandas.DataFrame: 종목코드, 종목명, 시장구분
        """
        from sqlalchemy import text

        session = self.get_session()
        try:
            query = """
                SELECT DISTINCT
                    symbol_code,
                    MAX(trade_date) as last_trade_date,
                    COUNT(*) as data_count
                FROM daily_ohlcv
                GROUP BY symbol_code
                ORDER BY last_trade_date DESC
            """

            result = session.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=['symbol_code', 'last_trade_date', 'data_count'])

            logger.info(f"KIS 사용 가능 종목 조회: {len(df)}개")
            return df

        except Exception as e:
            logger.error(f"KIS 사용 가능 종목 조회 실패: {e}")
            return pd.DataFrame()
        finally:
            session.close()
