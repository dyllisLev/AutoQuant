# AutoQuant - 자동 주식 트레이딩 시스템

한국 주식 시장을 위한 종합 자동 트레이딩 시스템입니다.

## 주요 기능

### 1. 데이터 수집 (Data Collection)
- **주가 데이터**: KOSPI, KOSDAQ, KONEX 시장의 일별 주가 데이터
- **재무 데이터**: PER, PBR, ROE, EPS 등 기본적 분석 지표
- **시장 데이터**: 시가총액, 거래량, 거래대금 등

### 2. 데이터 분석 및 예측 (Analysis & Prediction)
- 머신러닝/딥러닝 기반 주가 예측
- 향후 1주일 주가 예측
- 기술적 지표 분석 (SMA, EMA, RSI, MACD 등)

### 3. 매매 전략 (Trading Strategy)
- 종목 선정 알고리즘
- 매수/매도 시그널 생성
- 리스크 관리

### 4. 포트폴리오 관리 (Portfolio Management)
- 자산 배분 최적화
- 리밸런싱
- 손익 관리

### 5. 자동 실행 (Automation)
- 매일 자동 데이터 수집
- 자동 분석 및 매매 실행
- 스케줄러 기반 운영

## 프로젝트 구조

```
AutoQuant/
├── src/
│   ├── data_collection/      # 데이터 수집 모듈
│   │   ├── base_collector.py
│   │   ├── stock_collector.py
│   │   ├── market_collector.py
│   │   ├── financial_collector.py
│   │   └── data_manager.py
│   ├── database/              # 데이터베이스 모듈
│   ├── analysis/              # 데이터 분석 모듈
│   ├── strategy/              # 매매 전략 모듈
│   ├── execution/             # 매매 실행 모듈
│   ├── portfolio/             # 포트폴리오 관리 모듈
│   └── scheduler/             # 스케줄러 모듈
├── config/
│   └── settings.yaml          # 설정 파일
├── tests/                     # 테스트
├── logs/                      # 로그 파일
├── data/                      # 데이터 저장소
├── collect_data.py            # 데이터 수집 스크립트
├── requirements.txt           # 의존성 패키지
├── .env.example               # 환경 변수 예시
└── README.md
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd AutoQuant
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 입력
```

## 사용 방법

### 데이터 수집

#### 1. 일일 데이터 수집 (KOSPI 상위 100개 종목)

```bash
python collect_data.py --mode daily --market KOSPI --top-n 100
```

#### 2. 특정 종목 데이터 수집

```bash
python collect_data.py --mode daily --tickers 005930 035720 000660
```

#### 3. 히스토리 데이터 수집

```bash
python collect_data.py --mode history --tickers 005930 --days 365
```

#### 4. 시장 개요 조회

```bash
python collect_data.py --mode overview --market KOSPI
```

### 명령행 옵션

- `--mode`: 실행 모드 (`daily`, `history`, `overview`)
- `--market`: 시장 선택 (`KOSPI`, `KOSDAQ`, `KONEX`, `ALL`)
- `--top-n`: 수집할 상위 종목 수 (기본값: 100)
- `--tickers`: 특정 종목코드 리스트
- `--days`: 히스토리 수집 기간 (기본값: 365일)

## 주요 종목코드

```
삼성전자: 005930
SK하이닉스: 000660
NAVER: 035420
카카오: 035720
LG에너지솔루션: 373220
삼성바이오로직스: 207940
현대차: 005380
기아: 000270
```

## 데이터 수집 모듈 상세

### StockDataCollector
주가 데이터 (시가, 고가, 저가, 종가, 거래량) 수집

```python
from src.data_collection import StockDataCollector

collector = StockDataCollector()

# 단일 종목 수집
df = collector.collect(ticker='005930', days=365)

# 여러 종목 수집
data = collector.collect_multiple(
    tickers=['005930', '035720'],
    days=365
)

# 현재가 조회
price = collector.get_current_price('005930')
```

### MarketDataCollector
시장 전체 데이터 수집

```python
from src.data_collection import MarketDataCollector

collector = MarketDataCollector()

# 시장 데이터 수집
df = collector.collect(market='KOSPI')

# 종목 리스트 조회
tickers = collector.get_ticker_list(market='KOSPI')

# 상위 종목 조회
top_stocks = collector.get_top_stocks(
    market='KOSPI',
    criterion='market_cap',
    top_n=100
)
```

### FinancialDataCollector
재무제표 및 기본적 분석 지표 수집

```python
from src.data_collection import FinancialDataCollector

collector = FinancialDataCollector()

# 기본적 지표 조회
fundamental = collector.get_fundamental_data('005930')
print(f"PER: {fundamental['PER']}")
print(f"PBR: {fundamental['PBR']}")

# 재무비율 계산
ratios = collector.get_financial_ratios('005930')
```

### DataCollectionManager
통합 데이터 수집 매니저

```python
from src.data_collection import DataCollectionManager

manager = DataCollectionManager()

# 일일 데이터 수집
result = manager.collect_daily_data(
    market='KOSPI',
    top_n=100
)

# 종목 정보 조회
info = manager.get_ticker_info('005930')
```

## 설정

`config/settings.yaml` 파일에서 다양한 설정을 변경할 수 있습니다:

- 데이터 수집 설정
- 데이터베이스 설정
- 분석 및 예측 설정
- 매매 전략 설정
- 포트폴리오 관리 설정
- 로깅 설정
- 알림 설정

## 로그

로그 파일은 `logs/` 디렉토리에 저장됩니다:
- `data_collection_YYYYMMDD.log`: 데이터 수집 로그
- 로그는 30일간 보관됩니다

## 다음 단계

### 구현 예정 기능

1. **데이터베이스 모듈**: SQLAlchemy 기반 데이터 저장
2. **분석 모듈**: ML/AI 기반 주가 예측
3. **전략 모듈**: 매매 전략 구현
4. **실행 모듈**: 실제 매매 실행
5. **포트폴리오 관리**: 자산 관리 및 최적화
6. **스케줄러**: 자동 실행 스케줄링
7. **백테스팅**: 전략 성능 테스트
8. **웹 대시보드**: 실시간 모니터링

## 주의사항

⚠️ **중요**: 이 프로그램은 교육 및 연구 목적으로 제작되었습니다.
- 실제 투자에 사용 시 자기 책임하에 사용하세요
- 과거 데이터가 미래 수익을 보장하지 않습니다
- 투자 손실에 대한 책임은 사용자에게 있습니다

## 라이선스

MIT License

## 기여

이슈와 PR은 언제나 환영합니다!

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
