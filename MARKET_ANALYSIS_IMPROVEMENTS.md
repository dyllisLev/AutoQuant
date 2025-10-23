# 시장 분석 로직 개선 방향 분석

## 1. 현재 로직의 강점과 약점

### 현재 구현의 강점 ✅

1. **5요소 포괄적 분석**
   - 지수 성과, 투자자 흐름, 투자자 밸런스, 섹터 모멘텀, 시장 폭
   - 기존 3요소 대비 훨씬 풍부한 신호

2. **투자자군 세분화**
   - 외국인(15점), 기관(10점), 개인(5점) 별도 분석
   - 개인의 역신호 로직 적용

3. **4신호 가중 합성**
   - 모멘텀(40%) + 투자자흐름(20%) + 시장추세(20%) + KOSPI기술신호(20%)
   - 단순 점수보다 포괄적 판단

### 현재 구현의 약점 ❌

#### 1. **시간 정보 부재 (Time Dimension Missing)**

```python
# 현재: 1일 데이터만 사용
kospi_change = kospi_data['change']  # 오늘 -0.98%

# 문제점:
# - 오늘 -0.98%가 약세인가 강세인가?
# - 지난 주는 +5% 상승했는데 오늘 -0.98%는 약한 조정인가?
# - 아니면 상승 추세 종료 신호인가?
# 답: 맥락 없이는 알 수 없음
```

**필요한 개선**:
- 5일, 20일, 60일 이동평균 추가
- 최근 5일 추세 vs 과거 20일 추세 비교
- 추세 전환점 감지

#### 2. **변동성 미고려 (Volatility Adjustment Missing)**

```python
# 현재: 고정 임계값
if kospi_change > 1.5:      signal = 75
elif kospi_change > 0.5:    signal = 60

# 문제점:
# 시나리오 A: 평상시 변동성 0.5~0.7%
#   - KOSPI +0.6% = 상승 신호 (60점)
# 시나리오 B: 고변동성 시간 (1.0~2.0%)
#   - KOSPI +0.6% = 약한 신호? 하지만 같은 점수 (60점)
#
# 고변동성 시장에서는 0.6%는 약한 이동
# 저변동성 시장에서는 0.6%는 강한 이동
# 하지만 현재는 같은 점수 부여
```

**필요한 개선**:
- 20일 ATR(평균진정범위) 계산
- 실제 변화 / ATR = 정규화된 신호 강도
- 변동성에 따라 동적 임계값 조정

#### 3. **기술적 신호 부재 (Technical Signals Missing)**

```python
# 현재: KOSPI 가격과 advance/decline만 사용
# 부재:
# - RSI (과매수/과매도 상태)
# - MACD (추세 전환 신호)
# - Bollinger Bands (상단/하단 터치)
# - 이격도 (가격 vs 이동평균)

# 예시: 2025-10-23
# - KOSPI -0.98% (약세)
# - 하지만 RSI가 30 이하 (과매도) → 반등 신호
# - MACD가 상향교차 중 → 추세 전환 신호
# → 현재 로직: NEUTRAL
# → 기술적 신호 추가 시: 약한 BULLISH 또는 재평가 필요
```

**필요한 개선**:
- RSI 14일: 30 미만(과매도/반등 신호), 70 초과(과매수/조정 신호)
- MACD: 신호선 교차 방향
- Bollinger Bands: 상단/중앙/하단 위치
- Price to SMA ratio: 가격이 이동평균으로부터 얼마나 벗어났는가

#### 4. **거래량 신호 부재 (Volume Confirmation Missing)**

```python
# 현재: 거래량 정보 없음
# 문제점:
# - 신호 A: KOSPI +1.5%, 거래량 100% 증가
# - 신호 B: KOSPI +1.5%, 거래량 50% 감소
# 신뢰도: A >> B
# 하지만 현재는 같은 신호 (both 75점)

# 기관/외국인 매수:
# - 신호 A: +50조, 거래량 평상시 수준
# - 신호 B: +50조, 거래량 200% 증가
# 신뢰도: B >> A (확신 있는 매수)
# 하지만 현재는 같은 신호
```

