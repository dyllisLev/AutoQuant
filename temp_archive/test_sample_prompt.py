import os
import sys
from dotenv import load_dotenv
from src.database.database import Database
from src.screening.market_analyzer import MarketAnalyzer
from sqlalchemy import text
import pandas as pd

load_dotenv()

print("=" * 100)
print("🤖 AI에게 요청하는 프롬프트 샘플 (2개 주식)")
print("=" * 100)

# KIS DB에서 실제 데이터 조회
db = Database()
session = db.get_session()

query = """
    SELECT
        symbol_code,
        trade_date,
        close_price as close,
        high_price as high,
        low_price as low,
        open_price as open,
        volume,
        trade_amount as amount
    FROM daily_ohlcv
    WHERE trade_date = (SELECT MAX(trade_date) FROM daily_ohlcv)
    ORDER BY volume DESC
    LIMIT 2
"""

result = session.execute(text(query))
columns = result.keys()
rows = result.fetchall()
session.close()

stocks_df = pd.DataFrame(rows, columns=columns)

print(f"\n✅ KIS DB에서 상위 2개 주식 조회:")
print(f"   거래 일자: {stocks_df['trade_date'].iloc[0]}")
print(f"   주식 1: {stocks_df.iloc[0]['symbol_code']} (거래량: {stocks_df.iloc[0]['volume']:,})")
print(f"   주식 2: {stocks_df.iloc[1]['symbol_code']} (거래량: {stocks_df.iloc[1]['volume']:,})")

# 시장 분석 결과 생성
analyzer = MarketAnalyzer()
market_snapshot = analyzer.analyze_market('2025-10-23')

print(f"\n📊 시장 분석 결과:")
print(f"   KOSPI: {market_snapshot['kospi_close']:.2f}")
print(f"   시장 추세: {market_snapshot.get('market_trend', 'UNKNOWN')}")
print(f"   심리: {market_snapshot.get('market_sentiment', 'UNKNOWN')}")

# 프롬프트 생성 (실제 AIScreener 방식)
print("\n" + "=" * 100)
print("📝 AI에게 전송되는 프롬프트 (정확한 형식)")
print("=" * 100)

# 주식 데이터 포맷팅
header = "Code|Name|Price|Change%|Market Cap|RSI|Volume|Vol%\n"
lines = []

for _, row in stocks_df.iterrows():
    code = str(row['symbol_code'])
    name = f"Stock_{code}"
    close = row['close']
    change = -0.5  # Mock
    market_cap = 1000000000  # Mock
    rsi = 50  # Mock
    volume = row['volume']
    vol_change = 0  # Mock
    
    line = f"{code}|{name}|{close:,.0f}|{change:+.1f}|{market_cap:,.0f}|{rsi:.0f}|{volume:,.0f}|{vol_change:+.0f}"
    lines.append(line)

formatted_stocks = header + "\n".join(lines)

# 완전한 프롬프트
full_prompt = f"""당신은 한국 주식 시장 분석 전문가입니다.

## 현재 시장 상황
- KOSPI: {market_snapshot['kospi_close']:.2f}
- 시장 추세: {market_snapshot.get('market_trend', 'UNKNOWN')}
- 시장 심리: {market_snapshot.get('market_sentiment', 'UNKNOWN')}
- 모멘텀 점수: {market_snapshot.get('momentum_score', 0)}/100

## 분석 대상 주식 (상위 거래량)
{formatted_stocks}

## 분석 요청
위 주식 중에서 내일 상승 가능성이 높은 종목 3~5개를 선택하세요.

각 종목에 대해:
- 선택 이유
- 신뢰도 (0~100%)
- 목표가
- 위험도

JSON 형식으로 반환하세요:
{{"candidates": [
  {{"code": "000020", "name": "Stock_000020", "confidence": 75, "reason": "...", "target_price": 6500, "risk": "medium"}},
  {{"code": "000040", "name": "Stock_000040", "confidence": 65, "reason": "...", "target_price": 520, "risk": "high"}}
]}}
"""

print("\n📨 PROMPT CONTENT:")
print("-" * 100)
print(full_prompt)
print("-" * 100)

print("\n📊 프롬프트 통계:")
lines_count = full_prompt.count('\n')
words_count = len(full_prompt.split())
print(f"   라인 수: {lines_count}")
print(f"   단어 수: {words_count}")
print(f"   문자 수: {len(full_prompt)}")

# 토큰 추정
try:
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(full_prompt)
    print(f"   추정 토큰: {len(tokens)}")
except:
    print(f"   토큰 계산: 불가능")

print("\n" + "=" * 100)
print("✅ 샘플 완료")
print("=" * 100)

