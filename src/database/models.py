"""
데이터베이스 모델 정의
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """종목 정보"""
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    market = Column(String(20))  # KOSPI, KOSDAQ, KONEX
    sector = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    market_data = relationship("MarketData", back_populates="stock", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="stock", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', name='{self.name}')>"


class StockPrice(Base):
    """주가 데이터"""
    __tablename__ = 'stock_prices'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="prices")

    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"


class MarketData(Base):
    """시장 데이터 (시가총액, 재무지표 등)"""
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    market_cap = Column(Float)  # 시가총액
    per = Column(Float)  # 주가수익비율
    pbr = Column(Float)  # 주가순자산비율
    roe = Column(Float)  # 자기자본이익률
    eps = Column(Float)  # 주당순이익
    bps = Column(Float)  # 주당순자산
    div_yield = Column(Float)  # 배당수익률
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="market_data")

    def __repr__(self):
        return f"<MarketData(stock_id={self.stock_id}, date='{self.date}')>"


class Prediction(Base):
    """주가 예측 결과"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    prediction_date = Column(DateTime, nullable=False, index=True)  # 예측한 날짜
    target_date = Column(DateTime, nullable=False, index=True)  # 예측 목표 날짜
    model_name = Column(String(50), nullable=False)  # LSTM, XGBoost 등
    predicted_price = Column(Float, nullable=False)
    confidence = Column(Float)  # 신뢰도
    actual_price = Column(Float)  # 실제 가격 (나중에 업데이트)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(stock_id={self.stock_id}, model='{self.model_name}', price={self.predicted_price})>"


class Trade(Base):
    """거래 내역"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # 거래금액
    commission = Column(Float, default=0)  # 수수료
    strategy = Column(String(50))  # 전략명
    signal_strength = Column(Float)  # 시그널 강도
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="trades")

    def __repr__(self):
        return f"<Trade(stock_id={self.stock_id}, type='{self.trade_type}', price={self.price})>"


class Portfolio(Base):
    """포트폴리오 (현재 보유 종목)"""
    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, unique=True, index=True)
    quantity = Column(Integer, nullable=False)
    avg_buy_price = Column(Float, nullable=False)  # 평균 매수가
    current_price = Column(Float)  # 현재가
    profit_loss = Column(Float)  # 손익
    profit_loss_rate = Column(Float)  # 손익률
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Portfolio(stock_id={self.stock_id}, quantity={self.quantity}, avg_price={self.avg_buy_price})>"


class BacktestResult(Base):
    """백테스팅 결과"""
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float)  # 총 수익률
    annual_return = Column(Float)  # 연간 수익률
    sharpe_ratio = Column(Float)  # 샤프 비율
    max_drawdown = Column(Float)  # 최대 낙폭
    win_rate = Column(Float)  # 승률
    total_trades = Column(Integer)  # 총 거래 횟수
    profitable_trades = Column(Integer)  # 수익 거래 수
    parameters = Column(Text)  # JSON 형태의 전략 파라미터
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<BacktestResult(strategy='{self.strategy_name}', return={self.total_return}%)>"
