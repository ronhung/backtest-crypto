#!/usr/bin/env python3
"""
回測平台測試腳本
用於驗證回測平台的基本功能
"""

import pandas as pd
import numpy as np
from backtest_platform import BacktestEngine
from strategy_example import simple_moving_average_strategy

def create_sample_data(n_points: int = 1000) -> pd.DataFrame:
    """創建示例數據用於測試"""
    print("創建示例數據...")
    
    # 生成時間序列
    start_time = pd.Timestamp('2024-01-01 00:00:00')
    timestamps = [start_time + pd.Timedelta(minutes=i) for i in range(n_points)]
    
    # 生成價格數據（模擬BTC價格走勢）
    np.random.seed(42)  # 固定隨機種子以確保可重現性
    
    # 基礎價格
    base_price = 50000
    prices = [base_price]
    
    # 生成價格序列（帶趨勢和波動）
    for i in range(1, n_points):
        # 添加趨勢和隨機波動
        trend = 0.0001 * i  # 輕微上升趨勢
        noise = np.random.normal(0, 0.01)  # 1%的隨機波動
        
        new_price = prices[-1] * (1 + trend + noise)
        prices.append(max(new_price, 1000))  # 確保價格不會低於1000
    
    # 創建DataFrame
    data = pd.DataFrame({
        'Open time': timestamps,
        'Close time': timestamps,
        'Open': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
        'High': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        'Close': prices,
        'Volume': [np.random.uniform(100, 1000) for _ in prices],
        'Quote asset volume': [np.random.uniform(1000000, 10000000) for _ in prices],
        'Number of trades': [np.random.randint(50, 500) for _ in prices],
        'Taker buy base volume': [np.random.uniform(50, 500) for _ in prices],
        'Taker buy quote volume': [np.random.uniform(500000, 5000000) for _ in prices],
        'Ignore': [0 for _ in prices]
    })
    
    # 確保High >= Low
    data['High'] = data[['High', 'Low']].max(axis=1)
    data['Low'] = data[['High', 'Low']].min(axis=1)
    
    print(f"創建了 {len(data)} 條示例數據")
    print(f"價格範圍: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
    
    return data

def test_basic_functionality():
    """測試基本功能"""
    print("\n" + "="*50)
    print("測試基本功能")
    print("="*50)
    
    # 創建示例數據
    sample_data = create_sample_data(500)  # 500個數據點
    
    # 保存示例數據
    sample_data.to_csv('sample_data.csv', index=False)
    print("示例數據已保存到 sample_data.csv")
    
    # 創建回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,
        commission_rate=0.001,
        symbol='BTCUSDT'
    )
    
    # 手動設置數據
    backtest.data = sample_data
    
    # 生成簡單的信號（每100個點買入，每100個點賣出）
    signals = []
    for i in range(len(sample_data)):
        if i % 100 == 0 and i > 0:
            signals.append(1)  # 買入
        elif i % 100 == 50 and i > 0:
            signals.append(-1)  # 賣出
        else:
            signals.append(0)  # 不動作
    
    print(f"生成信號: 買入={signals.count(1)}, 賣出={signals.count(-1)}, 不動作={signals.count(0)}")
    
    # 執行回測
    try:
        performance = backtest.run_backtest(signals)
        print("基本回測測試通過！")
        
        # 顯示結果
        backtest.print_summary()
        
        return True
        
    except Exception as e:
        print(f"基本回測測試失敗: {e}")
        return False

def test_strategy_integration():
    """測試策略整合"""
    print("\n" + "="*50)
    print("測試策略整合")
    print("="*50)
    
    try:
        # 載入示例數據
        data = pd.read_csv('sample_data.csv')
        data['Open time'] = pd.to_datetime(data['Open time'])
        data['Close time'] = pd.to_datetime(data['Close time'])
        
        # 測試移動平均線策略
        signals = simple_moving_average_strategy(data, short_window=10, long_window=30)
        
        print(f"移動平均線策略信號: 買入={signals.count(1)}, 賣出={signals.count(-1)}, 不動作={signals.count(0)}")
        
        # 創建回測引擎並執行
        backtest = BacktestEngine(
            initial_capital=10000,
            commission_rate=0.001,
            symbol='BTCUSDT'
        )
        backtest.data = data
        
        performance = backtest.run_backtest(signals)
        print("策略整合測試通過！")
        
        # 顯示結果
        backtest.print_summary()
        
        return True
        
    except Exception as e:
        print(f"策略整合測試失敗: {e}")
        return False

def test_performance_calculation():
    """測試績效計算"""
    print("\n" + "="*50)
    print("測試績效計算")
    print("="*50)
    
    try:
        # 創建一個簡單的權益曲線
        backtest = BacktestEngine()
        backtest.equity_curve = pd.Series([10000, 10100, 10200, 10150, 10300, 10250, 10400])
        
        performance = backtest.calculate_performance()
        
        print("績效計算結果:")
        for key, value in performance.items():
            if isinstance(value, float):
                if 'return' in key or 'drawdown' in key:
                    print(f"  {key}: {value:.2%}")
                elif 'ratio' in key:
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        print("績效計算測試通過！")
        return True
        
    except Exception as e:
        print(f"績效計算測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("開始運行回測平台測試...")
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("策略整合", test_strategy_integration),
        ("績效計算", test_performance_calculation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 測試通過")
            else:
                print(f"❌ {test_name} 測試失敗")
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
    
    print(f"\n測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！回測平台運行正常。")
    else:
        print("⚠️  部分測試失敗，請檢查相關功能。")

if __name__ == "__main__":
    run_all_tests()
