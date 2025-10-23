#!/usr/bin/env python3
"""
모의 데이터를 사용한 데모
실제 환경에서는 실제 데이터를 수집하지만,
테스트 환경에서는 모의 데이터로 기능을 시연합니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_collection.mock_data import MockDataGenerator

print("=" * 70)
print("AutoQuant 데이터 수집 시스템 데모 (모의 데이터)")
print("=" * 70)
print("\n⚠️  실제 환경에서는 pykrx/FinanceDataReader로 실제 데이터를 수집합니다")
print("   테스트 환경에서는 모의 데이터로 기능을 시연합니다\n")

# 모의 데이터 생성기
generator = MockDataGenerator()

# 날짜 설정
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

start_str = start_date.strftime('%Y%m%d')
end_str = end_date.strftime('%Y%m%d')

# 1. 주가 데이터 수집 데모
print("=" * 70)
print("1. 주가 데이터 수집 데모")
print("=" * 70)

print(f"\n📊 삼성전자(005930) 주가 데이터 (최근 30일)")
print(f"   기간: {start_str} ~ {end_str}")

df_samsung = generator.generate_stock_data('005930', start_str, end_str, initial_price=70000)

if not df_samsung.empty:
    print(f"\n   ✓ 수집 완료: {len(df_samsung)} 거래일")
    print("\n   최근 5일 데이터:")
    print(df_samsung.tail(5).to_string())

    # 통계 정보
    print(f"\n   📈 통계 정보:")
    print(f"   - 최고가: {df_samsung['High'].max():,.0f}원")
    print(f"   - 최저가: {df_samsung['Low'].min():,.0f}원")
    print(f"   - 평균 거래량: {df_samsung['Volume'].mean():,.0f}주")
    print(f"   - 종가 변화: {df_samsung['Close'].iloc[0]:,.0f}원 → {df_samsung['Close'].iloc[-1]:,.0f}원")

    change_rate = ((df_samsung['Close'].iloc[-1] / df_samsung['Close'].iloc[0]) - 1) * 100
    print(f"   - 수익률: {change_rate:+.2f}%")

# 2. 여러 종목 수집 데모
print("\n" + "=" * 70)
print("2. 여러 종목 데이터 수집 데모")
print("=" * 70)

tickers = ['005930', '000660', '035420', '035720', '051910']
ticker_names = {
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '035420': 'NAVER',
    '035720': '카카오',
    '051910': 'LG화학'
}

print(f"\n📊 {len(tickers)}개 종목 데이터 수집")

all_data = {}
for ticker in tickers:
    df = generator.generate_stock_data(ticker, start_str, end_str,
                                      initial_price=50000 + int(ticker) % 30000)
    all_data[ticker] = df

print(f"\n   ✓ 수집 완료: {len(all_data)}개 종목")
print("\n   종목별 최근 종가:")

for ticker, df in all_data.items():
    if not df.empty:
        name = ticker_names[ticker]
        latest_price = df['Close'].iloc[-1]
        volume = df['Volume'].iloc[-1]
        print(f"   - {name:10s} ({ticker}): {latest_price:>8,.0f}원  |  거래량: {volume:>10,}주")

# 3. 시장 데이터 데모
print("\n" + "=" * 70)
print("3. 시장 데이터 수집 데모")
print("=" * 70)

df_market = generator.generate_market_data('KOSPI')

print(f"\n📊 KOSPI 시장 데이터")
print(f"   ✓ 종목 수: {len(df_market)}")
print("\n   시가총액 상위 10개:")

for i, (ticker, row) in enumerate(df_market.head(10).iterrows(), 1):
    print(f"   {i:2d}. {row['Name']:10s} ({ticker}) | "
          f"시가총액: {row['MarketCap']/1e8:>8,.0f}억원 | "
          f"현재가: {row['Close']:>7,}원")

# 4. 재무 데이터 데모
print("\n" + "=" * 70)
print("4. 재무 지표 수집 데모")
print("=" * 70)

print(f"\n📊 주요 종목 재무 지표")

for ticker in tickers[:3]:
    name = ticker_names[ticker]
    fundamental = generator.generate_fundamental_data(ticker)

    print(f"\n   [{name} ({ticker})]")
    print(f"   - PER (주가수익비율):    {fundamental['PER']:>6.2f}")
    print(f"   - PBR (주가순자산비율):  {fundamental['PBR']:>6.2f}")
    print(f"   - ROE (자기자본이익률):  {fundamental['ROE']:>6.2f}%")
    print(f"   - EPS (주당순이익):      {fundamental['EPS']:>6,}원")
    print(f"   - BPS (주당순자산):      {fundamental['BPS']:>6,}원")
    print(f"   - DIV (배당수익률):      {fundamental['DIV']:>6.2f}%")

# 5. 데이터 분석 예제
print("\n" + "=" * 70)
print("5. 간단한 데이터 분석 예제")
print("=" * 70)

print(f"\n📊 삼성전자 기술적 분석")

# 이동평균 계산
df_samsung['SMA_5'] = df_samsung['Close'].rolling(window=5).mean()
df_samsung['SMA_20'] = df_samsung['Close'].rolling(window=20).mean()

latest = df_samsung.iloc[-1]
print(f"\n   현재가: {latest['Close']:,.0f}원")
print(f"   5일 이동평균: {latest['SMA_5']:,.0f}원")
print(f"   20일 이동평균: {latest['SMA_20']:,.0f}원")

if latest['Close'] > latest['SMA_5'] > latest['SMA_20']:
    signal = "🟢 강한 상승 추세"
elif latest['Close'] > latest['SMA_20']:
    signal = "🟡 상승 추세"
elif latest['Close'] < latest['SMA_20']:
    signal = "🔴 하락 추세"
else:
    signal = "⚪ 중립"

print(f"\n   추세 분석: {signal}")

# 거래량 분석
avg_volume = df_samsung['Volume'].mean()
latest_volume = latest['Volume']

print(f"\n   평균 거래량: {avg_volume:,.0f}주")
print(f"   최근 거래량: {latest_volume:,.0f}주")

if latest_volume > avg_volume * 1.5:
    volume_signal = "🔥 거래량 급증 (평균의 {:.1f}배)".format(latest_volume / avg_volume)
elif latest_volume > avg_volume:
    volume_signal = "📈 거래량 증가 (평균의 {:.1f}배)".format(latest_volume / avg_volume)
else:
    volume_signal = "📉 거래량 감소 (평균의 {:.1f}배)".format(latest_volume / avg_volume)

print(f"   거래량 분석: {volume_signal}")

# 6. 요약
print("\n" + "=" * 70)
print("데모 요약")
print("=" * 70)

print(f"""
✅ 구현 완료 기능:
   1. 주가 데이터 수집 (OHLCV)
   2. 여러 종목 동시 수집
   3. 시장 데이터 수집 (시가총액, 거래량)
   4. 재무 지표 수집 (PER, PBR, ROE, EPS 등)
   5. 기술적 분석 (이동평균, 거래량 분석)

📌 실제 환경 사용법:
   # KOSPI 상위 100개 종목 데이터 수집
   python collect_data.py --mode daily --market KOSPI --top-n 100

   # 특정 종목 수집
   python collect_data.py --mode daily --tickers 005930 000660

   # 시장 개요
   python collect_data.py --mode overview --market KOSPI

💡 다음 단계:
   - 데이터베이스에 저장
   - 머신러닝 모델로 주가 예측
   - 매매 전략 개발
   - 자동 매매 실행
""")

print("=" * 70)
print("데모 완료!")
print("=" * 70)
