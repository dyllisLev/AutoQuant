"""
데이터베이스 관리 클래스
"""

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .models import Base, Stock, StockPrice, MarketData, Prediction, Trade, Portfolio, BacktestResult


class Database:
    """데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "sqlite:///data/autoquant.db", echo: bool = False):
        """
        Args:
            db_path: 데이터베이스 경로 (SQLite 기본)
            echo: SQL 로그 출력 여부
        """
        self.db_path = db_path

        # SQLite 메모리 DB의 경우 특별 처리
        if ":memory:" in db_path:
            self.engine = create_engine(
                db_path,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo
            )
        else:
            self.engine = create_engine(db_path, echo=echo)

        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"데이터베이스 초기화: {db_path}")

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
