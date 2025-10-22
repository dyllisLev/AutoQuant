#!/usr/bin/env python3
"""
외부 API 직접 호출 테스트
실제 데이터를 가져올 수 있는지 확인합니다.
"""

import requests
import json
from datetime import datetime

print("=" * 80)
print("외부 API 직접 호출 테스트")
print("=" * 80)
print(f"테스트 시간: {datetime.now()}\n")

# 테스트할 API 목록
apis_to_test = [
    {
        'name': 'Yahoo Finance API (삼성전자)',
        'url': 'https://query1.finance.yahoo.com/v8/finance/chart/005930.KS',
        'params': {'interval': '1d', 'range': '5d'}
    },
    {
        'name': 'Yahoo Finance API (AAPL)',
        'url': 'https://query1.finance.yahoo.com/v8/finance/chart/AAPL',
        'params': {'interval': '1d', 'range': '5d'}
    },
    {
        'name': 'KRX 시장데이터 API',
        'url': 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd',
        'params': {
            'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
            'locale': 'ko_KR',
            'mktId': 'STK',
            'trdDd': '20241022'
        }
    },
]

print("\n" + "=" * 80)
print("API 호출 테스트")
print("=" * 80)

results = []

for api_info in apis_to_test:
    print(f"\n【{api_info['name']}】")
    print(f"URL: {api_info['url']}")

    try:
        # GET 요청
        response = requests.get(
            api_info['url'],
            params=api_info.get('params', {}),
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )

        print(f"  ✓ 응답 코드: {response.status_code}")

        if response.status_code == 200:
            # 응답 내용 확인
            content_type = response.headers.get('Content-Type', '')
            print(f"  ✓ Content-Type: {content_type}")

            # 데이터 크기
            data_size = len(response.content)
            print(f"  ✓ 데이터 크기: {data_size:,} bytes")

            # JSON 파싱 시도
            if 'json' in content_type.lower():
                try:
                    data = response.json()
                    print(f"  ✓ JSON 파싱 성공")

                    # 데이터 구조 간단히 출력
                    if isinstance(data, dict):
                        print(f"  ✓ JSON 키: {list(data.keys())[:5]}")
                except json.JSONDecodeError:
                    print(f"  ✗ JSON 파싱 실패")

            results.append({
                'api': api_info['name'],
                'status': '성공',
                'status_code': response.status_code
            })
        else:
            print(f"  ⚠ HTTP 오류: {response.status_code}")
            results.append({
                'api': api_info['name'],
                'status': f'HTTP {response.status_code}',
                'status_code': response.status_code
            })

    except requests.exceptions.ConnectionError as e:
        print(f"  ✗ 연결 실패: {str(e)[:100]}")
        results.append({
            'api': api_info['name'],
            'status': '연결 실패',
            'error': str(e)[:100]
        })

    except requests.exceptions.Timeout:
        print(f"  ✗ 타임아웃")
        results.append({
            'api': api_info['name'],
            'status': '타임아웃',
            'error': 'Request timeout'
        })

    except Exception as e:
        print(f"  ✗ 오류: {str(e)[:100]}")
        results.append({
            'api': api_info['name'],
            'status': '오류',
            'error': str(e)[:100]
        })

# 결과 요약
print("\n" + "=" * 80)
print("테스트 결과 요약")
print("=" * 80)

success_count = sum(1 for r in results if r['status'] == '성공')
total_count = len(results)

print(f"\n전체 API: {total_count}개")
print(f"성공: {success_count}개")
print(f"실패: {total_count - success_count}개")
print(f"성공률: {(success_count/total_count*100):.1f}%\n")

# 결과 상세
print("\n" + "=" * 80)
print("상세 결과")
print("=" * 80)

for i, result in enumerate(results, 1):
    status_icon = "✓" if result['status'] == '성공' else "✗"
    print(f"\n{i}. {status_icon} {result['api']}")
    print(f"   상태: {result['status']}")
    if 'error' in result:
        print(f"   오류: {result['error']}")

# 결론
print("\n" + "=" * 80)
print("결론")
print("=" * 80)

if success_count > 0:
    print("\n✅ 일부 외부 API에 접근할 수 있습니다.")
    print("   데이터 수집이 가능한 상태입니다.")
elif success_count == total_count:
    print("\n✅ 모든 외부 API에 정상적으로 접근할 수 있습니다.")
    print("   데이터 수집이 완전히 가능한 상태입니다.")
else:
    print("\n❌ 외부 API에 접근할 수 없습니다.")
    print("   현재 환경에서는 외부 데이터 수집이 불가능합니다.")
    print("\n【해결 방법】")
    print("   1. 네트워크 연결 확인")
    print("   2. 방화벽/프록시 설정 확인")
    print("   3. DNS 서버 설정 확인")
    print("   4. VPN 또는 프록시 사용 고려")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
