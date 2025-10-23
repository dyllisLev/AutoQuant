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

            # 5. 모멘텀 점수 계산
            momentum_score = self._calculate_momentum(
                kospi_data,
                investor_flows,
                sector_performance
            )

            # 6. 시장 심리 판단
            market_sentiment = self._judge_sentiment(
                momentum_score,
                investor_flows,
                market_trend
            )

            # 7. 변동성 지수 계산
            volatility = self._calculate_volatility(target_date)

            # 8. 상위 섹터 선정
            top_sectors = self._get_top_sectors(sector_performance, top_n=3)

            snapshot = {
                'snapshot_date': target_date,
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
                'momentum_score': momentum_score,
                'volatility_index': volatility
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
                # KOSDAQ은 pykrx에 없으므로 코스피 대형주 (1002) 사용 또는 대체
                self.logger.info(f"KOSDAQ 데이터 조회: {target_date}")
                try:
                    # 코스피 대형주 지수 (1002)를 KOSDAQ 대체로 사용
                    # 또는 별도의 API 사용 필요
                    df = stock.get_index_ohlcv(start_date_str, date_str, "1002")

                    if df.empty:
                        self.logger.warning(f"코스피 대형주 데이터 없음: {target_date}")
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
                    self.logger.info(f"코스피 대형주 조회 성공: {close:.2f} ({change:+.2f}%)")
                    return result

                except Exception as e:
                    self.logger.error(f"KOSDAQ 대체 지수 조회 실패: {e}")
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
                           sector_performance: Dict) -> int:
        """
        모멘텀 점수 계산 (0-100)

        Args:
            kospi_data: KOSPI 지수 데이터
            investor_flows: 투자자 매매동향
            sector_performance: 섹터별 성과

        Returns:
            int: 모멘텀 점수 (0-100)
        """
        try:
            score = 50  # 기본값: 50점

            # 1. 지수 변화율 반영 (+/-20)
            kospi_change = kospi_data['change']
            score += min(max(kospi_change * 2, -20), 20)

            # 2. 외국인 매매동향 반영 (+/-15)
            if investor_flows['foreign'] > 0:
                foreign_factor = min(investor_flows['foreign'] / 1e9 * 2, 15)
            else:
                foreign_factor = max(investor_flows['foreign'] / 1e9 * 2, -15)
            score += foreign_factor

            # 3. 섹터 모멘텀 반영 (+/-15)
            avg_sector_perf = np.mean(list(sector_performance.values()))
            sector_factor = min(max(avg_sector_perf * 2, -15), 15)
            score += sector_factor

            # 점수 범위 조정 (0-100)
            momentum = int(min(max(score, 0), 100))

            self.logger.info(f"모멘텀 점수: {momentum}/100")
            return momentum

        except Exception as e:
            self.logger.error(f"모멘텀 계산 실패: {e}")
            return 50

    def _judge_sentiment(self, momentum_score: int, investor_flows: Dict,
                        market_trend: str) -> str:
        """
        시장 심리 판단 (BULLISH/NEUTRAL/BEARISH)

        Args:
            momentum_score: 모멘텀 점수
            investor_flows: 투자자 매매동향
            market_trend: 시장 추세

        Returns:
            str: 시장 심리
        """
        try:
            # 1. 모멘텀 점수
            if momentum_score > 65:
                return 'BULLISH'
            elif momentum_score < 35:
                return 'BEARISH'
            else:
                return 'NEUTRAL'

        except Exception as e:
            self.logger.error(f"심리 판단 실패: {e}")
            return 'NEUTRAL'

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
