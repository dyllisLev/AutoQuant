#!/usr/bin/env python3
"""
AutoQuant 웹 대시보드
Flask 기반 웹 애플리케이션
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from src.data_collection.mock_data import MockDataGenerator
from src.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from src.analysis.prediction_models import LSTMPredictor, XGBoostPredictor
from src.strategy import SMAStrategy, RSIStrategy
from src.execution import BacktestEngine
from src.portfolio import PortfolioManager

app = Flask(__name__)
CORS(app)

# 데이터베이스 초기화
db = Database("sqlite:///data/autoquant_webapp.db")
db.create_tables()

# 모의 데이터 생성기
generator = MockDataGenerator()

# 글로벌 변수
portfolio = PortfolioManager(initial_capital=10000000)


@app.route('/')
def index():
    """메인 대시보드"""
    return render_template('dashboard.html')


@app.route('/api/stocks')
def get_stocks():
    """종목 리스트"""
    stocks = db.get_all_stocks()
    return jsonify([{
        'ticker': s.ticker,
        'name': s.name,
        'market': s.market
    } for s in stocks])


@app.route('/api/stock/<ticker>/price')
def get_stock_price(ticker):
    """주가 데이터"""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    df = db.get_stock_prices(ticker, start_date, end_date)

    if df.empty:
        # 모의 데이터 생성
        df = generator.generate_stock_data(
            ticker,
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d'),
            70000
        )

    # JSON 변환
    data = []
    for idx, row in df.iterrows():
        data.append({
            'date': idx.strftime('%Y-%m-%d'),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume'])
        })

    return jsonify(data)


@app.route('/api/stock/<ticker>/indicators')
def get_stock_indicators(ticker):
    """기술적 지표"""
    days = request.args.get('days', 60, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    df = generator.generate_stock_data(
        ticker,
        start_date.strftime('%Y%m%d'),
        end_date.strftime('%Y%m%d'),
        70000
    )

    df = TechnicalIndicators.add_all_indicators(df)

    # 최근 값만
    latest = df.iloc[-1]

    indicators = {
        'RSI': float(latest.get('RSI_14', 0)) if latest.get('RSI_14') else None,
        'MACD': float(latest.get('MACD', 0)) if latest.get('MACD') else None,
        'MACD_Signal': float(latest.get('MACD_Signal', 0)) if latest.get('MACD_Signal') else None,
        'SMA_5': float(latest.get('SMA_5', 0)) if latest.get('SMA_5') else None,
        'SMA_20': float(latest.get('SMA_20', 0)) if latest.get('SMA_20') else None,
        'BB_Upper': float(latest.get('BB_Upper', 0)) if latest.get('BB_Upper') else None,
        'BB_Lower': float(latest.get('BB_Lower', 0)) if latest.get('BB_Lower') else None,
    }

    return jsonify(indicators)


@app.route('/api/stock/<ticker>/predict')
def predict_stock(ticker):
    """주가 예측"""
    model_type = request.args.get('model', 'LSTM')
    days = request.args.get('days', 7, type=int)

    # 데이터 생성
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    df = generator.generate_stock_data(
        ticker,
        start_date.strftime('%Y%m%d'),
        end_date.strftime('%Y%m%d'),
        70000
    )

    # 예측
    if model_type == 'LSTM':
        model = LSTMPredictor()
        X, y = model.prepare_data(df)
        model.train(X, y, epochs=5)
        predictions = model.predict_future(df, days=days)
    else:
        model = XGBoostPredictor()
        X, y = model.prepare_data(df)
        model.train(X, y)
        predictions = model.predict_future(df, days=days)

    # 결과
    result = []
    for i, pred in enumerate(predictions):
        future_date = end_date + timedelta(days=i+1)
        result.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'predicted_price': float(pred)
        })

    return jsonify(result)


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """백테스팅 실행"""
    data = request.json
    strategy_name = data.get('strategy', 'SMA')
    tickers = data.get('tickers', ['005930'])

    # 데이터 생성
    stock_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    for ticker in tickers:
        df = generator.generate_stock_data(
            ticker,
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d'),
            50000 + int(ticker) % 30000
        )
        stock_data[ticker] = df

    # 전략 선택
    if strategy_name == 'SMA':
        strategy = SMAStrategy(short_period=5, long_period=20)
    else:
        strategy = RSIStrategy()

    # 백테스팅
    engine = BacktestEngine(initial_capital=10000000)
    result = engine.run(strategy, stock_data)

    # 결과 반환
    return jsonify({
        'strategy': result['strategy_name'],
        'initial_capital': result['initial_capital'],
        'final_capital': result['final_capital'],
        'total_return': result['total_return'],
        'sharpe_ratio': result['sharpe_ratio'],
        'max_drawdown': result['max_drawdown'],
        'total_trades': result['total_trades'],
        'win_rate': result['win_rate']
    })


@app.route('/api/portfolio')
def get_portfolio():
    """포트폴리오 조회"""
    current_prices = {'005930': 72000, '000660': 135000}
    holdings = portfolio.get_holdings_summary(current_prices)
    pl = portfolio.get_profit_loss(current_prices)

    return jsonify({
        'holdings': holdings,
        'profit_loss': pl
    })


if __name__ == '__main__':
    print("=" * 60)
    print("AutoQuant 웹 대시보드 시작")
    print("=" * 60)
    print("\n접속 URL: http://localhost:5000")
    print("\n종료: Ctrl+C\n")

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
