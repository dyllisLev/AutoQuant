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


class AnalysisRun(Base):
    """분석 실행 기록 (일일 분석 실행 추적)"""
    __tablename__ = 'analysis_runs'

    id = Column(Integer, primary_key=True)
    run_date = Column(Date, nullable=False, index=True)  # 분석 실행 날짜
    target_trade_date = Column(Date, nullable=False)  # 매매 대상 날짜
    status = Column(String(20), nullable=False, default='running', index=True)  # running, completed, failed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    total_duration_seconds = Column(Float)

    # Phase completion tracking
    phase1_completed = Column(Boolean, default=False)  # Data collection
    phase2_completed = Column(Boolean, default=False)  # Market analysis
    phase3_completed = Column(Boolean, default=False)  # AI screening
    phase4_completed = Column(Boolean, default=False)  # Technical screening
    phase5_completed = Column(Boolean, default=False)  # Price calculation

    # Error tracking
    error_message = Column(Text)
    error_phase = Column(String(50))  # Increased from 20 to accommodate longer phase names

    # Summary metrics
    total_stocks_analyzed = Column(Integer)
    ai_candidates_count = Column(Integer)
    technical_selections_count = Column(Integer)
    final_signals_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    market_snapshot = relationship("MarketSnapshot", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan")
    ai_screening = relationship("AIScreeningResult", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan")
    technical_screening = relationship("TechnicalScreeningResult", back_populates="analysis_run", uselist=False, cascade="all, delete-orphan")
    trading_signals = relationship("TradingSignal", back_populates="analysis_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisRun(date={self.run_date}, status='{self.status}', signals={self.final_signals_count})>"


class MarketSnapshot(Base):
    """시장 분석 결과 (Phase 2)"""
    __tablename__ = 'market_snapshots'

    id = Column(Integer, primary_key=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)

    # KOSPI/KOSDAQ
    kospi_close = Column(Float, nullable=False)
    kospi_change_pct = Column(Float, nullable=False)
    kospi_volume = Column(BigInteger)
    kospi_trend = Column(String(20))  # UPTREND, DOWNTREND, NEUTRAL

    kosdaq_close = Column(Float, nullable=False)
    kosdaq_change_pct = Column(Float, nullable=False)
    kosdaq_volume = Column(BigInteger)
    kosdaq_trend = Column(String(20))

    # Investor flows (KRW)
    foreign_net_buy = Column(BigInteger)
    foreign_buy_ratio = Column(Float)
    institution_net_buy = Column(BigInteger)
    institution_buy_ratio = Column(Float)
    retail_net_buy = Column(BigInteger)
    retail_buy_ratio = Column(Float)

    # Market breadth
    advancing_count = Column(Integer)
    declining_count = Column(Integer)
    unchanged_count = Column(Integer)
    new_highs_52w = Column(Integer)
    new_lows_52w = Column(Integer)

    # Momentum & Sentiment
    momentum_score = Column(Float)  # 0-100
    market_sentiment = Column(String(20))  # BULLISH, BEARISH, NEUTRAL

    # Sector performance (JSON)
    sector_performance = Column(JSON)  # [{sector, change_pct, volume_ratio}, ...]

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="market_snapshot")

    def __repr__(self):
        return f"<MarketSnapshot(date={self.snapshot_date}, kospi={self.kospi_close}, sentiment='{self.market_sentiment}')>"


class AIScreeningResult(Base):
    """AI 스크리닝 결과 (Phase 3)"""
    __tablename__ = 'ai_screening_results'

    id = Column(Integer, primary_key=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    screening_date = Column(Date, nullable=False)

    # AI provider info
    ai_provider = Column(String(50))  # openai, anthropic, google
    ai_model = Column(String(50))     # gpt-4, claude-3, gemini-pro

    # Execution metrics
    total_input_stocks = Column(Integer, nullable=False)
    selected_count = Column(Integer, nullable=False)
    execution_time_seconds = Column(Float)
    api_cost_usd = Column(Float)

    # Prompt & Response
    prompt_text = Column(Text)
    response_text = Column(Text)
    response_summary = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="ai_screening")
    candidates = relationship("AICandidate", back_populates="ai_screening", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AIScreeningResult(date={self.screening_date}, provider='{self.ai_provider}', selected={self.selected_count})>"


class AICandidate(Base):
    """AI 선정 종목 상세 (Phase 3)"""
    __tablename__ = 'ai_candidates'

    id = Column(Integer, primary_key=True)
    ai_screening_id = Column(Integer, ForeignKey('ai_screening_results.id', ondelete='CASCADE'), nullable=False, index=True)

    stock_code = Column(String(10), nullable=False, index=True)
    company_name = Column(String(100))

    # AI evaluation
    ai_score = Column(Float)  # 0-100
    ai_reasoning = Column(Text)
    rank_in_batch = Column(Integer)

    # Mentioned factors (JSON array)
    mentioned_factors = Column(JSON)  # ['sector_strength', 'foreign_buying', ...]

    # Stock data at screening time
    current_price = Column(Float)
    market_cap = Column(BigInteger)
    volume = Column(BigInteger)
    sector = Column(String(50))

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    ai_screening = relationship("AIScreeningResult", back_populates="candidates")

    def __repr__(self):
        return f"<AICandidate(code={self.stock_code}, score={self.ai_score}, rank={self.rank_in_batch})>"


class TechnicalScreeningResult(Base):
    """기술적 스크리닝 결과 (Phase 4)"""
    __tablename__ = 'technical_screening_results'

    id = Column(Integer, primary_key=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    screening_date = Column(Date, nullable=False)

    input_candidates_count = Column(Integer, nullable=False)
    final_selections_count = Column(Integer, nullable=False)
    execution_time_seconds = Column(Float)

    # Scoring thresholds used
    min_final_score = Column(Float)  # Minimum score to pass (e.g., 50)
    max_selections = Column(Integer)   # Maximum stocks to select (e.g., 5)

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="technical_screening")
    selections = relationship("TechnicalSelection", back_populates="tech_screening", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TechnicalScreeningResult(date={self.screening_date}, input={self.input_candidates_count}, selected={self.final_selections_count})>"


class TechnicalSelection(Base):
    """기술적 선정 종목 상세 (Phase 4)"""
    __tablename__ = 'technical_selections'

    id = Column(Integer, primary_key=True)
    tech_screening_id = Column(Integer, ForeignKey('technical_screening_results.id', ondelete='CASCADE'), nullable=False, index=True)

    stock_code = Column(String(10), nullable=False, index=True)
    company_name = Column(String(100))
    current_price = Column(Float, nullable=False)

    # Technical scores (5-factor system)
    sma_score = Column(Float)      # out of 20
    rsi_score = Column(Float)      # out of 15
    macd_score = Column(Float)     # out of 15
    bb_score = Column(Float)       # out of 10
    volume_score = Column(Float)   # out of 10
    final_score = Column(Float)    # out of 70

    # Technical indicators (JSON for all 16 indicators)
    indicators = Column(JSON)  # {SMA_5, SMA_20, RSI_14, MACD, ...}

    rank_in_batch = Column(Integer)
    selection_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    tech_screening = relationship("TechnicalScreeningResult", back_populates="selections")

    def __repr__(self):
        return f"<TechnicalSelection(code={self.stock_code}, score={self.final_score}, rank={self.rank_in_batch})>"


class TradingSignal(Base):
    """AI 기반 매매 신호 (Phase 5 - 최종 결과)"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    tech_selection_id = Column(Integer, ForeignKey('technical_selections.id'))  # Link to technical selection
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)

    stock_code = Column(String(10), nullable=False, index=True)
    company_name = Column(String(100))

    # Analysis & Trade dates
    analysis_date = Column(Date, nullable=False, index=True)  # 분석 날짜
    target_trade_date = Column(Date, nullable=False, index=True)  # 매매 예정 날짜

    # Prices
    current_price = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)  # 매수가
    target_price = Column(Float, nullable=False)  # 목표가
    stop_loss_price = Column(Float, nullable=False)  # 손절가

    # Performance metrics
    predicted_return = Column(Float, nullable=False)  # 예상 수익률
    risk_reward_ratio = Column(Float)  # Target profit / Stop loss
    ai_confidence = Column(Integer, nullable=False)  # AI 신뢰도 (0-100)

    # Support/Resistance levels
    support_level = Column(Float)
    resistance_level = Column(Float)
    pivot_point = Column(Float)
    r1_level = Column(Float)
    s1_level = Column(Float)
    high_60d = Column(Float)
    low_60d = Column(Float)

    # Volatility
    atr = Column(Float)
    atr_percent = Column(Float)
    volatility_rank = Column(String(20))  # LOW, MEDIUM, HIGH

    # Technical indicators (key ones)
    current_rsi = Column(Float)
    current_macd = Column(Float)
    current_bollinger_position = Column(String(20))

    # Market context
    market_trend = Column(String(20))  # 시장 추세
    investor_flow = Column(String(20))  # 투자자 매매동향
    sector_momentum = Column(String(20))  # 섹터 모멘텀

    # AI reasoning
    ai_reasoning = Column(Text)  # AI가 선택한 이유

    # Calculation details (JSON)
    calculation_details = Column(JSON)  # {buy_premium_pct, target_method, stop_method, ...}

    # Execution tracking
    status = Column(String(20), default='pending', index=True)  # pending, executed, cancelled, expired
    executed_price = Column(Float)  # 실제 체결가
    executed_date = Column(DateTime)  # 실제 체결 날짜

    # Performance tracking (filled after trade)
    actual_return = Column(Float)  # 실제 수익률
    exit_price = Column(Float)
    exit_time = Column(DateTime)
    exit_reason = Column(String(50))  # target_hit, stop_hit, manual, timeout

    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="trading_signals")
    stock = relationship("Stock", foreign_keys=[stock_id])

    def __repr__(self):
        return f"<TradingSignal(code={self.stock_code}, date={self.analysis_date}, buy={self.buy_price}, target={self.target_price})>"
