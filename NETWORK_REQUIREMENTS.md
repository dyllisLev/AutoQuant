# 네트워크 요구사항

AutoQuant 시스템이 실제 주식 데이터를 수집하기 위해 필요한 네트워크 설정입니다.

## 📋 요약

현재 테스트 환경에서는 **모든 외부 도메인에 대한 DNS 조회가 차단**되어 있습니다.
실제 데이터 수집을 위해서는 다음 도메인들에 대한 접근을 허용해야 합니다.

## 🔴 필수 도메인 (우선순위 높음)

### 1. KRX (한국거래소) - 한국 주식 데이터의 핵심
```
✓ data.krx.co.kr              # 주가 데이터
✓ file.krx.co.kr              # 파일 다운로드
✓ open.krx.co.kr              # OPEN API
✓ marketdata.krx.co.kr        # 시장 데이터
✓ kind.krx.co.kr              # 전자공시
```

**용도**: KOSPI, KOSDAQ, KONEX 전체 종목의 주가/시가총액/거래량 데이터

**pykrx 패키지가 이 도메인들을 사용합니다.**

---

### 2. Yahoo Finance - 글로벌 + 한국 주식 데이터
```
✓ query1.finance.yahoo.com    # API 메인
✓ query2.finance.yahoo.com    # API 백업
✓ finance.yahoo.com           # 웹 인터페이스
```

**용도**: 글로벌 주식 데이터, 대체 데이터 소스

**FinanceDataReader 패키지가 이 도메인들을 사용합니다.**

---

### 3. 네이버 금융 (선택사항, 추가 데이터)
```
✓ finance.naver.com           # 실시간 시세, 뉴스
```

**용도**: 실시간 주가, 뉴스, 종목 분석 데이터

---

## 🟡 선택 도메인 (추가 기능용)

### 4. 금융감독원 (공시 정보)
```
✓ dart.fss.or.kr              # 전자공시시스템
```

**용도**: 기업 공시, 재무제표, IR 자료

---

### 5. 기타 데이터 소스
```
✓ comp.fnguide.com            # FnGuide 재무 데이터
✓ www.koreaexim.go.kr         # 환율 정보
✓ ecos.bok.or.kr              # 한국은행 경제통계
```

---

## 🔧 방화벽/프록시 설정 방법

### Option 1: 개별 도메인 허용 (권장)

```
# 필수 도메인
data.krx.co.kr
file.krx.co.kr
open.krx.co.kr
marketdata.krx.co.kr
kind.krx.co.kr

query1.finance.yahoo.com
query2.finance.yahoo.com
finance.yahoo.com

finance.naver.com

# 선택 도메인
dart.fss.or.kr
comp.fnguide.com
www.koreaexim.go.kr
ecos.bok.or.kr
```

### Option 2: 와일드카드 사용 (간편)

```
*.krx.co.kr
*.finance.yahoo.com
*.naver.com
*.fss.or.kr
```

### 프로토콜 및 포트

```
HTTPS: 443 포트 (필수)
HTTP:  80 포트 (리다이렉트용)
```

---

## 🧪 접근 테스트 방법

### 1. Python 스크립트로 테스트
```bash
cd /home/user/AutoQuant
python test_api_access.py
```

이 스크립트는 각 도메인에 대해:
- DNS 조회 가능 여부
- HTTP/HTTPS 접근 가능 여부
- 최종 성공률

을 자동으로 테스트합니다.

### 2. 명령줄로 개별 테스트

```bash
# DNS 조회 테스트
nslookup data.krx.co.kr
nslookup query1.finance.yahoo.com

# HTTP 접근 테스트
curl -I https://data.krx.co.kr
curl -I https://query1.finance.yahoo.com

# Ping 테스트
ping data.krx.co.kr
ping finance.yahoo.com
```

---

## 📊 현재 테스트 환경 상태

```
전체 테스트: 13개 도메인
성공: 0개 (0.0%)
실패: 13개 (100%)

상태: ❌ 모든 도메인 DNS 조회 실패
원인: 네트워크 격리 환경 or 방화벽 차단
```

---

## ✅ 설정 완료 후 확인

도메인 허용 설정을 완료한 후:

```bash
# 1. 접근 테스트 실행
python test_api_access.py

# 2. 실제 데이터 수집 테스트
python collect_data.py --mode daily --market KOSPI --top-n 10

# 3. 디버그 테스트
python debug_test2.py
```

**예상 결과**:
- test_api_access.py에서 성공률 80% 이상
- 실제 주가 데이터 수집 성공
- 로그에 "데이터 수집 완료" 메시지

---

## 🔒 보안 고려사항

### 안전한 도메인들
위에 나열된 모든 도메인은:
- ✓ 공식 금융 기관 및 데이터 제공 사이트
- ✓ HTTPS 암호화 지원
- ✓ 업계 표준 데이터 소스
- ✓ 읽기 전용 API (쓰기 권한 없음)

### 추가 보안 조치
```
1. Outbound 트래픽만 허용 (Inbound는 불필요)
2. HTTPS만 허용하고 HTTP는 리다이렉트만
3. 로그 모니터링으로 비정상 접근 감지
4. IP 화이트리스트 추가 설정 가능
```

---

## 📞 문제 해결

### Q: DNS 조회는 되는데 HTTP 접근이 안 됩니다
A: 방화벽에서 443, 80 포트를 허용했는지 확인

### Q: 일부 도메인만 작동합니다
A: 최소 data.krx.co.kr과 query1.finance.yahoo.com만 허용해도 기본 기능 동작

### Q: VPN/프록시 환경입니다
A: requests 라이브러리의 프록시 설정 필요:
```python
import os
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'
```

### Q: 여전히 안 됩니다
A:
1. test_api_access.py 결과 확인
2. 네트워크 관리자에게 위 도메인 목록 전달
3. 로그 파일 확인 (logs/ 디렉토리)

---

## 📝 참고

- **pykrx 공식**: https://github.com/sharebook-kr/pykrx
- **FinanceDataReader**: https://github.com/FinanceData/FinanceDataReader
- **KRX 정보데이터시스템**: http://data.krx.co.kr

---

**문서 작성일**: 2025-10-22
**테스트 환경**: Claude Code Environment