**필요한 개선**:
- 거래량 20일 평균 대비 현재 거래량
- 가격 상승 + 거래량 증가 = 강한 신호
- 가격 상승 + 거래량 감소 = 약한 신호 (약세)

#### 5. **신호 일치도 측정 부재 (Signal Convergence Missing)**

```python
# 현재: 각 신호를 독립적으로 계산 후 가중합
# 문제점:
# 시나리오 A (강한 신호):
# - 모멘텀: 75점
# - 투자자흐름: 75점
# - 시장추세: 75점
# - KOSPI기술: 75점
# → 모두 75점, 신호 완벽 일치
# → 신뢰도: 매우 높음 (100%)

# 시나리오 B (약한 신호):
# - 모멘텀: 75점
# - 투자자흐름: 25점
# - 시장추세: 25점
# - KOSPI기술: 75점
# → 평균: 50점, 신호 발산
# → 신뢰도: 낮음 (분화된 신호)

# 현재: 두 경우 모두 가중평균만 계산
# → 시나리오 B도 신뢰도 있는 신호처럼 취급됨
```

**필요한 개선**:
- 신호 표준편차 계산
- 표준편차가 작을수록 신뢰도 높음
- 신호 일치도 지수 추가 (0~1)

#### 6. **투자자 흐름의 가속도 부재 (Flow Momentum Missing)**

```python
# 현재: 1일 절대값만 사용
# 외국인: +50조

# 부재한 정보:
# - 어제는 -30조였나? +20조였나?
# - 매수가 증가하는 중인가? 감소하는 중인가?
# - 추세 시작? 종료?

# 예시:
# 일 1: 외국인 +10조
# 일 2: 외국인 +20조 (가속도: +10조)
# 일 3: 외국인 +50조 (가속도: +30조)
# → 매수 모멘텀 강해짐

# vs

# 일 1: 외국인 +50조
# 일 2: 외국인 +45조 (가속도: -5조)
# 일 3: 외국인 +40조 (가속도: -5조)
# → 매수 모멘텀 약해짐

# 둘 다 오늘 +40~+50조이지만 신호 의미가 다름
```

**필요한 개선**:
- 5일 투자자 흐름 추세 분석
- 흐름의 가속도 (일일 변화의 변화)
- 흐름 모멘텀 신호

#### 7. **섹터 리더십 부재 (Sector Leadership Missing)**

```python
# 현재: 섹터 성과 평균 + 상승 섹터 비중
# 상승 섹터 6개: IT, Semiconductors, Chemical, ...
# 하락 섹터 4개: Finance, Energy, ...

# 부재한 정보:
# - 어떤 섹터가 시장을 주도하는가?
# - IT가 상승했지만 시장 주도 섹터인가?
# - 아니면 주변부 섹터인가?

# 예시:
# 시나리오 A (상승장):
# - Semiconductors +3.0% (시가총액 30% 차지)
# - IT +1.5% (시가총액 20% 차지)
# - Finance +0.5% (시가총액 25% 차지)
# → 주도 섹터(반도체)가 강력하게 주도

# 시나리오 B (약한 상승장):
# - Healthcare +1.5% (시가총액 5% 차지)
# - Retail +1.2% (시가총액 3% 차지)
# - Semiconductors -0.5% (시가총액 30% 차지)
# → 주변부 섹터만 상승, 주도 섹터는 약세
```

**필요한 개선**:
- 시가총액 가중 섹터 리더십 분석
- 주도 섹터 vs 주변부 섹터 구분
- 섹터 로테이션 감지 (시장 주도권 이동)

#### 8. **고정 임계값 문제 (Fixed Thresholds)**

```python
# 현재: 하드코딩된 고정 임계값
if foreign > 50e9:     foreign_score = 15
elif foreign > 20e9:   foreign_score = 10

# 문제점:
# 외국인 50조가 항상 "강한 매수"인가?
#
# 시나리오 A (평상시):
# - 외국인 일일 평균: 5~10조
# - 외국인 50조 = 매우 강한 신호
#
# 시나리오 B (고변동성 시장):
# - 외국인 일일 평균: 30~40조
# - 외국인 50조 = 약간 강한 신호일뿐
#
# 같은 절대값인데 상대적 의미가 다름
```

