"""
백테스팅 엔진
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
from loguru import logger

from src.portfolio.portfolio_manager import PortfolioManager
from src.strategy.base_strategy import BaseStrategy


class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital
        self.results = {}

    def run(self, strategy: BaseStrategy, data: Dict[str, pd.DataFrame],
           start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        백테스팅 실행

        Args:
            strategy: 매매 전략
            data: {ticker: DataFrame} 형태의 주가 데이터
            start_date: 시작일
            end_date: 종료일

        Returns:
            백테스팅 결과
        """
        logger.info(f"백테스팅 시작: 전략={strategy.name}, 종목={len(data)}개")

        portfolio = PortfolioManager(self.initial_capital)
        equity_curve = []
        all_trades = []

        # 각 종목별 시그널 생성
        signals = {}
        for ticker, df in data.items():
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]

            signals[ticker] = strategy.generate_signals(df)

        # 날짜별로 시뮬레이션
        all_dates = sorted(set().union(*[df.index for df in signals.values()]))

        for date in all_dates:
            current_prices = {}

            # 각 종목 처리
            for ticker, df in signals.items():
                if date not in df.index:
                    continue

                row = df.loc[date]
                price = row['Close']
                signal = row.get('Signal', 'HOLD')
                current_prices[ticker] = price

                # 매매 실행
                if signal == 'BUY':
                    # 가용 자금의 20%로 매수
                    max_buy_amount = portfolio.cash * 0.2
                    quantity = int(max_buy_amount / price)
                    if quantity > 0:
                        success = portfolio.buy(ticker, quantity, price)
                        if success:
                            all_trades.append({
                                'date': date,
                                'ticker': ticker,
                                'type': 'BUY',
                                'quantity': quantity,
                                'price': price
                            })

                elif signal == 'SELL':
                    if ticker in portfolio.holdings:
                        quantity = portfolio.holdings[ticker]['quantity']
                        success = portfolio.sell(ticker, quantity, price)
                        if success:
                            all_trades.append({
                                'date': date,
                                'ticker': ticker,
                                'type': 'SELL',
                                'quantity': quantity,
                                'price': price
                            })

            # 자산 추적
            portfolio_value = portfolio.get_portfolio_value(current_prices)
            equity_curve.append({
                'date': date,
                'value': portfolio_value,
                'cash': portfolio.cash
            })

        # 최종 결과 계산
        final_value = equity_curve[-1]['value'] if equity_curve else self.initial_capital
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100

        # 성능 지표 계산
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('date', inplace=True)

        # 수익률 계산
        returns = equity_df['value'].pct_change().dropna()

        # 샤프 비율
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

        # 최대 낙폭 (MDD)
        cummax = equity_df['value'].cummax()
        drawdown = (equity_df['value'] - cummax) / cummax * 100
        max_drawdown = drawdown.min()

        # 승률
        profitable_trades = sum(1 for t in all_trades if t['type'] == 'SELL')
        total_trades = len([t for t in all_trades if t['type'] == 'BUY'])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

        result = {
            'strategy_name': strategy.name,
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'equity_curve': equity_df,
            'trades': all_trades
        }

        logger.info(f"백테스팅 완료: 수익률={total_return:.2f}%, 샤프={sharpe_ratio:.2f}")

        return result

    def generate_report(self, result: Dict) -> str:
        """백테스팅 결과 리포트 생성"""
        report = f"""
        ====================================
        백테스팅 결과 리포트
        ====================================

        전략: {result['strategy_name']}

        자본:
        - 초기 자본: {result['initial_capital']:,.0f}원
        - 최종 자본: {result['final_capital']:,.0f}원
        - 총 수익률: {result['total_return']:.2f}%

        성능 지표:
        - 샤프 비율: {result['sharpe_ratio']:.2f}
        - 최대 낙폭: {result['max_drawdown']:.2f}%
        - 총 거래 횟수: {result['total_trades']}
        - 승률: {result['win_rate']:.2f}%

        ====================================
        """
        return report
