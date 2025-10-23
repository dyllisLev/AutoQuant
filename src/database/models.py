"""
데이터베이스 모델 정의
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date, JSON, BigInteger
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


class TradingSignal(Base):
    """AI 기반 매매 신호 (일일 분석 결과)"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    analysis_date = Column(Date, nullable=False, index=True)  # 분석 날짜
    target_trade_date = Column(Date, nullable=False, index=True)  # 매매 예정 날짜
    buy_price = Column(Float, nullable=False)  # 매수가
    target_price = Column(Float, nullable=False)  # 목표가
    stop_loss_price = Column(Float, nullable=False)  # 손절가
    ai_confidence = Column(Integer, nullable=False)  # AI 신뢰도 (0-100)
    predicted_return = Column(Float, nullable=False)  # 예상 수익률
    current_rsi = Column(Float)  # 현재 RSI
    current_macd = Column(Float)  # 현재 MACD
    current_bollinger_position = Column(String(20))  # Bollinger 위치 (upper/middle/lower)
    market_trend = Column(String(20))  # 시장 추세 (uptrend/downtrend/range)
    investor_flow = Column(String(20))  # 투자자 매매동향 (positive/negative/neutral)
    sector_momentum = Column(String(20))  # 섹터 모멘텀 (strong/moderate/weak)
    ai_reasoning = Column(Text)  # AI가 선택한 이유
    status = Column(String(20), default='pending', index=True)  # pending/executed/missed/cancelled
    executed_price = Column(Float)  # 실제 체결가
    executed_date = Column(DateTime)  # 실제 체결 날짜
    actual_return = Column(Float)  # 실제 수익률
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    stock = relationship("Stock", foreign_keys=[stock_id])

    def __repr__(self):
        return f"<TradingSignal(stock_id={self.stock_id}, date={self.analysis_date}, confidence={self.ai_confidence}%)>"


class MarketSnapshot(Base):
    """시장 현황 스냅샷 (일일 시장 분석)"""
    __tablename__ = 'market_snapshots'

    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)  # 스냅샷 날짜
    kospi_close = Column(Float)  # KOSPI 종가
    kospi_change = Column(Float)  # KOSPI 일일 변화율 (%)
    kosdaq_close = Column(Float)  # KOSDAQ 종가
    kosdaq_change = Column(Float)  # KOSDAQ 일일 변화율 (%)
    advance_decline_ratio = Column(Float)  # 상승/하락 종목 비율
    foreign_flow = Column(BigInteger)  # 외국인 순매수 (KRW)
    institution_flow = Column(BigInteger)  # 기관 순매수 (KRW)
    retail_flow = Column(BigInteger)  # 개인 순매수 (KRW)
    sector_performance = Column(JSON)  # 섹터별 수익률 {'IT': 1.2, 'Finance': -0.5, ...}
    top_sectors = Column(JSON)  # 상위 섹터 ['IT', 'Semiconductors', ...]
    market_sentiment = Column(String(20))  # 시장 심리 (bullish/bearish/neutral)
    momentum_score = Column(Integer)  # 모멘텀 점수 (0-100)
    volatility_index = Column(Float)  # 변동성 지수
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MarketSnapshot(date={self.snapshot_date}, kospi={self.kospi_close}, sentiment={self.market_sentiment})>"
