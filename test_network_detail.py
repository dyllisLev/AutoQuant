#!/usr/bin/env python3
"""
네트워크 연결 상세 테스트
"""

import requests
import socket
from datetime import datetime, timedelta

print("=" * 80)
print("네트워크 연결 상세 테스트")
print("=" * 80)
print()

# 1. 기본 인터넷 연결 테스트
print("1. 기본 인터넷 연결 테스트")
print("-" * 80)

test_urls = [
    "https://www.google.com",
    "https://www.naver.com",
    "https://httpbin.org/get",
]

for url in test_urls:
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ {url}: 상태코드 {response.status_code}")
    except Exception as e:
        print(f"✗ {url}: {type(e).__name__} - {str(e)[:60]}")

print()

# 2. 한국 금융 API 직접 테스트
print("2. 한국 금융 데이터 API 연결 테스트")
print("-" * 80)

# KRX API 엔드포인트
krx_endpoints = [
    "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd",
    "https://file.krx.co.kr/",
]

for endpoint in krx_endpoints:
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"✓ {endpoint}: 상태코드 {response.status_code}")
    except Exception as e:
        print(f"✗ {endpoint}: {type(e).__name__}")
        print(f"   세부사항: {str(e)[:80]}")

print()

# 3. DNS 해석 테스트
print("3. DNS 해석 상세 테스트")
print("-" * 80)

domains = [
    "data.krx.co.kr",
    "www.google.com",
    "finance.naver.com",
]

for domain in domains:
    try:
        ip = socket.gethostbyname(domain)
        print(f"✓ {domain} → {ip}")
    except socket.gaierror as e:
        print(f"✗ {domain}: DNS 조회 실패 - {e}")

print()

# 4. pykrx가 사용하는 실제 엔드포인트 테스트
print("4. pykrx 실제 API 엔드포인트 테스트")
print("-" * 80)

try:
    # pykrx가 사용하는 KRX 데이터 엔드포인트
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"

    # KOSPI 시장 데이터 요청 (pykrx가 사용하는 방식)
    data = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
        'locale': 'ko_KR',
        'mktId': 'STK',
        'share': '1',
        'csvxls_isNo': 'false',
    }

    print(f"  URL: {url}")
    print(f"  요청 시도 중...")

    response = requests.post(url, data=data, timeout=10)
    print(f"  ✓ 상태코드: {response.status_code}")
    print(f"  ✓ 응답 크기: {len(response.content)} bytes")

    if response.status_code == 200:
        import json
        try:
            json_data = response.json()
            print(f"  ✓ JSON 파싱 성공")
            if 'OutBlock_1' in json_data:
                print(f"  ✓ 데이터 수신 성공: {len(json_data['OutBlock_1'])} 건")
            else:
                print(f"  응답 키: {list(json_data.keys())[:5]}")
        except:
            print(f"  응답 내용 (처음 200자): {response.text[:200]}")
    else:
        print(f"  응답 내용: {response.text[:200]}")

except Exception as e:
    print(f"  ✗ 요청 실패: {type(e).__name__}")
    print(f"  세부사항: {str(e)}")
    import traceback
    traceback.print_exc()

print()

# 5. 과거 날짜로 데이터 수집 재시도
print("5. 과거 날짜로 실제 데이터 수집 테스트")
print("-" * 80)

try:
    from pykrx import stock

    # 2024년 데이터로 시도
    test_date = "20240101"
    print(f"  테스트 날짜: {test_date}")
    print(f"  KOSPI 종목 리스트 조회 시도...")

    tickers = stock.get_market_ticker_list(test_date, market="KOSPI")

    if tickers:
        print(f"  ✓ 종목 리스트 조회 성공: {len(tickers)}개 종목")
        print(f"  상위 5개 종목: {tickers[:5]}")

        # 삼성전자 주가 조회
        print(f"\n  삼성전자(005930) 과거 데이터 조회 시도...")
        df = stock.get_market_ohlcv_by_date("20240101", "20240105", "005930")

        if df is not None and not df.empty:
            print(f"  ✓ 데이터 수집 성공: {len(df)} 건")
            print(df)
        else:
            print(f"  ✗ 데이터 없음")
    else:
        print(f"  ✗ 종목 리스트 조회 실패")

except Exception as e:
    print(f"  ✗ 오류 발생: {type(e).__name__}")
    print(f"  세부사항: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("테스트 완료")
print("=" * 80)
