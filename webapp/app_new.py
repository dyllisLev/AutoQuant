"""
AutoQuant Web Application - Mobile & Desktop Responsive
Displays AI stock analysis results with modern UI/UX
"""

from flask import Flask, render_template, jsonify
from datetime import datetime
import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database import Database
from sqlalchemy import text
from loguru import logger

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Korean characters support

# Initialize database
db = Database()


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/signals')
def signals_page():
    """Trading signals page"""
    return render_template('signals.html')


@app.route('/ai-screening')
def ai_screening_page():
    """AI screening results page"""
    return render_template('ai_screening.html')


@app.route('/technical')
def technical_page():
    """Technical analysis page"""
    return render_template('technical.html')


@app.route('/market')
def market_page():
    """Market analysis page"""
    return render_template('market.html')


@app.route('/history')
def history_page():
    """Analysis history page"""
    return render_template('history.html')


# ==================== API ENDPOINTS ====================

@app.route('/api/dashboard')
def get_dashboard_data():
    """Get main dashboard data (latest analysis summary with signals)"""
    session = db.get_session()
    try:
        # Latest completed analysis run (신호 있는 것 우선)
        result = session.execute(text("""
            SELECT
                ar.id, ar.run_date, ar.target_trade_date, ar.status,
                ar.total_stocks_analyzed, ar.ai_candidates_count,
                ar.technical_selections_count, ar.final_signals_count,
                ms.market_sentiment, ms.kospi_trend, ms.kospi_close,
                ms.kospi_change_pct
            FROM analysis_runs ar
            LEFT JOIN market_snapshots ms ON ar.id = ms.analysis_run_id
            WHERE ar.status = 'completed'
              AND EXISTS (SELECT 1 FROM trading_signals WHERE analysis_run_id = ar.id)
            ORDER BY ar.run_date DESC, ar.id DESC
            LIMIT 1
        """))

        run = result.fetchone()
        if not run:
            return jsonify({'error': 'No data available'}), 404

        return jsonify({
            'run_id': run[0],
            'analysis_date': str(run[1]),
            'target_date': str(run[2]),
            'status': run[3],
            'stats': {
                'total_stocks': run[4],
                'ai_candidates': run[5],
                'technical_picks': run[6],
                'final_signals': run[7]
            },
            'market': {
                'sentiment': run[8],
                'trend': run[9],
                'kospi': float(run[10]) if run[10] else 0,
                'change_pct': float(run[11]) if run[11] else 0
            }
        })
    finally:
        session.close()


@app.route('/api/signals')
def get_trading_signals():
    """Get all trading signals for latest run WITH signals"""
    session = db.get_session()
    try:
        # Get latest run with signals
        run_result = session.execute(text("""
            SELECT id FROM analysis_runs
            WHERE status = 'completed'
              AND EXISTS (SELECT 1 FROM trading_signals WHERE analysis_run_id = analysis_runs.id)
            ORDER BY run_date DESC, id DESC
            LIMIT 1
        """))
        run_row = run_result.fetchone()
        if not run_row:
            return jsonify({'signals': []})

        run_id = run_row[0]

        # Get signals
        signals_result = session.execute(text("""
            SELECT
                ts.stock_code, ts.company_name,
                ts.buy_price, ts.target_price, ts.stop_loss_price,
                ts.predicted_return, ts.risk_reward_ratio,
                ts.ai_confidence, ts.status,
                tsel.final_score,
                ac.sector
            FROM trading_signals ts
            LEFT JOIN technical_selections tsel ON ts.tech_selection_id = tsel.id
            LEFT JOIN ai_candidates ac ON ts.stock_code = ac.stock_code
                AND ac.ai_screening_id = (
                    SELECT id FROM ai_screening_results
                    WHERE analysis_run_id = :run_id LIMIT 1
                )
            WHERE ts.analysis_run_id = :run_id
            ORDER BY ts.risk_reward_ratio DESC, ts.predicted_return DESC
        """), {'run_id': run_id})

        signals = []
        for row in signals_result:
            profit = float(row[3]) - float(row[2])
            loss = float(row[2]) - float(row[4])

            signals.append({
                'code': row[0],
                'name': row[1],
                'buy': float(row[2]),
                'target': float(row[3]),
                'stop': float(row[4]),
                'profit_amt': profit,
                'loss_amt': loss,
                'return_pct': float(row[5]),
                'rr_ratio': float(row[6]),
                'ai_conf': float(row[7]) if row[7] else 0,
                'status': row[8],
                'tech_score': float(row[9]) if row[9] else 0,
                'sector': row[10] or '미분류'
            })

        return jsonify({'signals': signals, 'run_id': run_id})
    finally:
        session.close()


