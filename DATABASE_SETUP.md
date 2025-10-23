# AutoQuant PostgreSQL 데이터베이스 설정 가이드

## 개요

AutoQuant는 KIS 주식 데이터 수집 시스템의 PostgreSQL 데이터베이스와 직접 연동하여 일봉 데이터를 조회합니다.

- **데이터베이스**: PostgreSQL (KIS 시스템 공유)
- **호스트**: ***REDACTED_HOST***
- **데이터베이스**: postgres
- **수집 데이터**: daily_ohlcv 테이블 (4,359개 종목)

## 환경 설정

### 1. .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하세요:

```bash
# 데이터베이스 설정
DB_TYPE=postgresql
DB_HOST=***REDACTED_HOST***
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=***REDACTED***

# 로그 레벨
LOG_LEVEL=INFO
```

### 2. 패키지 설치

필요한 PostgreSQL 드라이버를 설치합니다:

```bash
pip install psycopg2-binary
```

## 데이터베이스 구조

### KIS System Tables (조회 전용)

AutoQuant에서 사용하는 KIS 시스템의 테이블:

#### daily_ohlcv (일봉 데이터)
```sql
CREATE TABLE daily_ohlcv (
    symbol_code VARCHAR(10) NOT NULL,
    market_type VARCHAR(10),
    trade_date DATE NOT NULL,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    close_price DECIMAL(10,2),
    volume BIGINT,
    trade_amount BIGINT,
    ...
    PRIMARY KEY (symbol_code, trade_date)
);
```

- **symbol_code**: 종목코드 (예: '005930' - 삼성전자)
- **trade_date**: 거래일
- **OHLCV**: 시가, 고가, 저가, 종가, 거래량

### AutoQuant Tables (생성 자동)

데이터베이스 초기화 시 자동으로 생성되는 테이블:

#### Stock (종목 정보)
```sql
CREATE TABLE stock (
    id BIGINT PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE,
    name VARCHAR(255),
    market VARCHAR(50),
    sector VARCHAR(50),
    created_at TIMESTAMP
);
```

#### StockPrice (주가 데이터)
```sql
CREATE TABLE stock_price (
    id BIGINT PRIMARY KEY,
    stock_id BIGINT REFERENCES stock(id),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    amount DECIMAL(15,2)
);
```

#### Prediction (예측 결과)
```sql
CREATE TABLE prediction (
    id BIGINT PRIMARY KEY,
    stock_id BIGINT REFERENCES stock(id),
    prediction_date TIMESTAMP,
    target_date DATE,
    model_name VARCHAR(100),
    predicted_price DECIMAL(10,2),
    confidence DECIMAL(5,2)
);
```

#### Trade (거래 내역)
```sql
CREATE TABLE trade (
    id BIGINT PRIMARY KEY,
    stock_id BIGINT REFERENCES stock(id),
    trade_date TIMESTAMP,
    trade_type VARCHAR(10),
    quantity INTEGER,
    price DECIMAL(10,2),
    amount DECIMAL(15,2),
    commission DECIMAL(15,2),
    strategy VARCHAR(100),
    signal_strength DECIMAL(5,2)
);
```

#### Portfolio (포트폴리오)
```sql
CREATE TABLE portfolio (
    id BIGINT PRIMARY KEY,
    stock_id BIGINT REFERENCES stock(id),
    quantity INTEGER,
    avg_buy_price DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### BacktestResult (백테스트 결과)
```sql
CREATE TABLE backtest_result (
    id BIGINT PRIMARY KEY,
    strategy_name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(15,2),
    final_capital DECIMAL(15,2),
    total_return DECIMAL(10,4),
    annual_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(5,2),
    total_trades INTEGER,
    profitable_trades INTEGER,
    parameters TEXT,
    created_at TIMESTAMP
);
```

## 사용 방법

### 1. 데이터베이스 초기화

```python
from src.database.database import Database

# 데이터베이스 초기화 (.env에서 설정 자동 로드)
db = Database()

# 테이블 생성
db.create_tables()
```

### 2. KIS 데이터 조회

```python
from datetime import datetime, timedelta

# 사용 가능한 종목 조회
symbols = db.get_available_symbols_from_kis()
print(f"사용 가능 종목: {len(symbols)}개")

# 특정 종목의 일봉 데이터 조회
symbol_code = "005930"  # 삼성전자
start_date = datetime.now() - timedelta(days=100)
end_date = datetime.now()

ohlcv = db.get_daily_ohlcv_from_kis(symbol_code, start_date, end_date)
print(ohlcv.head())
```

### 3. AutoQuant 테이블 사용

```python
# 종목 추가
stock = db.add_stock("005930", "삼성전자", "KOSPI", "전자")

# 주가 데이터 추가
db.add_stock_prices("005930", ohlcv)

# 예측 결과 추가
db.add_prediction("005930", datetime.now() + timedelta(days=7), "LSTM", 70000, 0.85)

# 거래 추가
db.add_trade("005930", "BUY", 10, 70000, "SMA_CROSSOVER", 0.8)

# 백테스트 결과 추가
db.add_backtest_result(
    "SMA_CROSSOVER",
    datetime(2024, 1, 1),
    datetime(2024, 10, 23),
    1000000,
    1250000,
    {"total_return": 25.0, "annual_return": 25.0, "sharpe_ratio": 1.5}
)
```

## 테스트

제공되는 테스트 스크립트로 연결을 확인하세요:

```bash
source venv/bin/activate
python test_db_connection.py
```

이 스크립트는:
- ✅ PostgreSQL 연결 확인
- ✅ AutoQuant 테이블 생성 확인
- ✅ KIS 데이터 조회 확인
- ✅ 기본 CRUD 동작 확인

## 주의사항

### 1. 보안
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 `.env`가 포함되어 있는지 확인하세요

### 2. 데이터 신선도
- KIS 시스템은 매일 장 마감 후 (15:30 이후) 데이터를 수집합니다
- daily_ohlcv 테이블의 최신 업데이트 날짜를 확인하세요

### 3. 성능
- 대량의 데이터 조회 시 날짜 범위를 지정하여 조회하세요
- 예: `get_daily_ohlcv_from_kis(symbol, start_date, end_date)`

## 트러블슈팅

### 연결 실패
```
Error: could not translate host name "***REDACTED_HOST***" to address
```
- 네트워크 설정 확인
- ***REDACTED_HOST*** 호스트 연결 확인
- 방화벽 설정 확인

### 인증 실패
```
Error: password authentication failed for user "postgres"
```
- `.env` 파일의 DB_PASSWORD 확인
- PostgreSQL 사용자 권한 확인

### daily_ohlcv 테이블 없음
```
Error: relation "daily_ohlcv" does not exist
```
- KIS 데이터 수집 시스템이 실행되었는지 확인
- `python /workspace/kis/collect/main_collect.py`로 데이터 수집

## 참고 자료

- [KIS 데이터 수집 시스템](/workspace/kis/README_TRADING_SYSTEM.md)
- [SQLAlchemy ORM 문서](https://docs.sqlalchemy.org/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
