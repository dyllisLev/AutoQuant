#!/usr/bin/env python3
"""
AI 스크리닝 요청 프롬프트 샘플 보기 (실제 요청 없음)
"""
import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
from src.database.database import Database
from src.screening.market_analyzer import MarketAnalyzer
from sqlalchemy import text
import pandas as pd

load_dotenv()

print("=" * 120)
print("🤖 AI에게 전송되는 프롬프트 샘플 (2개 실제 주식 - 요청 없이 프롬프트만 표시)")
print("=" * 120)

# ============================================================================
# Step 1: KIS DB에서 실제 상위 2개 주식 데이터 + 회사 정보 조회
# ============================================================================
print("\n📋 Step 1: KIS DB에서 상위 2개 주식 + 회사 정보 조회...")

db = Database()
session = db.get_session()

# JOIN with stock info to get company names and financial data
# Filter for real companies with substantial financial data (exclude ETFs and funds)
query = """
    SELECT
        d.symbol_code,
        d.trade_date,
        d.close_price as close,
        d.high_price as high,
        d.low_price as low,
        d.open_price as open,
        d.volume,
        d.trade_amount as amount,
        k.korean_name as company_name,
        k.index_sector_large_code as sector_code,
        k.market_cap,
        k.revenue,
        k.operating_profit,
        k.net_profit,
        k.roe
    FROM daily_ohlcv d
    LEFT JOIN kospi_stock_info k ON d.symbol_code = k.short_code
    WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily_ohlcv)
    AND k.korean_name IS NOT NULL
    AND k.market_cap > 100000
    AND k.revenue > 100000
    AND NOT k.korean_name LIKE '%KODEX%'
    AND NOT k.korean_name LIKE '%인버스%'
    AND NOT k.korean_name LIKE '%레버리지%'
    AND NOT k.korean_name LIKE '%ETF%'
    AND NOT k.korean_name LIKE '%ETN%'
    ORDER BY k.market_cap DESC, d.volume DESC
    LIMIT 2
"""

result = session.execute(text(query))
columns = result.keys()
rows = result.fetchall()
session.close()

stocks_df = pd.DataFrame(rows, columns=columns)

if stocks_df.empty:
    print("❌ KIS DB에서 데이터를 조회하지 못했습니다")
    sys.exit(1)

print(f"✅ 상위 2개 주식 + 회사 정보 조회 완료:")
for i, (_, row) in enumerate(stocks_df.iterrows(), 1):
    company = row['company_name'] if pd.notna(row['company_name']) else f"Stock_{row['symbol_code']}"
    market_cap_str = f"{row['market_cap']/100000000:,.0f}억" if pd.notna(row['market_cap']) else "N/A"
    revenue_str = f"{row['revenue']/100000000:,.0f}억" if pd.notna(row['revenue']) else "N/A"
    print(f"   {i}. 코드: {row['symbol_code']}, 회사: {company}, 가격: {row['close']:,.0f}원, 시가총액: {market_cap_str}")

# ============================================================================
# Step 2: 시장 분석 (datetime 객체 사용)
# ============================================================================
print("\n📊 Step 2: 시장 분석 (2025-10-23)...")

analyzer = MarketAnalyzer()
target_date = datetime(2025, 10, 23).date()  # ← datetime 객체 올바르게 전달

try:
    market_snapshot = analyzer.analyze_market(target_date)
    print(f"✅ 시장 분석 완료:")
    print(f"   KOSPI: {market_snapshot['kospi_close']:.2f}")
    print(f"   시장 추세: {market_snapshot.get('market_sentiment', 'UNKNOWN')}")
    print(f"   모멘텀: {market_snapshot.get('momentum_score', 0)}/100")
