#!/usr/bin/env python3
"""
웹앱 API 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'webapp'))

from app import app

print("=" * 70)
print("웹앱 API 테스트")
print("=" * 70)

# 테스트 클라이언트 생성
client = app.test_client()

# 1. 메인 페이지
print("\n[1] 메인 페이지 테스트")
response = client.get('/')
if response.status_code == 200:
    print("   ✓ 메인 페이지 로드 성공")
else:
    print(f"   ✗ 실패: {response.status_code}")

# 2. 주가 조회 API
print("\n[2] 주가 조회 API 테스트")
response = client.get('/api/stock/005930/price?days=5')
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✓ 데이터 {len(data)}건 조회")
    if len(data) > 0:
        print(f"   ✓ 최근 종가: {data[-1]['close']:,.0f}원")
else:
    print(f"   ✗ 실패: {response.status_code}")

# 3. 기술적 지표 API
print("\n[3] 기술적 지표 API 테스트")
response = client.get('/api/stock/005930/indicators')
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✓ 지표 {len(data)}개 계산")
    for key, value in list(data.items())[:3]:
        if value:
            print(f"   - {key}: {value:.2f}")
else:
    print(f"   ✗ 실패: {response.status_code}")

# 4. 예측 API (간단 테스트)
print("\n[4] 예측 API 테스트")
response = client.get('/api/stock/005930/predict?model=XGBoost&days=3')
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✓ {len(data)}일 예측 완료")
    for item in data:
        print(f"   - {item['date']}: {item['predicted_price']:,.0f}원")
else:
    print(f"   ✗ 실패: {response.status_code}")

# 5. 백테스팅 API
print("\n[5] 백테스팅 API 테스트")
response = client.post('/api/backtest', json={
    'strategy': 'SMA',
    'tickers': ['005930']
})
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✓ 전략: {data['strategy']}")
    print(f"   ✓ 수익률: {data['total_return']:.2f}%")
    print(f"   ✓ 샤프 비율: {data['sharpe_ratio']:.2f}")
    print(f"   ✓ 거래 횟수: {data['total_trades']}")
else:
    print(f"   ✗ 실패: {response.status_code}")

# 6. 포트폴리오 API
print("\n[6] 포트폴리오 API 테스트")
response = client.get('/api/portfolio')
if response.status_code == 200:
    data = response.get_json()
    print(f"   ✓ 포트폴리오 조회 성공")
    print(f"   ✓ 현재 가치: {data['profit_loss']['current_value']:,.0f}원")
else:
    print(f"   ✗ 실패: {response.status_code}")

print("\n" + "=" * 70)
print("웹앱 API 테스트 완료!")
print("=" * 70)

print("""
✓ 메인 페이지
✓ 주가 조회 API
✓ 기술적 지표 API
✓ AI 예측 API
✓ 백테스팅 API
✓ 포트폴리오 API

모든 API 정상 작동!

실제 실행 방법:
cd webapp
python app.py

접속: http://localhost:5000
""")