@app.route('/api/ai-candidates/<int:run_id>')
def get_ai_candidates(run_id):
    """Get AI screening candidates"""
    session = db.get_session()
    try:
        # Get screening_id
        screening_result = session.execute(text("""
            SELECT id FROM ai_screening_results
            WHERE analysis_run_id = :run_id LIMIT 1
        """), {'run_id': run_id})
        screening_row = screening_result.fetchone()
        if not screening_row:
            return jsonify({'candidates': []})

        # Get candidates
        candidates_result = session.execute(text("""
            SELECT
                stock_code, company_name, ai_score, ai_reasoning,
                sector, current_price, volume, rank_in_batch
            FROM ai_candidates
            WHERE ai_screening_id = :screening_id
            ORDER BY rank_in_batch ASC
        """), {'screening_id': screening_row[0]})

        candidates = []
        for row in candidates_result:
            candidates.append({
                'code': row[0],
                'name': row[1],
                'ai_score': float(row[2]) if row[2] else 0,
                'reason': row[3] or '',
                'sector': row[4] or '미분류',
                'price': float(row[5]) if row[5] else 0,
                'volume': int(row[6]) if row[6] else 0,
                'rank': int(row[7]) if row[7] else 0
            })

        return jsonify({'candidates': candidates})
    finally:
        session.close()


@app.route('/api/technical/<int:run_id>')
def get_technical_analysis(run_id):
    """Get technical screening results"""
    session = db.get_session()
    try:
        result = session.execute(text("""
            SELECT
                ts.stock_code, ts.company_name, ts.current_price,
                ts.sma_score, ts.rsi_score, ts.macd_score,
                ts.bb_score, ts.volume_score, ts.final_score,
                ts.selection_reason, ts.rank_in_batch
            FROM technical_selections ts
            WHERE ts.tech_screening_id = (
                SELECT id FROM technical_screening_results
                WHERE analysis_run_id = :run_id LIMIT 1
            )
            ORDER BY ts.rank_in_batch ASC
        """), {'run_id': run_id})

        selections = []
        for row in result:
            selections.append({
                'code': row[0],
                'name': row[1],
                'price': float(row[2]),
                'scores': {
                    'sma': float(row[3]),
                    'rsi': float(row[4]),
                    'macd': float(row[5]),
                    'bb': float(row[6]),
                    'volume': float(row[7]),
                    'total': float(row[8])
                },
                'reason': row[9],
                'rank': int(row[10])
            })

        return jsonify({'selections': selections})
    finally:
        session.close()


@app.route('/api/market/<int:run_id>')
def get_market_data(run_id):
    """Get market analysis data"""
    session = db.get_session()
    try:
        result = session.execute(text("""
            SELECT
                snapshot_date, kospi_close, kospi_change_pct,
                market_sentiment, kospi_trend, momentum_score,
                retail_net_buy, foreign_net_buy, institution_net_buy,
                advancing_count, declining_count, unchanged_count,
                sector_performance
            FROM market_snapshots
            WHERE analysis_run_id = :run_id LIMIT 1
        """), {'run_id': run_id})

        row = result.fetchone()
        if not row:
            return jsonify({'error': 'No market data'}), 404

        return jsonify({
            'date': str(row[0]),
            'kospi': {
                'close': float(row[1]),
                'change_pct': float(row[2]) if row[2] else 0
            },
            'sentiment': row[3],
            'trend': row[4],
            'momentum': float(row[5]) if row[5] else 0,
            'investors': {
                'individual': float(row[6]) if row[6] else 0,
                'foreigner': float(row[7]) if row[7] else 0,
                'institution': float(row[8]) if row[8] else 0
            },
            'market_breadth': {
                'advancing': int(row[9]) if row[9] else 0,
                'declining': int(row[10]) if row[10] else 0,
                'unchanged': int(row[11]) if row[11] else 0
            },
            'sector_analysis': str(row[12]) if row[12] else None,
            'summary': None  # Not in database schema
        })
    finally:
        session.close()


@app.route('/api/history')
def get_analysis_history():
    """Get analysis history (last 30 runs)"""
    session = db.get_session()
    try:
        result = session.execute(text("""
            SELECT
                ar.id, ar.run_date, ar.target_trade_date, ar.status,
                ar.final_signals_count, ms.market_sentiment, ms.kospi_close
            FROM analysis_runs ar
            LEFT JOIN market_snapshots ms ON ar.id = ms.analysis_run_id
            ORDER BY ar.run_date DESC
            LIMIT 30
        """))

        history = []
        for row in result:
            history.append({
                'run_id': row[0],
                'date': str(row[1]),
                'target_date': str(row[2]),
                'status': row[3],
                'signals': row[4],
                'sentiment': row[5],
                'kospi': float(row[6]) if row[6] else 0
            })

        return jsonify({'history': history})
    finally:
        session.close()


if __name__ == '__main__':
    logger.info("🚀 Starting AutoQuant Web Application")
    logger.info("📱 Mobile & Desktop Responsive")
    logger.info("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