except Exception as e:
    print(f"❌ 시장 분석 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# Step 3: AI 요청 프롬프트 생성 (실제 요청 없음)
# ============================================================================
print("\n📝 Step 3: AI 요청 프롬프트 생성...")

# 주식 데이터 포맷팅 (파이프 구분) - 회사 정보 포함
header = "Code|Company Name|Price|Sector|Market Cap|Revenue|Operating Profit|Volume\n"
lines = []

# Sector mapping (index_sector_large_code -> name)
sector_map = {
    1: "Agriculture, Forestry & Fishing", 2: "Mining", 3: "Manufacturing",
    4: "Electricity, Gas & Water", 5: "Construction", 6: "Wholesale & Retail",
    7: "Transportation & Storage", 8: "Accommodation & Food", 9: "Information & Communication",
    10: "Financial & Insurance", 11: "Real Estate & Lease", 12: "Professional & Technical",
    13: "Business & Management", 14: "Public Administration & Defense", 15: "Education",
    16: "Human Health & Social Work", 17: "Arts, Sports & Entertainment", 18: "Other Services"
}

for _, row in stocks_df.iterrows():
    code = str(row['symbol_code']).strip()
    company_name = row['company_name'] if pd.notna(row['company_name']) else f"Stock_{code}"
    close = float(row['close'])

    # Get sector name (default to sector code if not found)
    sector_code = int(row['sector_code']) if pd.notna(row['sector_code']) else None
    sector_name = sector_map.get(sector_code, f"Sector_{sector_code}") if sector_code else "N/A"

    # Financial data (already in 100 million KRW units from DB)
    # market_cap, revenue, operating_profit are already in units of 100 million won
    market_cap = f"{int(row['market_cap']):,}억" if pd.notna(row['market_cap']) and row['market_cap'] > 0 else "N/A"
    revenue = f"{int(row['revenue']):,}억" if pd.notna(row['revenue']) and row['revenue'] > 0 else "N/A"
    operating_profit = f"{int(row['operating_profit']):,}억" if pd.notna(row['operating_profit']) and row['operating_profit'] > 0 else "N/A"
    volume = f"{float(row['volume'])/1000000:,.1f}M" if pd.notna(row['volume']) else "N/A"

    line = f"{code}|{company_name}|{close:,.0f}|{sector_name}|{market_cap}|{revenue}|{operating_profit}|{volume}"
    lines.append(line)

formatted_stocks = header + "\n".join(lines)

# 완전한 프롬프트 생성
full_prompt = f"""당신은 한국 주식시장 전문가입니다.

## 현재 시장 상황
- KOSPI 지수: {market_snapshot['kospi_close']:.2f}
- 시장 추세: {market_snapshot.get('market_sentiment', 'UNKNOWN')}
- 모멘텀 점수: {market_snapshot.get('momentum_score', 0)}/100
- 변동성 지수: {market_snapshot.get('volatility_index', 0):.2f}

## 분석할 주식 (거래량 상위)
아래는 거래량이 많은 상위 종목들의 실제 정보입니다. 각 회사명, 섹터, 시가총액, 매출액, 영업이익 등의 기초 데이터를 포함합니다:

{formatted_stocks}

## 분석 요청
현재 시장 상황을 고려하여 내일 상승할 가능성이 높은 종목들을 선별해주세요.

각 종목에 대해 다음을 제공하세요:
- 종목 코드 및 회사명
- 선별 이유 (시장 상황 + 기업 펀더멘탈 + 기술적 분석 종합)
- 신뢰도 점수 (0-100%)
- 내일의 목표가
- 위험 수준 (낮음/중간/높음)
- 상세한 분석 근거

아래 JSON 형식으로 응답해주세요:
{{
  "candidates": [
    {{
      "code": "252670",
      "name": "삼성전자",
      "sector": "Information & Communication",
      "confidence": 72,
      "reason": "높은 거래량 + 시장 모멘텀 일치 + 반도체 섹터 강세",
      "target_price": 70000,
      "risk": "medium",
      "analysis": "..."
    }}
  ],
  "total_count": 1
}}

JSON만 반환하세요.
"""

# ============================================================================
# Step 4: 프롬프트 출력 및 통계
# ============================================================================
print("\n" + "=" * 120)
print("📨 AI에게 전송되는 프롬프트 (요청 없이 표시만 함)")
print("=" * 120)
print(full_prompt)
print("=" * 120)

# 토큰 계산
try:
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(full_prompt)
    token_count = len(tokens)
except:
    token_count = 0

print("\n📊 프롬프트 통계:")
print(f"   라인 수: {full_prompt.count(chr(10))}")
print(f"   단어 수: {len(full_prompt.split())}")
print(f"   문자 수: {len(full_prompt)}")
print(f"   토큰 수: {token_count} tokens (gpt-5-mini context window: 400,000)")
print(f"   사용률: {(token_count/400000)*100:.2f}%")

print("\n" + "=" * 120)
print("✅ 프롬프트 샘플 표시 완료 (실제 AI 요청은 하지 않음)")
print("=" * 120)
