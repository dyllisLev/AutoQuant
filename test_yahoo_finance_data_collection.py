#!/usr/bin/env python3
"""
Yahoo Finance API를 사용한 실제 데이터 수집 테스트
"""

import requests
import json
from datetime import datetime, timedelta

def get_stock_data(ticker, period='1mo', interval='1d'):
    """
    Yahoo Finance API로 주가 데이터 가져오기

    Args:
        ticker: 종목 심볼 (예: '005930.KS', 'AAPL')
        period: 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: 간격 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

    Returns:
        dict: 주가 데이터
    """
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
    params = {
        'range': period,
        'interval': interval
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"오류: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

def parse_stock_data(data):
    """Yahoo Finance 응답 데이터 파싱"""
    try:
        chart = data['chart']['result'][0]

        # 메타 정보
        meta = chart['meta']
        symbol = meta['symbol']
        currency = meta['currency']
        timezone = meta['timezone']
        current_price = meta.get('regularMarketPrice', 'N/A')

        # 시계열 데이터
        timestamps = chart['timestamp']
        quote = chart['indicators']['quote'][0]

        opens = quote.get('open', [])
        highs = quote.get('high', [])
        lows = quote.get('low', [])
        closes = quote.get('close', [])
        volumes = quote.get('volume', [])

        return {
            'meta': {
                'symbol': symbol,
                'currency': currency,
                'timezone': timezone,
                'current_price': current_price
            },
            'data': {
                'timestamps': timestamps,
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            }
        }

    except Exception as e:
        print(f"데이터 파싱 오류: {str(e)}")
        return None

def print_stock_data(parsed_data):
    """주가 데이터 출력"""
    if not parsed_data:
        return

    meta = parsed_data['meta']
    data = parsed_data['data']

    print("\n" + "=" * 80)
    print(f"종목: {meta['symbol']}")
    print(f"통화: {meta['currency']}")
    print(f"시간대: {meta['timezone']}")
    print(f"현재가: {meta['current_price']}")
    print("=" * 80)

    # 최근 데이터 출력
    print("\n최근 거래 데이터 (최대 10건):")
    print("-" * 80)
    print(f"{'날짜':^20} {'시가':>10} {'고가':>10} {'저가':>10} {'종가':>10} {'거래량':>15}")
    print("-" * 80)

    num_records = min(10, len(data['timestamps']))

    for i in range(num_records):
        timestamp = data['timestamps'][i]
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

        open_price = data['open'][i] if i < len(data['open']) else 'N/A'
        high_price = data['high'][i] if i < len(data['high']) else 'N/A'
        low_price = data['low'][i] if i < len(data['low']) else 'N/A'
        close_price = data['close'][i] if i < len(data['close']) else 'N/A'
        volume = data['volume'][i] if i < len(data['volume']) else 'N/A'

        # None 값 처리
        open_price = f"{open_price:,.2f}" if isinstance(open_price, (int, float)) and open_price else "N/A"
        high_price = f"{high_price:,.2f}" if isinstance(high_price, (int, float)) and high_price else "N/A"
        low_price = f"{low_price:,.2f}" if isinstance(low_price, (int, float)) and low_price else "N/A"
        close_price = f"{close_price:,.2f}" if isinstance(close_price, (int, float)) and close_price else "N/A"
        volume = f"{volume:,}" if isinstance(volume, (int, float)) and volume else "N/A"

        print(f"{date_str:^20} {open_price:>10} {high_price:>10} {low_price:>10} {close_price:>10} {volume:>15}")

    print("-" * 80)
    print(f"총 {len(data['timestamps'])}건의 데이터 수집 완료")

# 메인 테스트
print("=" * 80)
print("Yahoo Finance API 데이터 수집 테스트")
print("=" * 80)
print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 테스트할 종목 목록
test_stocks = [
    {'ticker': '005930.KS', 'name': '삼성전자 (Korea)'},
    {'ticker': 'AAPL', 'name': 'Apple Inc.'},
    {'ticker': 'TSLA', 'name': 'Tesla Inc.'},
]

results = []

for stock in test_stocks:
    ticker = stock['ticker']
    name = stock['name']

    print("\n" + "=" * 80)
    print(f"종목: {name} ({ticker})")
    print("=" * 80)

    # 데이터 수집
    print(f"\n데이터 수집 중...")
    raw_data = get_stock_data(ticker, period='5d', interval='1d')

    if raw_data:
        print("✓ 데이터 수집 성공")

        # 데이터 파싱
        parsed = parse_stock_data(raw_data)

        if parsed:
            print("✓ 데이터 파싱 성공")
            print_stock_data(parsed)

            results.append({
                'ticker': ticker,
                'name': name,
                'status': '성공',
                'records': len(parsed['data']['timestamps'])
            })
        else:
            print("✗ 데이터 파싱 실패")
            results.append({
                'ticker': ticker,
                'name': name,
                'status': '파싱 실패',
                'records': 0
            })
    else:
        print("✗ 데이터 수집 실패")
        results.append({
            'ticker': ticker,
            'name': name,
            'status': '수집 실패',
            'records': 0
        })

# 최종 결과 요약
print("\n" + "=" * 80)
print("테스트 결과 요약")
print("=" * 80)

success_count = sum(1 for r in results if r['status'] == '성공')
total_count = len(results)
total_records = sum(r['records'] for r in results)

print(f"\n전체 종목: {total_count}개")
print(f"성공: {success_count}개")
print(f"실패: {total_count - success_count}개")
print(f"수집된 총 레코드: {total_records}건")
print(f"성공률: {(success_count/total_count*100):.1f}%")

print("\n" + "=" * 80)
print("결론")
print("=" * 80)

if success_count == total_count:
    print("\n✅ 외부 API를 통한 데이터 수집이 정상적으로 작동합니다!")
    print("   Yahoo Finance API를 사용하여 실시간 주가 데이터를 수집할 수 있습니다.")
    print("\n【사용 가능한 기능】")
    print("   ✓ 한국 주식 데이터 수집 (예: 005930.KS)")
    print("   ✓ 미국 주식 데이터 수집 (예: AAPL, TSLA)")
    print("   ✓ 과거 데이터 조회 (최대 수년치)")
    print("   ✓ 다양한 시간 간격 데이터 (1분, 1시간, 1일 등)")
elif success_count > 0:
    print("\n⚠️  일부 종목의 데이터 수집에 성공했습니다.")
    print("   일부 API는 정상 작동하지만 일부는 문제가 있을 수 있습니다.")
else:
    print("\n❌ 외부 API를 통한 데이터 수집에 실패했습니다.")
    print("   네트워크 연결이나 API 접근 권한을 확인해주세요.")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
