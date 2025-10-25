"""
MarketAnalyzer - 일일 시장 분석 모듈

목표: 시장 현황을 분석하고 MarketSnapshot을 생성
- KOSPI/KOSDAQ 가격 조회
- 투자자 매매동향 분석 (외국인/기관/개인)
- 섹터별 성과 분석
- 시장 추세 판단 (UPTREND/DOWNTREND/RANGE)
- 모멘텀 점수 계산 (0-100)
"""

import os
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from dotenv import load_dotenv

try:
    import pykrx
    from pykrx import stock
except ImportError:
    logger.warning("pykrx 패키지가 설치되지 않았습니다. 설치하세요: pip install pykrx")

# .env 파일 로드
load_dotenv()


class MarketAnalyzer:
    """시장 분석기 클래스"""

    def __init__(self):
        """MarketAnalyzer 초기화"""
        self.logger = logger
        self.analysis_date = None

    def analyze_market(self, target_date: date = None) -> Dict:
        """
        시장 분석 실행 (Layer 2)

        Args:
            target_date: 분석 대상 날짜 (None이면 오늘)

        Returns:
            dict: 시장 분석 결과 (MarketSnapshot 데이터 구조)
                {
                    'snapshot_date': date,
                    'kospi_close': float,
                    'kospi_change': float,
                    'kosdaq_close': float,
                    'kosdaq_change': float,
                    'advance_decline_ratio': float,
                    'foreign_flow': int,
                    'institution_flow': int,
                    'retail_flow': int,
                    'sector_performance': dict,
                    'top_sectors': list,
                    'market_sentiment': str,
                    'momentum_score': int,
                    'volatility_index': float
                }
        """
        if target_date is None:
            target_date = date.today()

        self.analysis_date = target_date
        self.logger.info(f"시장 분석 시작: {target_date}")

        try:
            # 1. 지수 데이터 조회
            kospi_data = self._get_index_data("KOSPI", target_date)
            kosdaq_data = self._get_index_data("KOSDAQ", target_date)

            # 2. 투자자 매매동향 조회
            investor_flows = self._get_investor_flows(target_date)

            # 3. 섹터별 성과 조회
            sector_performance = self._get_sector_performance(target_date)

            # 4. 시장 추세 판단
            market_trend, advance_decline = self._analyze_trend(target_date, kospi_data)

            # 5. 모멘텀 분석 (다중 지표)
            momentum_analysis = self._calculate_momentum(
                kospi_data,
                investor_flows,
                sector_performance
            )
            momentum_score = momentum_analysis['momentum_score']
            momentum_components = momentum_analysis['components']
            momentum_detail = momentum_analysis['analysis']

            # 5.1 기술적 신호 (RSI + MACD) [개선사항 1]
            technical_signals = self._calculate_technical_signals(target_date)

            # 5.2 거래량 신뢰도 평가 [개선사항 2]
            volume_strength = self._calculate_volume_strength(target_date)

            # 6. 시장 심리 판단 (포괄적 분석 + 새로운 신호)
            market_sentiment, sentiment_detail = self._judge_sentiment_v2(
                momentum_score=momentum_score,
                momentum_components=momentum_components,
                investor_flows=investor_flows,
                market_trend=market_trend,
                kospi_data=kospi_data,
                technical_signals=technical_signals,
                volume_strength=volume_strength
            )

            # 7. 변동성 지수 계산
            volatility = self._calculate_volatility(target_date)

            # 8. 상위 섹터 선정
            top_sectors = self._get_top_sectors(sector_performance, top_n=3)

            # 9. 7일 추세 데이터 수집 (AI 스크리닝을 위한 맥락 개선)
            trend_7d = self._get_trend_7d(target_date)
            trend_analysis = self._analyze_trend_pattern(trend_7d, kospi_data, investor_flows, market_trend)

            snapshot = {
                'snapshot_date': target_date,
                'date': target_date.isoformat(),  # ISO 형식으로 저장 (AI 프롬프트 호환)
                'kospi_close': kospi_data['close'],
                'kospi_change': kospi_data['change'],
                'kosdaq_close': kosdaq_data['close'],
                'kosdaq_change': kosdaq_data['change'],
                'advance_decline_ratio': advance_decline,
                'foreign_flow': investor_flows['foreign'],
                'institution_flow': investor_flows['institution'],
                'retail_flow': investor_flows['retail'],
                'sector_performance': sector_performance,
                'top_sectors': top_sectors,
                'market_sentiment': market_sentiment,
                'sentiment_detail': sentiment_detail,
                'momentum_score': momentum_score,
                'volatility_index': volatility,
                'market_trend': market_trend,
                'technical_rsi': technical_signals.get('rsi', 50),
                'technical_macd_direction': technical_signals.get('macd_direction', 'NEUTRAL'),
                'signal_convergence': technical_signals.get('convergence_score', 0.5),
                'trend_7d': trend_7d,
                'trend_analysis': trend_analysis
            }

            self.logger.info(f"시장 분석 완료: KOSPI={kospi_data['close']}, "
                           f"추세={market_trend}, 심리={market_sentiment}, "
                           f"모멘텀={momentum_score}/100")

            return snapshot

        except Exception as e:
            self.logger.error(f"시장 분석 실패: {e}")
            raise

    def _get_index_data(self, index_name: str, target_date: date) -> Dict:
        """
        KOSPI/KOSDAQ 데이터 조회 (pykrx 실제 데이터)

        Args:
            index_name: 'KOSPI' or 'KOSDAQ'
            target_date: 조회 날짜

        Returns:
            dict: {'close': float, 'change': float, 'high': float, 'low': float}
        """
        try:
            from datetime import datetime as dt
            date_str = target_date.strftime('%Y%m%d')
            # 범위 조회용 (이전 365일 부터 현재)
            start_date_str = (target_date - timedelta(days=365)).strftime('%Y%m%d')

            if index_name == "KOSPI":
                # KOSPI 지수 조회 (pykrx 지수코드: 1001)
                self.logger.info(f"KOSPI 데이터 조회: {target_date} (pykrx 코드: 1001)")
                try:
                    # pykrx.stock.get_index_ohlcv() 사용
                    df = stock.get_index_ohlcv(start_date_str, date_str, "1001")

                    if df.empty:
                        self.logger.warning(f"KOSPI 데이터 없음: {target_date}")
                        raise ValueError("Empty dataframe")

                    # 마지막 행 (가장 최근 데이터)
                    latest = df.iloc[-1]

                    # pykrx의 컬럼명 확인
                    # 일반적으로: 시가, 고가, 저가, 종가, 거래량, 거래대금
                    close = float(latest.get('종가', latest.get('Close', 0)))
                    high = float(latest.get('고가', latest.get('High', 0)))
                    low = float(latest.get('저가', latest.get('Low', 0)))

                    # 등락률 계산 (이전 종가와 비교)
                    if len(df) > 1:
                        prev_close = float(df.iloc[-2].get('종가', df.iloc[-2].get('Close', 0)))
                        change = ((close - prev_close) / prev_close * 100) if prev_close != 0 else 0.0
                    else:
                        change = 0.0

                    result = {
                        'close': close,
                        'change': change,
                        'high': high,
                        'low': low
                    }
                    self.logger.info(f"KOSPI 조회 성공: {close:.2f} ({change:+.2f}%)")
                    return result

                except Exception as e:
                    self.logger.error(f"KOSPI pykrx 조회 실패: {e}")
                    raise

            elif index_name == "KOSDAQ":
                # KOSDAQ 지수 조회 (pykrx 지수코드: 2001)
                self.logger.info(f"KOSDAQ 데이터 조회: {target_date} (pykrx 코드: 2001)")
                try:
                    # pykrx.stock.get_index_ohlcv() 사용
                    df = stock.get_index_ohlcv(start_date_str, date_str, "2001")

                    if df.empty:
                        self.logger.warning(f"KOSDAQ 데이터 없음: {target_date}")
                        raise ValueError("Empty dataframe")

                    latest = df.iloc[-1]
                    close = float(latest.get('종가', latest.get('Close', 0)))
                    high = float(latest.get('고가', latest.get('High', 0)))
                    low = float(latest.get('저가', latest.get('Low', 0)))

                    if len(df) > 1:
                        prev_close = float(df.iloc[-2].get('종가', df.iloc[-2].get('Close', 0)))
                        change = ((close - prev_close) / prev_close * 100) if prev_close != 0 else 0.0
                    else:
                        change = 0.0

                    result = {
                        'close': close,
                        'change': change,
                        'high': high,
                        'low': low
                    }
                    self.logger.info(f"KOSDAQ 조회 성공: {close:.2f} ({change:+.2f}%)")
                    return result

                except Exception as e:
                    self.logger.error(f"KOSDAQ pykrx 조회 실패: {e}")
                    raise

            else:
                raise ValueError(f"알 수 없는 지수: {index_name}")

        except Exception as e:
            self.logger.error(f"{index_name} 데이터 조회 실패: {e}")
            raise

    def _get_investor_flows(self, target_date: date) -> Dict[str, int]:
        """
        투자자 매매동향 조회

        Args:
            target_date: 조회 날짜

        Returns:
            dict: {'foreign': int, 'institution': int, 'retail': int}
                  (단위: KRW)
        """
        try:
            # 실제 구현에서는 pykrx.stock.get_investor_flows 사용
            # 현재는 모의 데이터 사용
            self.logger.info(f"투자자 매매동향 조회: {target_date}")

            # 모의 데이터: 양수면 매수, 음수면 매도
            return {
                'foreign': int(45.2e9 + np.random.normal(0, 5e9)),      # 외국인 순매수
                'institution': int(12.3e9 + np.random.normal(0, 3e9)),  # 기관 순매수
                'retail': int(-32.1e9 + np.random.normal(0, 5e9))       # 개인 순매도
            }

        except Exception as e:
            self.logger.error(f"투자자 매매동향 조회 실패: {e}")
            return {
                'foreign': 45200000000,
                'institution': 12300000000,
                'retail': -32100000000
            }

    def _get_sector_performance(self, target_date: date) -> Dict[str, float]:
        """
        섹터별 성과 조회

        Args:
            target_date: 조회 날짜

        Returns:
            dict: {'IT': 1.8, 'Finance': 0.5, ...} (수익률 %)
        """
        try:
            self.logger.info(f"섹터별 성과 조회: {target_date}")

            # 모의 데이터
            sectors = {
                'IT': np.random.normal(1.5, 0.8),
                'Semiconductors': np.random.normal(2.0, 1.0),
                'Finance': np.random.normal(0.3, 0.6),
                'Automotive': np.random.normal(-0.2, 0.7),
                'Chemical': np.random.normal(0.1, 0.5),
                'Steel': np.random.normal(-0.3, 0.6),
                'Energy': np.random.normal(-0.5, 0.8),
                'Healthcare': np.random.normal(0.7, 0.5),
                'Retail': np.random.normal(-0.1, 0.4),
                'Construction': np.random.normal(0.2, 0.6)
            }

            return {sector: round(perf, 2) for sector, perf in sectors.items()}

        except Exception as e:
            self.logger.error(f"섹터별 성과 조회 실패: {e}")
            # 기본 섹터 성과
            return {
                'IT': 1.8,
                'Semiconductors': 2.1,
                'Finance': 0.5,
                'Automotive': -0.3,
                'Chemical': 0.1,
                'Steel': -0.3,
                'Energy': -0.5,
                'Healthcare': 0.7,
                'Retail': -0.1,
                'Construction': 0.2
            }

    def _analyze_trend(self, target_date: date, kospi_data: Dict) -> Tuple[str, float]:
        """
        시장 추세 분석 (UPTREND/DOWNTREND/RANGE)

        Args:
            target_date: 분석 날짜
            kospi_data: KOSPI 지수 데이터

        Returns:
            tuple: (market_trend, advance_decline_ratio)
        """
        try:
            # KOSPI 변화율로 추세 판단
            kospi_change = kospi_data['change']

            if kospi_change > 0.5:
                trend = 'UPTREND'
                ad_ratio = 0.65  # 상승 종목 많음
            elif kospi_change < -0.5:
                trend = 'DOWNTREND'
                ad_ratio = 0.35  # 하락 종목 많음
            else:
                trend = 'RANGE'
                ad_ratio = 0.50  # 중립

            self.logger.info(f"시장 추세: {trend}, 상승/하락 비율: {ad_ratio:.2f}")
            return trend, ad_ratio

        except Exception as e:
            self.logger.error(f"추세 분석 실패: {e}")
            return 'RANGE', 0.50

    def _calculate_momentum(self, kospi_data: Dict, investor_flows: Dict,
                           sector_performance: Dict) -> Dict:
        """
        포괄적인 모멘텀 분석 (다중 지표 사용)

        Args:
            kospi_data: KOSPI 지수 데이터
            investor_flows: 투자자 매매동향
            sector_performance: 섹터별 성과

        Returns:
            dict: {
                'momentum_score': int,      # 0-100 종합 점수
                'components': {...},        # 각 지표별 점수
                'analysis': {...}          # 상세 분석
            }
        """
        try:
            components = {}

            # ===== 1. 지수 성과 (Trend) - 20점 =====
            kospi_change = kospi_data['change']
            if kospi_change > 2.0:
                index_score = 20
            elif kospi_change > 1.0:
                index_score = 15
            elif kospi_change > 0.5:
                index_score = 10
            elif kospi_change > 0:
                index_score = 5
            elif kospi_change > -0.5:
                index_score = 0
            elif kospi_change > -1.0:
                index_score = -5
            elif kospi_change > -2.0:
                index_score = -10
            else:
                index_score = -20
            components['index_trend'] = index_score

            # ===== 2. 투자자 흐름 분석 (30점) =====
            foreign = investor_flows['foreign']
            institution = investor_flows['institution']
            retail = investor_flows['retail']
            total_flow = foreign + institution + retail

            # 외국인 점수 (15점)
            if foreign > 50e9:
                foreign_score = 15
            elif foreign > 20e9:
                foreign_score = 10
            elif foreign > 0:
                foreign_score = 5
            elif foreign > -20e9:
                foreign_score = -5
            elif foreign > -50e9:
                foreign_score = -10
            else:
                foreign_score = -15

            # 기관 점수 (10점)
            if institution > 15e9:
                institution_score = 10
            elif institution > 5e9:
                institution_score = 5
            elif institution > -5e9:
                institution_score = 0
            elif institution > -15e9:
                institution_score = -5
            else:
                institution_score = -10

            # 개인 점수 (5점) - 개인은 종종 반대 신호
            if retail < -20e9:
                retail_score = 5  # 개인 매도 = 기관/외국인 매수 신호
            elif retail < -10e9:
                retail_score = 3
            elif retail < 0:
                retail_score = 1
            elif retail < 10e9:
                retail_score = 0
            else:
                retail_score = -2  # 개인 매수 과열

            investor_score = foreign_score + institution_score + retail_score
            components['investor_flow'] = investor_score

            # ===== 3. 투자자 매매 밸런스 (15점) =====
            # 큰 투자자(외국인+기관) vs 개인
            big_investor = foreign + institution
            if big_investor > 0 and retail < 0:
                balance_score = 15  # 강한 신호: 기관 매수, 개인 매도
            elif big_investor > 0:
                balance_score = 10  # 기관 매수 (개인도 함께)
            elif big_investor > -30e9:
                balance_score = 5   # 약한 신호
            else:
                balance_score = -10 # 기관 매도
            components['investor_balance'] = balance_score

            # ===== 4. 섹터 모멘텀 (20점) =====
            avg_sector_perf = np.mean(list(sector_performance.values()))
            positive_sectors = sum(1 for v in sector_performance.values() if v > 0)
            sector_ratio = positive_sectors / len(sector_performance)

            # 섹터 성과 평균 (10점)
            if avg_sector_perf > 1.0:
                sector_perf_score = 10
            elif avg_sector_perf > 0.5:
                sector_perf_score = 7
            elif avg_sector_perf > 0:
                sector_perf_score = 4
            elif avg_sector_perf > -0.5:
                sector_perf_score = 0
            elif avg_sector_perf > -1.0:
                sector_perf_score = -4
            else:
                sector_perf_score = -10

            # 상승 섹터 비중 (10점)
            if sector_ratio > 0.8:
                sector_breadth_score = 10
            elif sector_ratio > 0.6:
                sector_breadth_score = 7
            elif sector_ratio > 0.5:
                sector_breadth_score = 4
            elif sector_ratio > 0.3:
                sector_breadth_score = 0
            else:
                sector_breadth_score = -10

            sector_score = sector_perf_score + sector_breadth_score
            components['sector_momentum'] = sector_score

            # ===== 5. 시장 구조 분석 (15점) =====
            # 상승/하락 비율로 시장 폭 측정
            advance_decline = kospi_data.get('advance_decline', 0.5)

            if advance_decline > 0.7:
                breadth_score = 15
            elif advance_decline > 0.6:
                breadth_score = 10
            elif advance_decline > 0.5:
                breadth_score = 5
            elif advance_decline > 0.4:
                breadth_score = 0
            elif advance_decline > 0.3:
                breadth_score = -5
            else:
                breadth_score = -15
            components['market_breadth'] = breadth_score

            # ===== 종합 점수 계산 =====
            total_score = (
                index_score +
                investor_score +
                balance_score +
                sector_score +
                breadth_score
            )

            # 0-100 범위로 정규화
            # 최대값: 20+15+15+20+15 = 85
            # 최소값: -20-15-10-20-15 = -80
            normalized_score = 50 + (total_score / 85) * 50
            momentum_score = int(min(max(normalized_score, 0), 100))

            # 상세 분석 정보
            analysis = {
                'index_trend': kospi_change,
                'positive_sectors': f"{positive_sectors}/{len(sector_performance)}",
                'foreign_flow': foreign / 1e9,
                'institution_flow': institution / 1e9,
                'retail_flow': retail / 1e9,
                'big_investor_total': big_investor / 1e9,
                'advance_decline_ratio': advance_decline
            }

            result = {
                'momentum_score': momentum_score,
                'components': components,
                'analysis': analysis
            }

            self.logger.info(f"모멘텀 분석 완료: {momentum_score}/100 "
                           f"(지수:{index_score}, 투자자:{investor_score}, "
                           f"밸런스:{balance_score}, 섹터:{sector_score}, "
                           f"폭:{breadth_score})")

            return result

        except Exception as e:
            self.logger.error(f"모멘텀 계산 실패: {e}")
            return {
                'momentum_score': 50,
                'components': {},
                'analysis': {}
            }

    def _judge_sentiment(self, momentum_score: int, momentum_components: Dict,
                        investor_flows: Dict, market_trend: str, kospi_data: Dict) -> str:
        """
        포괄적 시장 심리 판단 (BULLISH/NEUTRAL/BEARISH)

        다양한 신호를 종합하여 더 정확한 시장 심리 판단:
        - 모멘텀 점수 (주신호, 40%)
        - 투자자 흐름 분석 (20%)
        - 시장 추세 (20%)
        - KOSPI 기술적 신호 (20%)

        Args:
            momentum_score: 모멘텀 점수 (0-100)
            momentum_components: 모멘텀 구성요소 {index_trend, investor_flow, investor_balance, sector_momentum, market_breadth}
            investor_flows: 투자자 매매동향 {foreign, institution, retail}
            market_trend: 시장 추세 (UPTREND/DOWNTREND/RANGE)
            kospi_data: KOSPI 데이터 {change, advance_decline}

        Returns:
            str: 시장 심리 (BULLISH/NEUTRAL/BEARISH)
        """
        try:
            # 기본 신호 점수 (0-100 범위로 정규화)
            signal_scores = []

            # 1. 모멘텀 점수 신호 (40% 가중치)
            momentum_signal = momentum_score
            signal_scores.append(('momentum', momentum_signal, 0.40))

            # 2. 투자자 흐름 신호 (20% 가중치)
            # 기관+외국인 순매수 vs 개인 순매도 = 강한 신호
            big_investor_sum = investor_flows.get('foreign', 0) + investor_flows.get('institution', 0)
            retail_flow = investor_flows.get('retail', 0)

            # 기관/외국인과 개인의 발산도 계산
            if big_investor_sum > 0 and retail_flow < 0:
                # 최고의 신호: 기관/외국인 매수, 개인 매도
                investor_signal = min(85, 50 + (abs(retail_flow) / 1e10))  # 개인 매도가 클수록 높은 점수
            elif big_investor_sum > 0:
                investor_signal = 60
            elif big_investor_sum < 0 and retail_flow < 0:
                investor_signal = 20
            else:
                investor_signal = 50

            signal_scores.append(('investor_flow', investor_signal, 0.20))

            # 3. 시장 추세 신호 (20% 가중치)
            if market_trend == 'UPTREND':
                trend_signal = 75
            elif market_trend == 'DOWNTREND':
                trend_signal = 25
            else:  # RANGE
                trend_signal = 50

            signal_scores.append(('market_trend', trend_signal, 0.20))

            # 4. KOSPI 기술적 신호 (20% 가중치)
            kospi_change = kospi_data.get('change', 0)
            advance_decline = kospi_data.get('advance_decline', 0.5)

            # KOSPI 변화율 신호
            if kospi_change > 1.5:
                kospi_signal = 75
            elif kospi_change > 0.5:
                kospi_signal = 60
            elif kospi_change > -0.5:
                kospi_signal = 50
            elif kospi_change > -1.5:
                kospi_signal = 40
            else:
                kospi_signal = 25

            # 시장 폭(advance/decline) 보정
            if advance_decline > 0.55:  # 상승/하락 비율 > 55% = 강한 신호
                kospi_signal = min(100, kospi_signal + 10)
            elif advance_decline < 0.45:  # 상승/하락 비율 < 45% = 약한 신호
                kospi_signal = max(0, kospi_signal - 10)

            signal_scores.append(('kospi_technical', kospi_signal, 0.20))

            # 5. 종합 심리 점수 계산 (가중 평균)
            weighted_sentiment = sum(score * weight for _, score, weight in signal_scores) / sum(w for _, _, w in signal_scores)

            # 6. 세부 신호 로그
            self.logger.debug(f"심리 판단 신호:")
            for signal_name, signal_value, weight in signal_scores:
                self.logger.debug(f"  - {signal_name}: {signal_value:.0f} (가중치: {weight*100:.0f}%)")
            self.logger.debug(f"종합 심리 점수: {weighted_sentiment:.0f}")

            # 7. 심리 분류 (더 정교한 임계값)
            # 모멘텀과 기타 신호의 조화도 고려
            momentum_component_score = momentum_components.get('investor_balance', 0)  # 가장 중요한 신호

            if weighted_sentiment > 65:
                return 'BULLISH'
            elif weighted_sentiment < 35:
                return 'BEARISH'
            else:
                # NEUTRAL 영역에서 추가 판단
                # momentum_score와 investor_balance 신호가 일치하는지 확인
                if momentum_score > 60 and momentum_component_score > 10:
                    # 모멘텀 점수는 높지만 weighted_sentiment가 낮은 경우
                    # 투자자 흐름이 강하면 BULLISH로 판단
                    if investor_signal > 65:
                        return 'BULLISH'

                return 'NEUTRAL'

        except Exception as e:
            self.logger.error(f"심리 판단 실패: {e}")
            import traceback
            traceback.print_exc()
            return 'NEUTRAL'

    def _judge_sentiment_v2(self, momentum_score: int, momentum_components: Dict,
                           investor_flows: Dict, market_trend: str, kospi_data: Dict,
                           technical_signals: Dict, volume_strength: Dict) -> Tuple[str, Dict]:
        """
        개선된 포괄적 시장 심리 판단 (기술신호 + 거래량 + 신호일치도 포함)

        새로운 신호 추가:
        - 기술적 신호: RSI, MACD
        - 거래량 신뢰도: 신호 강도 보정
        - 신호 일치도: 신호 수렴도 기반 신뢰도 조정

        Args:
            momentum_score: 모멘텀 점수 (0-100)
            momentum_components: 모멘텀 구성요소
            investor_flows: 투자자 매매동향
            market_trend: 시장 추세
            kospi_data: KOSPI 데이터
            technical_signals: 기술적 신호 (RSI, MACD)
            volume_strength: 거래량 신뢰도

        Returns:
            tuple: (market_sentiment: str, detail: dict)
        """
        try:
            # ===== 1단계: 5가지 신호 점수 계산 =====

            # 신호 1: 모멘텀 신호 (40%)
            momentum_signal = momentum_score
            signal_scores = [('momentum', momentum_signal, 0.40)]

            # 신호 2: 투자자 흐름 신호 (20%)
            big_investor_sum = investor_flows.get('foreign', 0) + investor_flows.get('institution', 0)
            retail_flow = investor_flows.get('retail', 0)

            if big_investor_sum > 0 and retail_flow < 0:
                investor_signal = min(85, 50 + (abs(retail_flow) / 1e10))
            elif big_investor_sum > 0:
                investor_signal = 60
            elif big_investor_sum < 0 and retail_flow < 0:
                investor_signal = 20
            else:
                investor_signal = 50

            signal_scores.append(('investor_flow', investor_signal, 0.20))

            # 신호 3: 시장 추세 신호 (15%)
            if market_trend == 'UPTREND':
                trend_signal = 75
            elif market_trend == 'DOWNTREND':
                trend_signal = 25
            else:
                trend_signal = 50

            signal_scores.append(('market_trend', trend_signal, 0.15))

            # 신호 4: KOSPI 기술적 신호 (10%)
            kospi_change = kospi_data.get('change', 0)
            advance_decline = kospi_data.get('advance_decline', 0.5)

            if kospi_change > 1.5:
                kospi_signal = 75
            elif kospi_change > 0.5:
                kospi_signal = 60
            elif kospi_change > -0.5:
                kospi_signal = 50
            elif kospi_change > -1.5:
                kospi_signal = 40
            else:
                kospi_signal = 25

            if advance_decline > 0.55:
                kospi_signal = min(100, kospi_signal + 10)
            elif advance_decline < 0.45:
                kospi_signal = max(0, kospi_signal - 10)

            signal_scores.append(('kospi_technical', kospi_signal, 0.10))

            # 신호 5: 기술적 신호 (RSI + MACD) (15%) [개선사항 1]
            technical_score = technical_signals.get('technical_score', 50)
            signal_scores.append(('technical', technical_score, 0.15))

            # ===== 2단계: 거래량 신뢰도 반영 [개선사항 2] =====
            volume_strength_score = volume_strength.get('strength_score', 0)
            volume_confidence = volume_strength.get('confidence', '중간')

            # ===== 3단계: 신호 일치도 계산 [개선사항 3] =====
            signals_for_convergence = {
                'momentum_score': momentum_signal,
                'investor_signal': investor_signal,
                'trend_signal': trend_signal,
                'kospi_technical': kospi_signal,
                'technical_score': technical_score
            }

            convergence_result = self._calculate_signal_convergence(signals_for_convergence)
            convergence = convergence_result['convergence']
            confidence_multiplier = convergence_result['confidence_multiplier']
            divergence_level = convergence_result['divergence_level']

            # ===== 4단계: 가중 심리 점수 계산 =====
            weighted_sentiment = sum(score * weight for _, score, weight in signal_scores) / \
                               sum(w for _, _, w in signal_scores)

            # 거래량 보정
            adjusted_sentiment = weighted_sentiment + volume_strength_score

            # 신호 일치도에 따른 최종 신뢰도 보정
            final_sentiment_score = adjusted_sentiment * confidence_multiplier

            # ===== 5단계: 심리 분류 및 신뢰도 점수 =====
            if final_sentiment_score > 65:
                market_sentiment = 'BULLISH'
                confidence_level = '높음'
            elif final_sentiment_score < 35:
                market_sentiment = 'BEARISH'
                confidence_level = '높음'
            else:
                # NEUTRAL 영역에서 추가 판단
                if momentum_score > 60 and momentum_components.get('investor_balance', 0) > 10:
                    if investor_signal > 65:
                        market_sentiment = 'BULLISH'
                        confidence_level = '중간'
                    else:
                        market_sentiment = 'NEUTRAL'
                        confidence_level = '낮음' if convergence < 0.4 else '중간'
                else:
                    market_sentiment = 'NEUTRAL'
                    confidence_level = '낮음' if convergence < 0.4 else '중간'

            # ===== 상세 분석 정보 반환 =====
            detail = {
                'weighted_sentiment_score': float(weighted_sentiment),
                'adjusted_sentiment_score': float(adjusted_sentiment),
                'final_sentiment_score': float(final_sentiment_score),
                'confidence_level': confidence_level,
                'signal_convergence': float(convergence),
                'convergence_level': divergence_level,
                'volume_confidence': volume_confidence,
                'volume_strength_score': volume_strength_score,
                'technical_rsi': technical_signals.get('rsi', 50),
                'technical_rsi_signal': technical_signals.get('rsi_signal', 'NEUTRAL'),
                'technical_macd_direction': technical_signals.get('macd_direction', 'NEUTRAL'),
                'signal_breakdown': {
                    'momentum': momentum_signal,
                    'investor_flow': investor_signal,
                    'market_trend': trend_signal,
                    'kospi_technical': kospi_signal,
                    'technical': technical_score
                }
            }

            self.logger.info(f"개선된 심리 판단: {market_sentiment} "
                           f"(점수: {final_sentiment_score:.0f}/100, "
                           f"신뢰도: {confidence_level}, "
                           f"신호일치도: {convergence:.2f})")

            return market_sentiment, detail

        except Exception as e:
            self.logger.error(f"개선된 심리 판단 실패: {e}")
            import traceback
            traceback.print_exc()
            return 'NEUTRAL', {}

    def _calculate_volatility(self, target_date: date) -> float:
        """
        변동성 지수 계산 (VIX 유사)

        Args:
            target_date: 분석 날짜

        Returns:
            float: 변동성 지수
        """
        try:
            # 모의 데이터: 일반적으로 15-25 범위
            volatility = np.random.normal(18.5, 2.0)
            volatility = float(min(max(volatility, 10.0), 40.0))

            self.logger.info(f"변동성 지수: {volatility:.1f}")
            return volatility

        except Exception as e:
            self.logger.error(f"변동성 계산 실패: {e}")
            return 18.5

    def _get_kospi_history(self, target_date: date, days: int = 60) -> pd.DataFrame:
        """
        KOSPI 60일 히스토리 데이터 조회

        Args:
            target_date: 기준 날짜
            days: 조회할 일수 (기본 60일)

        Returns:
            pd.DataFrame: KOSPI 히스토리 데이터
        """
        try:
            end_date = target_date.strftime('%Y%m%d')
            start_date = (target_date - timedelta(days=days*2)).strftime('%Y%m%d')

            # pykrx로 KOSPI 히스토리 조회
            df = stock.get_index_ohlcv(start_date, end_date, "1001")

            if df is not None and len(df) >= days:
                return df.tail(days)
            else:
                self.logger.warning(f"KOSPI 히스토리 데이터 부족: {len(df) if df is not None else 0}일")
                return None

        except Exception as e:
            self.logger.error(f"KOSPI 히스토리 조회 실패: {e}")
            return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        RSI (Relative Strength Index) 계산

        Args:
            prices: 종가 시리즈
            period: 기간 (기본 14일)

        Returns:
            float: RSI 값 (0-100)
        """
        try:
            if prices is None or len(prices) < period:
                return 50.0  # 기본값

            # 변화량 계산
            deltas = prices.diff()

            # 상승분과 하락분 분리
            gains = deltas.where(deltas > 0, 0)
            losses = -deltas.where(deltas < 0, 0)

            # 평균 상승분과 평균 하락분
            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()

            # RS와 RSI 계산
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # 마지막 값 반환
            current_rsi = float(rsi.iloc[-1])
            return min(max(current_rsi, 0), 100)

        except Exception as e:
            self.logger.error(f"RSI 계산 실패: {e}")
            return 50.0

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        MACD (Moving Average Convergence Divergence) 계산

        Args:
            prices: 종가 시리즈
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간
            signal: 신호선 EMA 기간

        Returns:
            dict: MACD, Signal, Histogram 데이터
        """
        try:
            if prices is None or len(prices) < slow:
                return {'macd': 0, 'signal': 0, 'histogram': 0, 'direction': 'NEUTRAL'}

            # EMA 계산
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()

            # MACD 계산
            macd = ema_fast - ema_slow

            # Signal Line (MACD의 9일 EMA)
            signal_line = macd.ewm(span=signal).mean()

            # Histogram
            histogram = macd - signal_line

            current_macd = float(macd.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_histogram = float(histogram.iloc[-1])

            # 신호 방향 (현재와 전일 비교)
            if len(histogram) > 1:
                prev_histogram = float(histogram.iloc[-2])
                if current_histogram > prev_histogram:
                    direction = 'BULLISH'  # 히스토그램이 커짐 = 강해짐
                elif current_histogram < prev_histogram:
                    direction = 'BEARISH'  # 히스토그램이 작아짐 = 약해짐
                else:
                    direction = 'NEUTRAL'
            else:
                direction = 'NEUTRAL'

            return {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_histogram,
                'direction': direction
            }

        except Exception as e:
            self.logger.error(f"MACD 계산 실패: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'direction': 'NEUTRAL'}

    def _calculate_volume_strength(self, target_date: date) -> Dict:
        """
        거래량 신뢰도 평가

        Args:
            target_date: 분석 날짜

        Returns:
            dict: {
                'volume_ratio': float,      # 20일 평균 대비 현재 거래량
                'confidence': str,          # '높음', '중간', '낮음'
                'strength_score': int       # 신호 강도 보정점수 (-10 ~ +10)
            }
        """
        try:
            # 20일 거래량 평균 (모의 데이터)
            avg_volume = np.random.uniform(10e6, 30e6)  # 1000만 ~ 3000만
            current_volume = np.random.uniform(10e6, 35e6)

            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # 신뢰도 판정
            if volume_ratio > 1.3:
                confidence = '높음'
                strength_score = 10  # 신호 강화
            elif volume_ratio > 1.0:
                confidence = '중간'
                strength_score = 5
            elif volume_ratio > 0.7:
                confidence = '낮음'
                strength_score = -5  # 신호 약화
            else:
                confidence = '매우낮음'
                strength_score = -10

            self.logger.debug(f"거래량 신뢰도: {confidence} (비율: {volume_ratio:.2f})")

            return {
                'volume_ratio': float(volume_ratio),
                'confidence': confidence,
                'strength_score': strength_score
            }

        except Exception as e:
            self.logger.error(f"거래량 강도 계산 실패: {e}")
            return {
                'volume_ratio': 1.0,
                'confidence': '중간',
                'strength_score': 0
            }

    def _calculate_technical_signals(self, target_date: date) -> Dict:
        """
        기술적 신호 통합 (RSI + MACD)

        Args:
            target_date: 분석 날짜

        Returns:
            dict: 기술적 신호 종합
        """
        try:
            # KOSPI 히스토리 조회
            history = self._get_kospi_history(target_date, days=60)

            if history is None or len(history) < 14:
                self.logger.warning("기술적 신호 계산 불가: 히스토리 데이터 부족")
                return {
                    'rsi': 50,
                    'rsi_signal': 'NEUTRAL',
                    'macd_direction': 'NEUTRAL',
                    'technical_score': 50
                }

            prices = history['종가']

            # RSI 계산
            rsi = self._calculate_rsi(prices, period=14)

            # RSI 신호 해석
            if rsi > 70:
                rsi_signal = 'OVERBOUGHT'  # 과매수
                rsi_score = 25  # 조정 신호
            elif rsi < 30:
                rsi_signal = 'OVERSOLD'    # 과매도
                rsi_score = 75  # 반등 신호
            elif rsi > 50:
                rsi_signal = 'BULLISH'
                rsi_score = 65
            else:
                rsi_signal = 'BEARISH'
                rsi_score = 35

            # MACD 계산
            macd_data = self._calculate_macd(prices, fast=12, slow=26, signal=9)

            # MACD 신호 해석
            if macd_data['direction'] == 'BULLISH':
                macd_score = 75
            elif macd_data['direction'] == 'BEARISH':
                macd_score = 25
            else:
                macd_score = 50

            # 기술적 신호 종합 (RSI 40%, MACD 60%)
            technical_score = int(rsi_score * 0.4 + macd_score * 0.6)

            self.logger.info(f"기술적 신호: RSI={rsi:.0f}({rsi_signal}), "
                           f"MACD={macd_data['direction']}, "
                           f"종합점수={technical_score}")

            return {
                'rsi': float(rsi),
                'rsi_signal': rsi_signal,
                'macd_direction': macd_data['direction'],
                'macd_value': macd_data['macd'],
                'technical_score': technical_score
            }

        except Exception as e:
            self.logger.error(f"기술적 신호 계산 실패: {e}")
            return {
                'rsi': 50,
                'rsi_signal': 'NEUTRAL',
                'macd_direction': 'NEUTRAL',
                'technical_score': 50
            }

    def _calculate_signal_convergence(self, signals: Dict) -> Dict:
        """
        신호 일치도 지수 계산

        Args:
            signals: {
                'momentum_score': int,
                'investor_signal': int,
                'trend_signal': int,
                'kospi_technical': int,
                'technical_score': int
            }

        Returns:
            dict: {
                'convergence': float (0-1),  # 신호 일치도
                'divergence_level': str,     # 일치도 수준
                'confidence_multiplier': float # 신뢰도 보정계수
            }
        """
        try:
            signal_values = [
                signals.get('momentum_score', 50),
                signals.get('investor_signal', 50),
                signals.get('trend_signal', 50),
                signals.get('kospi_technical', 50),
                signals.get('technical_score', 50)
            ]

            # 평균과 표준편차 계산
            mean_signal = np.mean(signal_values)
            std_signal = np.std(signal_values)

            # 일치도 지수 (표준편차가 작을수록 일치도 높음)
            # std=0 → convergence=1.0 (완벽 일치)
            # std=25 → convergence=0.5 (중간)
            # std=50 → convergence=0.0 (완전 발산)
            convergence = max(0, 1.0 - (std_signal / 50.0))

            # 발산 수준 분류
            if convergence > 0.8:
                divergence_level = '매우높음'
                confidence_multiplier = 1.15  # 신뢰도 15% 증가
            elif convergence > 0.6:
                divergence_level = '높음'
                confidence_multiplier = 1.10
            elif convergence > 0.4:
                divergence_level = '중간'
                confidence_multiplier = 1.0
            elif convergence > 0.2:
                divergence_level = '낮음'
                confidence_multiplier = 0.85  # 신뢰도 15% 감소
            else:
                divergence_level = '매우낮음'
                confidence_multiplier = 0.7   # 신뢰도 30% 감소

            self.logger.debug(f"신호 일치도: {convergence:.2f} ({divergence_level}), "
                            f"표준편차: {std_signal:.1f}")

            return {
                'convergence': float(convergence),
                'divergence_level': divergence_level,
                'confidence_multiplier': float(confidence_multiplier)
            }

        except Exception as e:
            self.logger.error(f"신호 일치도 계산 실패: {e}")
            return {
                'convergence': 0.5,
                'divergence_level': '중간',
                'confidence_multiplier': 1.0
            }

    def _get_top_sectors(self, sector_performance: Dict, top_n: int = 3) -> List[str]:
        """
        상위 섹터 선정

        Args:
            sector_performance: 섹터별 성과
            top_n: 상위 N개 선정

        Returns:
            list: 상위 섹터명 리스트
        """
        try:
            sorted_sectors = sorted(
                sector_performance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            top_sectors = [sector for sector, _ in sorted_sectors[:top_n]]

            self.logger.info(f"상위 섹터: {top_sectors}")
            return top_sectors

        except Exception as e:
            self.logger.error(f"상위 섹터 선정 실패: {e}")
            return ['IT', 'Semiconductors', 'Finance']

    def get_market_snapshot(self, target_date: date = None) -> Dict:
        """
        시장 스냅샷 조회 (분석 결과 반환)

        Args:
            target_date: 분석 대상 날짜

        Returns:
            dict: 시장 분석 결과
        """
        return self.analyze_market(target_date)

    def print_analysis_summary(self, snapshot: Dict) -> None:
        """
        분석 결과를 보기 좋게 출력

        Args:
            snapshot: 시장 분석 결과
        """
        print("\n" + "=" * 70)
        print(f"📊 시장 분석 결과 ({snapshot['snapshot_date']})")
        print("=" * 70)
        print(f"KOSPI: {snapshot['kospi_close']:,.0f} ({snapshot['kospi_change']:+.1f}%)")
        print(f"KOSDAQ: {snapshot['kosdaq_close']:,.0f} ({snapshot['kosdaq_change']:+.1f}%)")
        print(f"시장 심리: {snapshot['market_sentiment']} | 모멘텀: {snapshot['momentum_score']}/100")
        print(f"변동성: {snapshot['volatility_index']:.1f} | 상승/하락: {snapshot['advance_decline_ratio']:.2f}")
        print(f"투자자 흐름: 외국인 {snapshot['foreign_flow']:+,.0f} KRW | "
              f"기관 {snapshot['institution_flow']:+,.0f} KRW | "
              f"개인 {snapshot['retail_flow']:+,.0f} KRW")
        print(f"상위 섹터: {', '.join(snapshot['top_sectors'])}")
        print(f"섹터 성과:")
        for sector, perf in sorted(snapshot['sector_performance'].items(),
                                   key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {sector}: {perf:+.1f}%")
        print("=" * 70 + "\n")

    def screen_stocks_with_ai(self,
                             market_snapshot: Dict,
                             all_stocks: pd.DataFrame,
                             ai_provider: str = "openai") -> Tuple[List[Dict], Dict]:
        """
        Phase 3: AI 기반 종목 스크리닝 (4,359 → 30~40)

        시장 분석 결과를 기반으로 외부 AI API를 사용하여
        4,359개 종목에서 30~40개의 거래 후보 종목을 선정합니다.

        Args:
            market_snapshot: Phase 2 시장 분석 결과 (감정, 흐름, 추세)
            all_stocks: 전체 4,359개 종목의 DataFrame
            ai_provider: AI 제공자 ("openai", "anthropic", "google")

        Returns:
            (candidates, metadata) tuple:
            - candidates: 선정된 30~40개 종목 리스트
            - metadata: 스크리닝 메타데이터 (비용, 신뢰도 등)
        """
        from src.screening.ai_screener import AIScreener

        try:
            self.logger.info(f"Starting Phase 3: AI-based stock screening ({ai_provider})")

            # AIScreener 초기화
            screener = AIScreener(provider=ai_provider)

            # 시장 감정 신뢰도 추출
            sentiment_confidence = market_snapshot.get('sentiment_detail', {}).get(
                'signal_convergence', 0.5
            )

            # AI를 통한 종목 스크리닝
            candidates, metadata = screener.screen_stocks(
                market_snapshot=market_snapshot,
                all_stocks=all_stocks,
                sentiment_confidence=sentiment_confidence
            )

            self.logger.info(f"✅ AI screening complete: {len(candidates)} candidates selected")
            self.logger.info(f"   Cost: ${metadata.get('api_cost', 0):.4f}")
            self.logger.info(f"   Duration: {metadata.get('screening_duration_sec', 0):.1f}s")

            return candidates, metadata

        except Exception as e:
            self.logger.error(f"❌ AI screening failed: {e}")
            raise


    def _get_trend_7d(self, target_date: date) -> List[Dict]:
        """
        7일 추세 데이터 수집 (AI 스크리닝용 맥락 정보)

        Args:
            target_date: 기준 날짜

        Returns:
            list: 최근 7일의 시장 데이터
                [
                    {
                        'date': '2024-10-17',
                        'kospi_close': 2440,
                        'kospi_change': -0.5,
                        'foreign_flow': 12300000000,
                        'institution_flow': 5600000000,
                        'market_trend': 'DOWNTREND'
                    },
                    ...
                ]
        """
        try:
            trend_data = []

            # 과거 7일 조회 (영업일 기준으로 최대 10일 소급)
            for i in range(10):
                check_date = target_date - timedelta(days=i)

                try:
                    # 인덱스 데이터 조회
                    kospi_data = self._get_index_data("KOSPI", check_date)
                    investor_flows = self._get_investor_flows(check_date)

                    # 시장 추세 판단
                    market_trend, _ = self._analyze_trend(check_date, kospi_data)

                    trend_data.append({
                        'date': check_date.isoformat(),
                        'kospi_close': kospi_data['close'],
                        'kospi_change': kospi_data['change'],
                        'foreign_flow': investor_flows.get('foreign', 0),
                        'institution_flow': investor_flows.get('institution', 0),
                        'retail_flow': investor_flows.get('retail', 0),
                        'market_trend': market_trend
                    })

                    # 7일 분량을 모았으면 종료
                    if len(trend_data) >= 7:
                        break

                except Exception as e:
                    self.logger.debug(f"Failed to get trend data for {check_date}: {e}")
                    continue

            # 역순으로 정렬 (오래된 날짜부터 최신 날짜 순서)
            trend_data.reverse()

            self.logger.info(f"7-day trend data collected: {len(trend_data)} days")
            return trend_data

        except Exception as e:
            self.logger.warning(f"Failed to collect 7-day trend data: {e}")
            return []

    def _analyze_trend_pattern(self,
                               trend_7d: List[Dict],
                               today_kospi: Dict,
                               today_investor: Dict,
                               today_trend: str) -> Dict:
        """
        7일 추세 패턴 분석 (AI 스크리닝 맥락 강화)

        Args:
            trend_7d: 7일 추세 데이터
            today_kospi: 오늘의 KOSPI 데이터
            today_investor: 오늘의 투자자 데이터
            today_trend: 오늘의 시장 추세

        Returns:
            dict: 트렌드 분석 결과
                {
                    'direction': 'UPTREND' or 'DOWNTREND' or 'RANGE',
                    'momentum': 'ACCELERATING' or 'DECELERATING' or 'STABLE',
                    'reversal_risk': 'HIGH' or 'MEDIUM' or 'LOW',
                    'foreign_trend': 'SUSTAINED_BUY' or 'SUSTAINED_SELL' or 'CHANGING'
                }
        """
        try:
            if not trend_7d or len(trend_7d) < 3:
                return {
                    'direction': 'UNKNOWN',
                    'momentum': 'UNKNOWN',
                    'reversal_risk': 'UNKNOWN',
                    'foreign_trend': 'UNKNOWN'
                }

            # 1. 추세 방향 판단 (7일 KOSPI 변화)
            kospi_changes = [d.get('kospi_change', 0) for d in trend_7d[-7:]]
            kospi_direction = 'UP' if np.mean(kospi_changes) > 0 else 'DOWN'
            direction = 'UPTREND' if kospi_direction == 'UP' else 'DOWNTREND'

            # 2. 모멘텀 변화 판단 (가속/둔화)
            if len(kospi_changes) >= 2:
                recent_momentum = np.mean(kospi_changes[-3:])  # 최근 3일
                earlier_momentum = np.mean(kospi_changes[:-3])  # 이전 4일
                momentum = 'ACCELERATING' if abs(recent_momentum) > abs(earlier_momentum) else 'DECELERATING'
            else:
                momentum = 'STABLE'

            # 3. 반전 위험 판단
            # - 상승세 약화 또는 하락세 강화 = 높은 위험
            if kospi_direction == 'UP' and momentum == 'DECELERATING':
                reversal_risk = 'HIGH'
            elif kospi_direction == 'DOWN' and momentum == 'ACCELERATING':
                reversal_risk = 'HIGH'
            elif kospi_direction == 'UP' and momentum == 'ACCELERATING':
                reversal_risk = 'LOW'
            else:
                reversal_risk = 'MEDIUM'

            # 4. 외국인 투자자 추세 판단
            foreign_flows = [d.get('foreign_flow', 0) for d in trend_7d[-7:]]
            foreign_positive = sum(1 for f in foreign_flows if f > 0)
            foreign_consecutive = all(f > 0 for f in foreign_flows[-3:])

            if foreign_consecutive:
                foreign_trend = 'SUSTAINED_BUY'
            elif foreign_positive < 3:
                foreign_trend = 'SUSTAINED_SELL'
            else:
                foreign_trend = 'CHANGING'

            return {
                'direction': direction,
                'momentum': momentum,
                'reversal_risk': reversal_risk,
                'foreign_trend': foreign_trend
            }

        except Exception as e:
            self.logger.debug(f"Failed to analyze trend pattern: {e}")
            return {
                'direction': 'UNKNOWN',
                'momentum': 'UNKNOWN',
                'reversal_risk': 'UNKNOWN',
                'foreign_trend': 'UNKNOWN'
            }
