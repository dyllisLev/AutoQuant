"""
PostgreSQL DB 연결 테스트 및 KIS 데이터 조회 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.database import Database
from datetime import datetime, timedelta
import pandas as pd


def test_connection():
    """데이터베이스 연결 테스트"""
    print("=" * 60)
    print("🔌 데이터베이스 연결 테스트")
    print("=" * 60)

    try:
        db = Database()
        print("✅ PostgreSQL 연결 성공!")
        print(f"   연결 URL: {db.db_url}")

        # 테이블 생성
        print("\n📋 AutoQuant 테이블 생성 중...")
        db.create_tables()
        print("✅ 테이블 생성 완료")

        return db

    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None


def test_kis_data_access(db):
    """KIS 시스템의 데이터 조회 테스트"""
    print("\n" + "=" * 60)
    print("📊 KIS 시스템 데이터 조회 테스트")
    print("=" * 60)

    try:
        # 1. 사용 가능한 종목 목록 조회
        print("\n1️⃣ 사용 가능한 종목 목록 조회 중...")
        symbols_df = db.get_available_symbols_from_kis()

        if symbols_df.empty:
            print("⚠️ 조회할 종목이 없습니다.")
            print("   KIS 시스템에서 데이터를 먼저 수집해주세요.")
            return False

        print(f"✅ {len(symbols_df)}개 종목 발견")
        print("\n상위 10개 종목:")
        print(symbols_df.head(10).to_string())

        # 2. 첫 번째 종목의 일봉 데이터 조회
        if not symbols_df.empty:
            test_symbol = symbols_df.iloc[0]['symbol_code']
            print(f"\n2️⃣ 테스트 종목 데이터 조회: {test_symbol}")

            # 최근 100일 데이터 조회
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=100)

            ohlcv_df = db.get_daily_ohlcv_from_kis(test_symbol, start_date, end_date)

            if not ohlcv_df.empty:
                print(f"✅ {len(ohlcv_df)}개 일봉 데이터 조회 성공")
                print("\n최근 5개 일봉 데이터:")
                print(ohlcv_df.tail(5).to_string())

                # 3. 데이터 통계
                print(f"\n3️⃣ 데이터 통계")
                print(f"   종목: {test_symbol}")
                print(f"   기간: {ohlcv_df.index.min().date()} ~ {ohlcv_df.index.max().date()}")
                print(f"   종가 (현재): {ohlcv_df['close'].iloc[-1]:,.0f}원")
                print(f"   종가 (최고): {ohlcv_df['close'].max():,.0f}원")
                print(f"   종가 (최저): {ohlcv_df['close'].min():,.0f}원")
                print(f"   평균 거래량: {ohlcv_df['volume'].mean():,.0f}")

                return True
            else:
                print(f"⚠️ {test_symbol} 데이터 조회 실패")
                return False

    except Exception as e:
        print(f"❌ KIS 데이터 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_autoquant_tables(db):
    """AutoQuant 테이블 기본 동작 테스트"""
    print("\n" + "=" * 60)
    print("✨ AutoQuant 테이블 기본 동작 테스트")
    print("=" * 60)

    try:
        # 테스트 종목 추가
        print("\n1️⃣ 종목 추가 테스트...")
        stock = db.add_stock("005930", "삼성전자", "KOSPI", "전자")
        print(f"✅ 종목 추가 성공: {stock.ticker} - {stock.name}")

        # 종목 조회
        print("\n2️⃣ 종목 조회 테스트...")
        retrieved_stock = db.get_stock("005930")
        if retrieved_stock:
            print(f"✅ 종목 조회 성공: {retrieved_stock.ticker} - {retrieved_stock.name}")
        else:
            print("❌ 종목 조회 실패")

        # 전체 종목 조회
        print("\n3️⃣ 전체 종목 조회 테스트...")
        all_stocks = db.get_all_stocks()
        print(f"✅ 전체 종목: {len(all_stocks)}개")

        return True

    except Exception as e:
        print(f"❌ AutoQuant 테이블 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print("\n🧪 AutoQuant PostgreSQL 통합 테스트 시작\n")

    # 1. 연결 테스트
    db = test_connection()
    if not db:
        print("\n❌ 데이터베이스 연결 실패로 테스트 중단")
        return

    # 2. KIS 데이터 조회 테스트
    kis_result = test_kis_data_access(db)

    # 3. AutoQuant 테이블 테스트
    aq_result = test_autoquant_tables(db)

    # 최종 결과
    print("\n" + "=" * 60)
    print("📊 최종 테스트 결과")
    print("=" * 60)
    print(f"✅ 데이터베이스 연결: 성공")
    print(f"{'✅' if kis_result else '⚠️'} KIS 데이터 조회: {'성공' if kis_result else '주의'}")
    print(f"✅ AutoQuant 테이블: {'성공' if aq_result else '실패'}")
    print("\n💡 설정 정보:")
    print(f"   - DB_TYPE: postgresql")
    print(f"   - DB_HOST: ***REDACTED_HOST***")
    print(f"   - DB_NAME: postgres")
    print(f"   - 환경변수 파일: .env")
    print("=" * 60)


if __name__ == "__main__":
    main()