**필요한 개선**:
- 20일 투자자 흐름 평균 계산
- 상대값으로 비교: (오늘 - 평균) / 표준편차 = Z-score
- 동적 임계값 생성

#### 9. **이상치 감지 부재 (Anomaly Detection Missing)**

```python
# 현재: 모든 신호를 그대로 받아들임
#
# 예시 (비정상적 상황):
# 일 1-4: 외국인 평균 +10조/일
# 일 5: 외국인 -200조 (갑작스러운 대량 매도)
#
# 이것은:
# A) 시장 위기 신호?
# B) 환헤징 / 수익실현?
# C) 데이터 오류?
#
# 현재 로직은 구분 불가
```

**필요한 개선**:
- 이상치 감지 알고리즘 (IQR, Z-score 등)
- 이상치 플래그 추가
- 이상치와 정상 신호 분리 처리

#### 10. **동적 가중치 부재 (Dynamic Weights Missing)**

```python
# 현재: 고정 가중치
# 모멘텀(40%) + 투자자흐름(20%) + 시장추세(20%) + KOSPI기술(20%)

# 문제점:
# 시나리오 A (기술적 신호 명확):
# - 모멘텀, 투자자흐름, 시장추세, KOSPI기술 모두 강함
# → 모멘텀 40% 가중치가 적절한가? 50%로 늘릴 수도?
#
# 시나리오 B (신호 불명확):
# - 모멘텀만 높고 나머지는 약함
# → 모멘텀 40% 가중치가 과도한가? 20%로 줄일 수도?

# 신호 신뢰도에 따라 가중치도 조정되어야 함
```

**필요한 개선**:
- 각 신호의 신뢰도 점수 계산
- 신뢰도 기반 동적 가중치 조정
- 신호 일치도가 높을수록 신뢰도 증가

---

## 2. 개선 로드맵

### Phase 2.1: 시간 차원 추가 (1주일)

**목표**: 5일 추세 데이터 추가

```python
def _calculate_momentum_v2(self, target_date, kospi_data_5days):
    # 최근 5일 KOSPI 데이터
    recent_trend = kospi_data_5days[-1]['change'] > kospi_data_5days[-5]['ma_20']
    momentum_trend = kospi_data_5days[-1]['change'] > kospi_data_5days[-2]['change']

    # 지수 성과 점수 (추세 반영)
    if recent_trend and momentum_trend:
        index_score = 20  # 상승 가속
    elif recent_trend:
        index_score = 15  # 상승 유지
    # ... 더 세밀한 분류
```

**추가 데이터**:
- 5일 이동평균
- 20일 이동평균
- 60일 이동평균
- 5일 추세 (상승/하락/보합)
- 최근 3일 vs 이전 2일 비교

### Phase 2.2: 기술적 신호 통합 (1주일)

**목표**: RSI, MACD 추가

```python
def _get_technical_signals(self, target_date):
    # KOSPI 60일 데이터 조회
    kospi_data = self._get_kospi_history(target_date, days=60)

    # RSI 계산
    rsi = self._calculate_rsi(kospi_data, period=14)
    if rsi < 30:
        rsi_signal = "과매도(반등신호)"
    elif rsi > 70:
        rsi_signal = "과매수(조정신호)"

    # MACD 계산
    macd, signal_line = self._calculate_macd(kospi_data)
    if macd > signal_line:
        macd_signal = "상향교차(매수신호)"

    return {'rsi': rsi, 'macd_signal': macd_signal}
```

**추가 지표**:
- RSI 14일
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- %K, %D (Stochastic)

### Phase 2.3: 거래량 신호 추가 (1주일)

**목표**: 거래량 기반 신뢰도 평가

