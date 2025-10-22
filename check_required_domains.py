#!/usr/bin/env python3
"""
데이터 수집 API 도메인 확인 스크립트
"""

print("=" * 70)
print("AutoQuant 데이터 수집을 위해 허용해야 하는 도메인")
print("=" * 70)

print("\n" + "=" * 70)
print("1. pykrx (한국거래소 데이터)")
print("=" * 70)
print("""
주요 도메인:
  ✓ data.krx.co.kr              # KRX 데이터 포털
  ✓ file.krx.co.kr              # KRX 파일 서버
  ✓ open.krx.co.kr              # KRX OPEN API
  ✓ marketdata.krx.co.kr        # 시장 데이터

추가 도메인 (일부 기능):
  ✓ finance.naver.com           # 네이버 금융
  ✓ asp1.krx.co.kr             # KRX ASP 서버
""")

print("\n" + "=" * 70)
print("2. FinanceDataReader (글로벌 + 한국 데이터)")
print("=" * 70)
print("""
주요 도메인:
  ✓ query1.finance.yahoo.com    # Yahoo Finance API
  ✓ query2.finance.yahoo.com    # Yahoo Finance API (백업)
  ✓ finance.yahoo.com           # Yahoo Finance 웹

한국 데이터:
  ✓ data.krx.co.kr              # KRX
  ✓ kind.krx.co.kr              # 전자공시

추가 데이터 소스:
  ✓ comp.fnguide.com            # FnGuide (재무 데이터)
  ✓ www.investing.com           # Investing.com
""")

print("\n" + "=" * 70)
print("3. 추가 데이터 소스 (선택사항)")
print("=" * 70)
print("""
뉴스/공시:
  ✓ dart.fss.or.kr              # 금융감독원 전자공시
  ✓ kind.krx.co.kr              # KRX 공시

환율/기타:
  ✓ www.koreaexim.go.kr         # 수출입은행 환율
  ✓ ecos.bok.or.kr              # 한국은행 경제통계
""")

print("\n" + "=" * 70)
print("4. 방화벽 설정 예시")
print("=" * 70)
print("""
【화이트리스트 도메인】
필수:
  - *.krx.co.kr
  - *.finance.yahoo.com
  - finance.naver.com

선택:
  - dart.fss.or.kr
  - comp.fnguide.com
  - www.koreaexim.go.kr
  - ecos.bok.or.kr

【프로토콜/포트】
  - HTTPS (443)
  - HTTP (80) - 일부 리다이렉트용
""")

print("\n" + "=" * 70)
print("5. 네트워크 테스트 명령어")
print("=" * 70)
print("""
# 도메인 접근 테스트
curl -I https://data.krx.co.kr
curl -I https://query1.finance.yahoo.com
curl -I https://finance.naver.com

# DNS 확인
nslookup data.krx.co.kr
nslookup query1.finance.yahoo.com

# Traceroute
traceroute data.krx.co.kr
""")

print("\n" + "=" * 70)
print("6. Python으로 접근 테스트")
print("=" * 70)
print("""
다음 스크립트를 실행하여 각 도메인 접근 가능 여부 확인:
  python test_api_access.py
""")

print("\n" + "=" * 70)
