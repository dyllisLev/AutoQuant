# Scripts

이 폴더는 유틸리티 스크립트와 데모 프로그램을 포함합니다.

## 📁 파일 목록

### 데이터 수집
- **`collect_data.py`**: 실제 데이터 수집 스크립트 (pykrx 사용)
  - KRX에서 실시간 주식 데이터 수집
  - 네트워크 접근 필요 (krx.co.kr)
  ```bash
  python scripts/collect_data.py
  ```

### 데모
- **`demo_with_mock_data.py`**: 모의 데이터로 전체 시스템 데모
  - 네트워크 없이 실행 가능
  - 데이터 수집 → 분석 → 예측 → 백테스팅 전 과정 시연
  ```bash
  python scripts/demo_with_mock_data.py
  ```

### 유틸리티
- **`check_required_domains.py`**: 필수 도메인 접근 가능 여부 확인
  - KRX, Yahoo Finance, Naver Finance 접근 테스트
  - 네트워크 문제 진단용
  ```bash
  python scripts/check_required_domains.py
  ```

## 🔧 사용 전 준비

모든 스크립트는 프로젝트 루트에서 실행하세요:

```bash
# 프로젝트 루트로 이동
cd /workspace/AutoQuant

# 가상환경 활성화
source venv/bin/activate

# 스크립트 실행
python scripts/<script_name>.py
```

## 📚 관련 문서

- [USER_GUIDE.md](../USER_GUIDE.md): 사용자 가이드
- [NETWORK_REQUIREMENTS.md](../NETWORK_REQUIREMENTS.md): 네트워크 요구사항
- [CLAUDE.md](../CLAUDE.md): 개발자 가이드