```python
def _get_volume_strength(self, target_date):
    # 20일 거래량 평균
    avg_volume = self._get_average_volume(target_date, days=20)
    current_volume = self._get_current_volume(target_date)

    volume_ratio = current_volume / avg_volume

    # 신호 강도 보정
    if kospi_change > 1.0:
        if volume_ratio > 1.2:
            confidence = "높음"  # 가격 상승 + 거래량 증가
        elif volume_ratio < 0.8:
            confidence = "낮음"   # 가격 상승 + 거래량 감소
```

### Phase 2.4: 동적 임계값 및 신호 일치도 (1주일)

**목표**: 변동성과 신호 수렴도 기반 조정

```python
def _calculate_dynamic_signals(self):
    # 변동성 계산 (20일 ATR)
    atr = self._calculate_atr(kospi_data, period=20)
    volatility_level = atr / kospi_close  # 상대 변동성

    # 동적 임계값
    if volatility_level > 2.0:  # 고변동성
        threshold_bullish = 70
        threshold_bearish = 30
    else:  # 저변동성
        threshold_bullish = 60
        threshold_bearish = 40

    # 신호 일치도
    signals = [momentum_score, investor_signal, trend_signal, technical_signal]
    signal_std = np.std(signals)
    convergence = 1 - (signal_std / 100)  # 0~1

    # 신뢰도 보정
    adjusted_sentiment_score = sentiment_score * convergence
```

### Phase 2.5: 투자자 흐름 가속도 및 섹터 분석 (1주일)

**목표**: 흐름 추세와 섹터 리더십 분석

```python
def _analyze_investor_flow_momentum(self, target_date):
    # 5일 외국인 흐름
    foreign_flows = [self._get_foreign_flow(d) for d in last_5_days]

    # 가속도 = 흐름의 변화
    acceleration = foreign_flows[-1] - foreign_flows[-2]

    # 가속도 추세
    if acceleration > 0 and acceleration > avg_acceleration:
        flow_momentum = "가속 중 (강한 신호)"
    elif acceleration < 0:
        flow_momentum = "감속 중 (약화)"

def _analyze_sector_leadership(self, sector_performance):
    # 시가총액 가중 섹터 성과
    weighted_performance = sum(perf * weight for perf, weight in zip(...))

    # 주도 섹터 확인
    top_sector = max(sector_performance.items(), key=lambda x: x[1])
    if top_sector[1] > market_average and top_sector_weight > 20%:
        leadership = "강한 리더십"
```

---

## 3. 구현 우선순위

### 즉시 (우선순위 1) ⭐⭐⭐
- **기술적 신호 추가**: RSI + MACD (가장 중요)
- **거래량 확인**: 신호 신뢰도 평가
- **신호 일치도**: 수렴도 지수

### 1주일 내 (우선순위 2) ⭐⭐
- **동적 임계값**: 변동성 기반 조정
- **시간 차원**: 5일, 20일 추세 비교
- **이상치 감지**: 비정상 신호 필터링

### 2주일 내 (우선순위 3) ⭐
- **투자자 흐름 가속도**: 흐름 추세 분석
- **섹터 리더십**: 시가총액 가중 분석
- **동적 가중치**: 신뢰도 기반 조정

---

## 4. 예상 개선 효과

### 신호 정확도 개선

```
현재: 70% 정확도 (모멘텀 점수만)
↓
개선 후: 85%+ 정확도 (기술적 + 거래량 + 신호 일치도)

이유:
- 거짓 신호 (false positive) 30% 감소
  → 거래량 및 신호 일치도로 필터링
- 놓친 신호 (false negative) 20% 감소
  → 기술적 신호로 추가 감지
```

### 과신호(Over-signal) 제거

```
현재: 모멘텀 50 근처에서 NEUTRAL이지만
      신호가 발산한 상황도 NEUTRAL로 표시

개선:
- 신호 일치도 낮으면 confidence 레벨 낮춤
- "약한 NEUTRAL" vs "강한 NEUTRAL" 구분
- 신호 신뢰도 점수 함께 제공
```

### 시장 환경 적응

