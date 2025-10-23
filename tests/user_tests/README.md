# User Test Suite

이 폴더는 USER_TEST_CHECKLIST.md를 기반으로 한 사용자 테스트 파일들을 포함합니다.

## 폴더 구조

```
tests/user_tests/
├── README.md                              # 이 파일
├── test_01_kis_data_collection.py         # 1.1 PostgreSQL 종목 조회 테스트
├── test_02_daily_ohlcv.py                 # 1.2 일봉 데이터 조회 테스트
└── TEST_RESULTS_01_DATA_COLLECTION.md     # 1단계 테스트 결과
```

## 테스트 실행 방법

**중요**: 반드시 가상환경을 활성화하고 프로젝트 루트에서 실행하세요.

```bash
# 프로젝트 루트로 이동
cd /workspace/AutoQuant

# 가상환경 활성화
source venv/bin/activate

# 개별 테스트 실행
python tests/user_tests/test_01_kis_data_collection.py
python tests/user_tests/test_02_daily_ohlcv.py

# 또는 모든 테스트 실행 (향후 추가 예정)
python tests/user_tests/run_all_tests.py
```

## 테스트 결과

각 테스트 단계별 상세 결과는 해당 `TEST_RESULTS_*.md` 파일에서 확인할 수 있습니다.

- [x] 1단계: 데이터 수집 모듈 (TEST_RESULTS_01_DATA_COLLECTION.md)
- [ ] 2단계: 기술적 지표 계산
- [ ] 3단계: AI 예측 모델
- [ ] 4단계: 매매 전략
- [ ] 5단계: 백테스팅
- [ ] 6단계: 포트폴리오 관리
- [ ] 7단계: 웹 대시보드
- [ ] 8단계: DB CRUD 작업
- [ ] 9단계: 성능 및 안정성

## 참고 문서

- [USER_TEST_CHECKLIST.md](../../USER_TEST_CHECKLIST.md): 전체 테스트 체크리스트
- [CLAUDE.md](../../CLAUDE.md): 프로젝트 가이드
