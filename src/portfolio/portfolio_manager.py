"""
포트폴리오 관리자
"""

import pandas as pd
from typing import Dict, List
from loguru import logger


class PortfolioManager:
    """포트폴리오 관리"""

    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings = {}  # {ticker: {'quantity': int, 'avg_price': float}}
        self.trades = []

    def buy(self, ticker: str, quantity: int, price: float):
        """매수"""
        cost = quantity * price
        if cost > self.cash:
            logger.warning(f"자금 부족: 필요 {cost:,}원, 보유 {self.cash:,}원")
            return False

        self.cash -= cost

        if ticker in self.holdings:
            # 평균 매수가 재계산
            current_qty = self.holdings[ticker]['quantity']
            current_avg = self.holdings[ticker]['avg_price']
            new_avg = (current_qty * current_avg + quantity * price) / (current_qty + quantity)

            self.holdings[ticker]['quantity'] += quantity
            self.holdings[ticker]['avg_price'] = new_avg
        else:
            self.holdings[ticker] = {'quantity': quantity, 'avg_price': price}

        self.trades.append({
            'type': 'BUY',
            'ticker': ticker,
            'quantity': quantity,
            'price': price,
            'amount': cost
        })

        logger.info(f"매수: {ticker} {quantity}주 @ {price:,}원")
        return True

    def sell(self, ticker: str, quantity: int, price: float):
        """매도"""
        if ticker not in self.holdings:
            logger.warning(f"보유하지 않은 종목: {ticker}")
            return False

        if self.holdings[ticker]['quantity'] < quantity:
            logger.warning(f"수량 부족: 보유 {self.holdings[ticker]['quantity']}주")
            return False

        revenue = quantity * price
        self.cash += revenue

        self.holdings[ticker]['quantity'] -= quantity
        if self.holdings[ticker]['quantity'] == 0:
            del self.holdings[ticker]

        self.trades.append({
            'type': 'SELL',
            'ticker': ticker,
            'quantity': quantity,
            'price': price,
            'amount': revenue
        })

        logger.info(f"매도: {ticker} {quantity}주 @ {price:,}원")
        return True

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """포트폴리오 총 가치"""
        holdings_value = sum(
            holding['quantity'] * current_prices.get(ticker, holding['avg_price'])
            for ticker, holding in self.holdings.items()
        )
        return self.cash + holdings_value

    def get_profit_loss(self, current_prices: Dict[str, float]) -> Dict:
        """손익 계산"""
        total_value = self.get_portfolio_value(current_prices)
        profit = total_value - self.initial_capital
        profit_rate = (profit / self.initial_capital) * 100

        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'profit': profit,
            'profit_rate': profit_rate,
            'cash': self.cash
        }

    def get_holdings_summary(self, current_prices: Dict[str, float]) -> List[Dict]:
        """보유 종목 요약"""
        summary = []
        for ticker, holding in self.holdings.items():
            current_price = current_prices.get(ticker, holding['avg_price'])
            value = holding['quantity'] * current_price
            profit = (current_price - holding['avg_price']) * holding['quantity']
            profit_rate = ((current_price / holding['avg_price']) - 1) * 100

            summary.append({
                'ticker': ticker,
                'quantity': holding['quantity'],
                'avg_price': holding['avg_price'],
                'current_price': current_price,
                'value': value,
                'profit': profit,
                'profit_rate': profit_rate
            })

        return summary
