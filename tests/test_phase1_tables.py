"""
Phase 1: 데이터베이스 스키마 확장 테스트
TradingSignal과 MarketSnapshot 테이블 생성 및 CRUD 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.database import Database
from datetime import date, datetime, timedelta
import pandas as pd


def test_table_creation():
    """테이블 생성 테스트"""
    print("\n" + "=" * 70)
    print("🔧 Task 1.3: 테이블 생성 및 검증")
    print("=" * 70)

    db = Database()

    # 테이블 생성
    print("\n[1] 테이블 생성 중...")
    db.create_tables()
    print("✅ 테이블 생성 완료")

    return db


def test_trading_signal_crud(db):
    """TradingSignal CRUD 테스트"""
    print("\n[2] TradingSignal CRUD 테스트")
    print("-" * 70)

    # 1. 종목 먼저 생성
    print("\n2.1) 테스트 종목 생성...")
    stock = db.add_stock("005930", "삼성전자", "KOSPI", "전자")
    print(f"✅ 종목 생성: {stock.ticker} - {stock.name}")

    # 2. TradingSignal 생성
    print("\n2.2) 거래 신호 생성...")
    signal_data = {
        'stock_id': stock.id,
        'analysis_date': date.today(),
        'target_trade_date': date.today() + timedelta(days=3),
        'buy_price': 78300.0,
        'target_price': 79500.0,
        'stop_loss_price': 77200.0,
        'ai_confidence': 75,
        'predicted_return': 1.54,
        'current_rsi': 52.0,
        'current_macd': 125.0,
        'current_bollinger_position': 'middle',
        'market_trend': 'uptrend',
        'investor_flow': 'positive',
        'sector_momentum': 'strong',
        'ai_reasoning': 'AI 칩 수요 + 외국인 매수세',
        'status': 'pending'
    }

    try:
        signal = db.create_trading_signal(signal_data)
        print(f"✅ 신호 생성: ID={signal.id}")
        print(f"   - 매수가: {signal.buy_price:,.0f} KRW")
        print(f"   - 목표가: {signal.target_price:,.0f} KRW")
        print(f"   - 손절가: {signal.stop_loss_price:,.0f} KRW")
        print(f"   - AI신뢰도: {signal.ai_confidence}%")
        print(f"   - 상태: {signal.status}")
    except Exception as e:
        print(f"❌ 신호 생성 실패: {e}")
        return False

    # 3. TradingSignal 조회 (날짜 기준)
    print("\n2.3) 신호 조회 (날짜 기준)...")
    signals = db.get_trading_signals_by_date(date.today().isoformat())
    print(f"✅ 조회 결과: {len(signals)}개 신호")
    for sig in signals:
        print(f"   - {sig.stock_id}: {sig.buy_price:,.0f} → {sig.target_price:,.0f}")

    # 4. TradingSignal 조회 (ID 기준)
    print("\n2.4) 신호 조회 (ID 기준)...")
    retrieved_signal = db.get_trading_signal_by_id(signal.id)
    if retrieved_signal:
        print(f"✅ 신호 조회 성공: ID={retrieved_signal.id}")
    else:
        print(f"❌ 신호 조회 실패")
        return False

    # 5. TradingSignal 수정
    print("\n2.5) 신호 수정 (매매 후 상태 업데이트)...")
    update_data = {
        'status': 'executed',
        'executed_price': 78300.0,
        'executed_date': datetime.now(),
        'actual_return': 1.54
    }
    updated_signal = db.update_trading_signal(signal.id, update_data)
    if updated_signal:
        print(f"✅ 신호 수정 성공")
        print(f"   - 상태: {updated_signal.status}")
        print(f"   - 체결가: {updated_signal.executed_price:,.0f} KRW")
        print(f"   - 실제 수익률: {updated_signal.actual_return:.2f}%")
    else:
        print(f"❌ 신호 수정 실패")
        return False

    # 6. 대기 신호 조회 (새로운 신호 생성해서 테스트)
    print("\n2.6) 대기 중인 신호 조회...")
    # 새로운 종목
    stock2 = db.add_stock("000660", "SK하이닉스", "KOSPI", "반도체")
    signal_data2 = {
        'stock_id': stock2.id,
        'analysis_date': date.today(),
        'target_trade_date': date.today() + timedelta(days=1),
        'buy_price': 130000.0,
        'target_price': 134500.0,
        'stop_loss_price': 127000.0,
        'ai_confidence': 72,
        'predicted_return': 3.46,
        'status': 'pending'
    }
    signal2 = db.create_trading_signal(signal_data2)
    print(f"✅ 새로운 신호 생성: ID={signal2.id}")

    pending_signals = db.get_pending_trading_signals()
    print(f"✅ 대기 신호 조회: {len(pending_signals)}개")
    for sig in pending_signals:
        print(f"   - {sig.stock_id}: 신뢰도 {sig.ai_confidence}%")

    return True


def test_market_snapshot_crud(db):
    """MarketSnapshot CRUD 테스트"""
    print("\n[3] MarketSnapshot CRUD 테스트")
    print("-" * 70)

    # 1. MarketSnapshot 생성
    print("\n3.1) 시장 스냅샷 생성...")
    snapshot_data = {
        'snapshot_date': date.today(),
        'kospi_close': 2467.0,
        'kospi_change': 0.8,
        'kosdaq_close': 778.0,
        'kosdaq_change': -0.3,
        'advance_decline_ratio': 0.65,
        'foreign_flow': 45200000000,  # 450억 KRW
        'institution_flow': 12300000000,  # 123억 KRW
        'retail_flow': -32100000000,  # -321억 KRW
        'sector_performance': {
            'IT': 1.8,
            'Finance': 0.5,
            'Semiconductors': 2.1,
            'Automotive': -0.3
        },
        'top_sectors': ['IT', 'Semiconductors', 'Finance'],
        'market_sentiment': 'bullish',
        'momentum_score': 75,
        'volatility_index': 18.5
    }

    try:
        snapshot = db.create_market_snapshot(snapshot_data)
        print(f"✅ 스냅샷 생성: {snapshot.snapshot_date}")
        print(f"   - KOSPI: {snapshot.kospi_close} ({snapshot.kospi_change:+.1f}%)")
        print(f"   - KOSDAQ: {snapshot.kosdaq_close} ({snapshot.kosdaq_change:+.1f}%)")
        print(f"   - 시장 심리: {snapshot.market_sentiment}")
        print(f"   - 모멘텀 점수: {snapshot.momentum_score}/100")
    except Exception as e:
        print(f"❌ 스냅샷 생성 실패: {e}")
        return False

    # 2. MarketSnapshot 조회
    print("\n3.2) 스냅샷 조회...")
    retrieved_snapshot = db.get_market_snapshot(date.today().isoformat())
    if retrieved_snapshot:
        print(f"✅ 스냅샷 조회 성공")
        print(f"   - KOSPI: {retrieved_snapshot.kospi_close}")
        print(f"   - 섹터: {retrieved_snapshot.top_sectors}")
    else:
        print(f"❌ 스냅샷 조회 실패")
        return False

    # 3. 최신 스냅샷 조회
    print("\n3.3) 최신 스냅샷 조회...")
    latest = db.get_latest_market_snapshot()
    if latest:
        print(f"✅ 최신 스냅샷: {latest.snapshot_date}")
    else:
        print(f"❌ 최신 스냅샷 조회 실패")
        return False

    # 4. MarketSnapshot 수정
    print("\n3.4) 스냅샷 수정...")
    update_data = {
        'market_sentiment': 'neutral',
        'momentum_score': 68
    }
    updated_snapshot = db.update_market_snapshot(date.today().isoformat(), update_data)
    if updated_snapshot:
        # 별도 조회로 수정된 값 확인
        verified_snapshot = db.get_market_snapshot(date.today().isoformat())
        print(f"✅ 스냅샷 수정 성공")
        print(f"   - 시장 심리: {verified_snapshot.market_sentiment}")
        print(f"   - 모멘텀: {verified_snapshot.momentum_score}")
    else:
        print(f"❌ 스냅샷 수정 실패")
        return False

    # 5. 기간별 조회
    print("\n3.5) 기간별 스냅샷 조회...")
    start_date = (date.today() - timedelta(days=5)).isoformat()
    end_date = date.today().isoformat()
    range_snapshots = db.get_market_snapshots_range(start_date, end_date)
    print(f"✅ 기간 조회: {len(range_snapshots)}개 스냅샷")

    return True


def main():
    """메인 테스트 함수"""
    print("\n🧪 Phase 1: 데이터베이스 스키마 확장 테스트 시작\n")

    try:
        # 1. 테이블 생성
        db = test_table_creation()

        # 2. TradingSignal 테스트
        signal_result = test_trading_signal_crud(db)

        # 3. MarketSnapshot 테스트
        snapshot_result = test_market_snapshot_crud(db)

        # 최종 결과
        print("\n" + "=" * 70)
        print("📊 Phase 1 최종 테스트 결과")
        print("=" * 70)
        print(f"✅ 테이블 생성: 성공")
        print(f"{'✅' if signal_result else '❌'} TradingSignal CRUD: {'성공' if signal_result else '실패'}")
        print(f"{'✅' if snapshot_result else '❌'} MarketSnapshot CRUD: {'성공' if snapshot_result else '실패'}")

        if signal_result and snapshot_result:
            print("\n🎉 Phase 1 완료! 모든 테스트 통과 ✅")
            return True
        else:
            print("\n❌ Phase 1 테스트 실패")
            return False

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