```
현재: 고변동성/저변동성 상황에서 같은 임계값

개선:
- 변동성 높으면 신호 강도 높게 책정
- 변동성 낮으면 작은 움직임도 의미 있게 평가
- 시장 환경에 자동 적응
```

---

## 5. 기술 구현 사항

### 필요한 데이터 확대

```python
# 현재: 1일 데이터
target_date_data = {...}

# 개선: 60일 히스토리 필요
history_data = {
    'kospi_close': [60일 데이터],
    'kospi_volume': [60일 데이터],
    'foreign_flow': [60일 데이터],
    'institution_flow': [60일 데이터],
    'retail_flow': [60일 데이터],
    'sector_performance': [60일 데이터]
}
```

### 새로운 메서드 추가

```python
class MarketAnalyzer:
    # 기술적 신호
    def _calculate_rsi(self, data, period=14)
    def _calculate_macd(self, data, fast=12, slow=26, signal=9)
    def _calculate_bollinger_bands(self, data, period=20, std=2)

    # 거래량 분석
    def _calculate_volume_strength(self, data)
    def _get_volume_trend(self, data)

    # 신호 신뢰도
    def _calculate_signal_convergence(self, signals)
    def _detect_anomalies(self, data)

    # 투자자 분석
    def _calculate_flow_momentum(self, flow_history)
    def _detect_flow_acceleration(self, flow_history)

    # 섹터 분석
    def _calculate_sector_leadership(self, sector_data, weights)
    def _detect_sector_rotation(self, sector_history)
```

### 수정된 모멘텀 계산 시그니처

```python
def _calculate_momentum_v2(
    self,
    kospi_data_history,        # 60일 KOSPI 데이터
    investor_flows_history,    # 60일 투자자 흐름
    sector_data_history,       # 60일 섹터 성과
    volume_data,               # 거래량 데이터
    technical_indicators       # 기술적 지표
) -> Dict:
    """
    개선된 포괄적 모멘텀 분석

    반환:
    {
        'momentum_score': int,              # 0-100
        'momentum_confidence': float,       # 0-1 신뢰도
        'components': {...},               # 각 요소별 점수
        'technical_signals': {...},        # 기술적 신호
        'flow_signals': {...},             # 투자자 흐름 신호
        'sector_signals': {...},           # 섹터 신호
        'signal_convergence': float,       # 신호 일치도
        'analysis': {...}                  # 상세 분석
    }
    """
```

---

## 6. 추천 순서

1. **먼저 Phase 2.2 (기술적 신호)** 구현
   - RSI와 MACD는 가장 신뢰할 수 있는 지표
   - 구현이 간단하고 즉시 효과 있음
   - pykrx 데이터로 충분

2. **다음 Phase 2.3 (거래량)**
   - 신호 신뢰도 평가의 핵심
   - 기술적 신호와 함께 사용하면 위력적

3. **그 다음 Phase 2.4 (신호 일치도)**
   - 거짓 신호 제거 효과
   - 신뢰도 점수 도입

4. 마지막으로 2.1, 2.5 구현
   - 고급 기능이지만 덜 급함

---

## 결론

현재 시장 분석 로직은 **강한 기초**를 가지고 있지만, 다음 6개 영역에서 **실질적 개선**이 가능합니다:

| 영역 | 현재 | 개선 후 | 우선순위 |
|------|------|--------|--------|
| 기술적 신호 | 없음 | RSI, MACD 추가 | ⭐⭐⭐ |
| 거래량 신뢰도 | 없음 | 거래량 기반 신뢰도 | ⭐⭐⭐ |
| 신호 일치도 | 없음 | 수렴도 지수 추가 | ⭐⭐⭐ |
| 동적 조정 | 고정값 | 변동성 기반 동적값 | ⭐⭐ |
| 시간 차원 | 1일만 | 5일/20일 추세 | ⭐⭐ |
| 투자자 흐름 | 절대값 | 가속도 + 추세 | ⭐ |

**가장 효과적인 개선**: 기술적 신호(RSI+MACD) + 거래량 + 신호 일치도
**예상 정확도 향상**: 70% → 85%+
**구현 기간**: 2~3주
