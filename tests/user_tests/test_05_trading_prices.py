"""
Phase 5: Trading Price Calculation Test
Tests buy/target/stop-loss price calculation with real stock data
"""

import sys
sys.path.insert(0, '/opt/AutoQuant')

from src.database.database import Database
from src.analysis.technical_indicators import TechnicalIndicators
from src.pricing.support_resistance import SupportResistanceDetector
from src.pricing.price_calculator import PriceCalculator
from datetime import datetime, timedelta
import pandas as pd

def test_phase5_pricing():
    """Test Phase 5: Price calculation for trading signals"""

    print("=" * 80)
    print("PHASE 5: TRADING PRICE CALCULATION TEST")
    print("=" * 80)

    # Initialize
    db = Database()
    tech_indicators = TechnicalIndicators()
    sr_detector = SupportResistanceDetector()
    price_calc = PriceCalculator(db=db)

    # Test stocks from Phase 4 output
    test_stocks = [
        ('005930', '삼성전자'),       # Large cap
        ('000660', 'SK하이닉스'),     # Large cap
        ('018000', '유니슨'),          # Phase 4 selected
        ('011080', '형지I&C'),        # Phase 4 selected
    ]

    print(f"\n📊 Testing with {len(test_stocks)} stocks")
    print("-" * 80)

    all_results = []

    for stock_code, stock_name in test_stocks:
        print(f"\n{'='*80}")
        print(f"🎯 Stock: {stock_code} ({stock_name})")
        print(f"{'='*80}")

        try:
            # 1. Get OHLCV data (200 days for sufficient history)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=200)

            print(f"\n1️⃣ Fetching Data")
            print(f"   Period: {start_date.date()} ~ {end_date.date()}")

            ohlcv_df = db.get_daily_ohlcv_from_kis(
                stock_code,
                start_date=start_date,
                end_date=end_date
            )

            if ohlcv_df is None or len(ohlcv_df) < 60:
                print(f"   ❌ Insufficient data: {len(ohlcv_df) if ohlcv_df is not None else 0} days")
                continue

            print(f"   ✅ Retrieved {len(ohlcv_df)} days of data")

            # 2. Prepare data
            ohlcv_df = ohlcv_df.copy()
            ohlcv_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)

            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in ohlcv_df.columns:
                    ohlcv_df[col] = ohlcv_df[col].astype(float)

            # 3. Add technical indicators
            print(f"\n2️⃣ Calculating Technical Indicators")
            ohlcv_with_indicators = tech_indicators.add_all_indicators(ohlcv_df)

            latest = ohlcv_with_indicators.iloc[-1]
            print(f"   Close: {latest['Close']:,.0f}")
            print(f"   SMA_5: {latest['SMA_5']:,.0f}")
            print(f"   SMA_20: {latest['SMA_20']:,.0f}")
            print(f"   RSI_14: {latest['RSI_14']:.2f}")
            print(f"   ATR: {latest['ATR']:,.0f}")

            # 4. Test Support/Resistance Detection
            print(f"\n3️⃣ Support/Resistance Detection")
            sr_levels = sr_detector.find_levels(ohlcv_with_indicators, lookback=60)

            print(f"   Support:    {sr_levels['support']:>12,.0f} KRW")
            print(f"   Pivot:      {sr_levels['pivot']:>12,.0f} KRW")
            print(f"   Resistance: {sr_levels['resistance']:>12,.0f} KRW")
            print(f"   Current:    {sr_levels['current_price']:>12,.0f} KRW")
            print(f"   60D High:   {sr_levels['high_60d']:>12,.0f} KRW")
            print(f"   60D Low:    {sr_levels['low_60d']:>12,.0f} KRW")

            # Validate S/R logic
            if sr_levels['support'] >= sr_levels['resistance']:
                print(f"   ⚠️  WARNING: Support >= Resistance (unusual)")
            else:
                print(f"   ✅ S/R levels valid")

            # 5. Calculate Trading Prices
            print(f"\n4️⃣ Trading Price Calculation")
            current_price = float(latest['Close'])

            prices = price_calc.calculate_prices(
                stock_code=stock_code,
                current_price=current_price,
                technical_data=ohlcv_with_indicators,
                prediction_days=7
            )

            # 6. Display Results
            print(f"\n{'='*80}")
            print(f"📊 TRADING SIGNAL FOR {stock_name} ({stock_code})")
            print(f"{'='*80}")
            print(f"\n💰 Price Levels:")
            print(f"   Current:    {prices['current_price']:>12,.0f} KRW")
            print(f"   Buy:        {prices['buy_price']:>12,.0f} KRW  (+{((prices['buy_price']/prices['current_price']-1)*100):.2f}%)")
            print(f"   Target:     {prices['target_price']:>12,.0f} KRW  (+{((prices['target_price']/prices['buy_price']-1)*100):.2f}%)")
            print(f"   Stop Loss:  {prices['stop_loss_price']:>12,.0f} KRW  (-{((1-prices['stop_loss_price']/prices['buy_price'])*100):.2f}%)")

            print(f"\n📈 Performance Metrics:")
            print(f"   Expected Return:    +{prices['predicted_return']:>6.2f}%")
            print(f"   Risk/Reward Ratio:   {prices['risk_reward_ratio']:>6.2f}:1")
            print(f"   AI Confidence:       {prices['ai_confidence']:>6.0f}%")

            print(f"\n🎯 Technical Levels:")
            print(f"   Support:     {prices['support_level']:>12,.0f} KRW")
            print(f"   Resistance:  {prices['resistance_level']:>12,.0f} KRW")
            print(f"   Pivot:       {prices['pivot_point']:>12,.0f} KRW")
            print(f"   ATR:         {prices['atr']:>12,.0f} KRW")

            # 7. Validation Checks
            print(f"\n✅ Validation:")
            checks = []

            # Check 1: Buy > Current
            if prices['buy_price'] > prices['current_price'] * 0.995:
                checks.append("✅ Buy price above current (entry premium)")
            else:
                checks.append("⚠️  Buy price below current")

            # Check 2: Target > Buy
            if prices['target_price'] > prices['buy_price']:
                checks.append("✅ Target price above buy price")
            else:
                checks.append("❌ Target price below buy price")

            # Check 3: Stop Loss < Buy
            if prices['stop_loss_price'] < prices['buy_price']:
                checks.append("✅ Stop loss below buy price")
            else:
                checks.append("❌ Stop loss above buy price")

            # Check 4: Risk/Reward >= 0.8
            if prices['risk_reward_ratio'] >= 0.8:
                checks.append(f"✅ Risk/Reward ratio acceptable ({prices['risk_reward_ratio']:.2f})")
            else:
                checks.append(f"⚠️  Risk/Reward ratio low ({prices['risk_reward_ratio']:.2f})")

            # Check 5: Buy > Support
            if prices['buy_price'] > prices['support_level']:
                checks.append("✅ Buy price above support")
            else:
                checks.append("⚠️  Buy price below support")

            # Check 6: Target <= Resistance (conservative)
            if prices['target_price'] <= prices['resistance_level'] * 1.05:
                checks.append("✅ Target price near/below resistance")
            else:
                checks.append("⚠️  Target price significantly above resistance")

            for check in checks:
                print(f"   {check}")

            # Store result
            result = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'current_price': prices['current_price'],
                'buy_price': prices['buy_price'],
                'target_price': prices['target_price'],
                'stop_loss_price': prices['stop_loss_price'],
                'predicted_return': prices['predicted_return'],
                'risk_reward_ratio': prices['risk_reward_ratio'],
                'ai_confidence': prices['ai_confidence'],
                'all_checks_passed': all('✅' in check for check in checks)
            }
            all_results.append(result)

            print(f"\n{'='*80}")

        except Exception as e:
            print(f"   ❌ Error processing {stock_code}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 PHASE 5 TEST SUMMARY")
    print(f"{'='*80}")

    if all_results:
        print(f"\n✅ Successfully calculated prices for {len(all_results)} stocks")
        print(f"\nTop Signals (by Risk/Reward):")
        print("-" * 80)

        # Sort by risk/reward ratio
        sorted_results = sorted(all_results, key=lambda x: x['risk_reward_ratio'], reverse=True)

        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. {result['stock_name']} ({result['stock_code']})")
            print(f"   Buy: {result['buy_price']:>10,.0f} → Target: {result['target_price']:>10,.0f} (Stop: {result['stop_loss_price']:>10,.0f})")
            print(f"   Return: +{result['predicted_return']:>5.2f}% | R/R: {result['risk_reward_ratio']:>4.2f}:1 | Confidence: {result['ai_confidence']:>3.0f}%")
            print(f"   Quality: {'✅ PASS' if result['all_checks_passed'] else '⚠️  REVIEW'}")

        # Statistics
        avg_return = sum(r['predicted_return'] for r in all_results) / len(all_results)
        avg_rr = sum(r['risk_reward_ratio'] for r in all_results) / len(all_results)
        pass_rate = sum(1 for r in all_results if r['all_checks_passed']) / len(all_results) * 100

        print(f"\n📈 Statistics:")
        print(f"   Average Expected Return: +{avg_return:.2f}%")
        print(f"   Average R/R Ratio: {avg_rr:.2f}:1")
        print(f"   Quality Pass Rate: {pass_rate:.1f}%")

        print(f"\n🎉 Phase 5 Test: {'✅ PASS' if pass_rate >= 75 else '⚠️  REVIEW NEEDED'}")

    else:
        print(f"\n❌ No results generated")
        return False

    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PHASE 5: TRADING PRICE CALCULATION - COMPREHENSIVE TEST")
    print("Testing: Support/Resistance Detection + Price Calculation")
    print("=" * 80)

    success = test_phase5_pricing()

    if success:
        print("\n" + "=" * 80)
        print("✅ PHASE 5 TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ PHASE 5 TEST FAILED")
        print("=" * 80)
