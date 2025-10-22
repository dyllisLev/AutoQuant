#!/usr/bin/env python3
"""
API 접근 가능 여부 테스트
각 도메인에 대한 접근을 테스트하여 차단 여부를 확인합니다.
"""

import requests
import socket
from urllib.parse import urlparse

# 테스트할 도메인 목록
DOMAINS_TO_TEST = {
    'KRX (한국거래소)': [
        'https://data.krx.co.kr',
        'https://file.krx.co.kr',
        'https://open.krx.co.kr',
        'https://marketdata.krx.co.kr',
        'https://kind.krx.co.kr',
    ],
    'Yahoo Finance': [
        'https://query1.finance.yahoo.com',
        'https://query2.finance.yahoo.com',
        'https://finance.yahoo.com',
    ],
    '네이버 금융': [
        'https://finance.naver.com',
    ],
    '금융감독원': [
        'https://dart.fss.or.kr',
    ],
    '기타': [
        'https://comp.fnguide.com',
        'https://www.koreaexim.go.kr',
        'https://ecos.bok.or.kr',
    ]
}

def test_dns(hostname):
    """DNS 조회 테스트"""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror:
        return False, "DNS 조회 실패"

def test_http_access(url, timeout=5):
    """HTTP/HTTPS 접근 테스트"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return True, response.status_code, response.url
    except requests.exceptions.SSLError:
        return False, "SSL 오류", None
    except requests.exceptions.ConnectionError:
        return False, "연결 거부", None
    except requests.exceptions.Timeout:
        return False, "타임아웃", None
    except Exception as e:
        return False, str(e)[:50], None

print("=" * 80)
print("API 도메인 접근 테스트")
print("=" * 80)
print("\n각 도메인에 대한 DNS 조회 및 HTTP 접근을 테스트합니다.\n")

total_tests = 0
success_count = 0
failed_domains = []

for category, urls in DOMAINS_TO_TEST.items():
    print("\n" + "=" * 80)
    print(f"【{category}】")
    print("=" * 80)

    for url in urls:
        total_tests += 1
        parsed = urlparse(url)
        hostname = parsed.netloc

        print(f"\n[{hostname}]")

        # 1. DNS 테스트
        dns_success, dns_result = test_dns(hostname)
        if dns_success:
            print(f"  ✓ DNS 조회: {dns_result}")
        else:
            print(f"  ✗ DNS 조회: {dns_result}")
            failed_domains.append({
                'url': url,
                'reason': 'DNS 실패'
            })
            continue

        # 2. HTTP 접근 테스트
        http_result = test_http_access(url)
        if http_result[0]:
            status_code = http_result[1]
            final_url = http_result[2]

            if status_code < 400:
                print(f"  ✓ HTTP 접근: 성공 (상태코드: {status_code})")
                success_count += 1
            else:
                print(f"  ⚠ HTTP 접근: 경고 (상태코드: {status_code})")
                success_count += 1  # 접근은 되지만 에러 응답

            if final_url != url:
                print(f"  ↳ 리다이렉트: {final_url}")
        else:
            reason = http_result[1]
            print(f"  ✗ HTTP 접근: 실패 ({reason})")
            failed_domains.append({
                'url': url,
                'reason': reason
            })

# 결과 요약
print("\n" + "=" * 80)
print("테스트 결과 요약")
print("=" * 80)
print(f"\n전체 테스트: {total_tests}개")
print(f"성공: {success_count}개")
print(f"실패: {len(failed_domains)}개")
print(f"성공률: {(success_count/total_tests*100):.1f}%")

if failed_domains:
    print("\n" + "=" * 80)
    print("❌ 접근 실패한 도메인 목록")
    print("=" * 80)
    print("\n다음 도메인들을 방화벽/프록시에서 허용해야 합니다:\n")

    for i, domain in enumerate(failed_domains, 1):
        parsed = urlparse(domain['url'])
        print(f"{i:2d}. {parsed.netloc}")
        print(f"    URL: {domain['url']}")
        print(f"    사유: {domain['reason']}\n")

    print("\n【방화벽 설정 방법】")
    print("=" * 80)
    print("\n1. 화이트리스트에 다음 도메인 패턴 추가:")
    unique_domains = set([urlparse(d['url']).netloc for d in failed_domains])
    for domain in sorted(unique_domains):
        print(f"   - {domain}")

    print("\n2. 허용할 프로토콜/포트:")
    print("   - HTTPS (443)")
    print("   - HTTP (80)")

    print("\n3. 와일드카드 도메인:")
    print("   - *.krx.co.kr")
    print("   - *.finance.yahoo.com")
else:
    print("\n✅ 모든 도메인에 정상적으로 접근할 수 있습니다!")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
