from backtest_platform import BacktestEngine
import numpy as np
import random

def reduce_trading_frequency(signals, target_trades=1000):
    """
    隨機將信號歸零，控制交易次數
    
    Args:
        signals: 原始信號列表
        target_trades: 目標交易次數
    
    Returns:
        處理後的信號列表
    """
    # 計算當前非零信號數量
    non_zero_count = sum(1 for s in signals if s != 0)
    print(f"原始非零信號數量: {non_zero_count}")
    
    if non_zero_count <= target_trades:
        print(f"信號數量已經小於等於目標數量，無需處理")
        return signals
    
    # 計算需要歸零的信號數量
    signals_to_zero = non_zero_count - target_trades
    print(f"需要隨機歸零的信號數量: {signals_to_zero}")
    
    # 獲取所有非零信號的索引
    non_zero_indices = [i for i, s in enumerate(signals) if s != 0]
    
    # 隨機選擇要歸零的索引
    indices_to_zero = random.sample(non_zero_indices, signals_to_zero)
    
    # 創建新的信號列表
    new_signals = signals.copy()
    for idx in indices_to_zero:
        new_signals[idx] = 0
    
    # 驗證結果
    final_non_zero = sum(1 for s in new_signals if s != 0)
    print(f"處理後非零信號數量: {final_non_zero}")
    print(f"預期交易次數: {final_non_zero}")
    
    return new_signals

def test_reduced_frequency():
    """測試減少交易頻率的效果"""
    
    print("="*60)
    print("測試減少交易頻率：控制交易次數在1000左右")
    print("="*60)
    
    # 創建回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,
        commission_rate=0.001,
        symbol='BTCUSDT'
    )
    
    # 載入數據
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    if not backtest.load_data(data_file):
        print("數據載入失敗")
        return
    
    # 生成原始信號 (1, 0, -1)
    print("\n生成原始離散信號...")
    original_signals = []
    for i in range(len(backtest.data)):
        if i % 3 == 0:
            original_signals.append(1)
        elif i % 5 == 0:
            original_signals.append(-1)
        else:
            original_signals.append(0)
    
    print(f"原始信號統計:")
    print(f"  買入信號(1): {original_signals.count(1)}")
    print(f"  賣出信號(-1): {original_signals.count(-1)}")
    print(f"  不動作(0): {original_signals.count(0)}")
    
    # 測試原始信號（高頻率）
    print("\n" + "="*50)
    print("測試原始高頻信號")
    print("="*50)
    try:
        performance_original = backtest.run_backtest(original_signals)
        print(f"原始信號結果:")
        print(f"  最終資金: ${performance_original['final_capital']:,.2f}")
        print(f"  總收益率: {performance_original['total_return']:.2%}")
        print(f"  最大回撤: {performance_original['max_drawdown']:.2%}")
        print(f"  交易次數: {performance_original['total_trades']}")
    except Exception as e:
        print(f"原始信號回測失敗: {e}")
    
    # 減少交易頻率
    print("\n減少交易頻率...")
    reduced_signals = reduce_trading_frequency(original_signals, target_trades=1000)
    
    print(f"減少頻率後信號統計:")
    print(f"  買入信號(1): {reduced_signals.count(1)}")
    print(f"  賣出信號(-1): {reduced_signals.count(-1)}")
    print(f"  不動作(0): {reduced_signals.count(0)}")
    
    # 測試減少頻率後的信號
    print("\n" + "="*50)
    print("測試減少頻率後的信號")
    print("="*50)
    try:
        performance_reduced = backtest.run_backtest(reduced_signals)
        print(f"減少頻率後結果:")
        print(f"  最終資金: ${performance_reduced['final_capital']:,.2f}")
        print(f"  總收益率: {performance_reduced['total_return']:.2%}")
        print(f"  最大回撤: {performance_reduced['max_drawdown']:.2%}")
        print(f"  交易次數: {performance_reduced['total_trades']}")
    except Exception as e:
        print(f"減少頻率後信號回測失敗: {e}")

def test_different_frequencies():
    """測試不同的交易頻率"""
    
    print("\n" + "="*60)
    print("測試不同交易頻率的效果")
    print("="*60)
    
    # 創建回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,
        commission_rate=0.001,
        symbol='BTCUSDT'
    )
    
    # 載入數據
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    if not backtest.load_data(data_file):
        print("數據載入失敗")
        return
    
    # 生成基礎信號
    base_signals = []
    for i in range(len(backtest.data)):
        if i % 3 == 0:
            base_signals.append(1)
        elif i % 5 == 0:
            base_signals.append(-1)
        else:
            base_signals.append(0)
    
    # 測試不同的交易頻率
    frequencies = [100, 500, 1000, 2000, 5000]
    
    results = []
    
    for target_trades in frequencies:
        print(f"\n" + "="*40)
        print(f"測試目標交易次數: {target_trades}")
        print("="*40)
        
        # 減少交易頻率
        reduced_signals = reduce_trading_frequency(base_signals, target_trades)
        
        # 執行回測
        try:
            performance = backtest.run_backtest(reduced_signals)
            result = {
                'target_trades': target_trades,
                'actual_trades': performance['total_trades'],
                'final_capital': performance['final_capital'],
                'total_return': performance['total_return'],
                'max_drawdown': performance['max_drawdown'],
                'sharpe_ratio': performance['sharpe_ratio']
            }
            results.append(result)
            
            print(f"結果:")
            print(f"  最終資金: ${performance['final_capital']:,.2f}")
            print(f"  總收益率: {performance['total_return']:.2%}")
            print(f"  最大回撤: {performance['max_drawdown']:.2%}")
            print(f"  夏普比率: {performance['sharpe_ratio']:.3f}")
            print(f"  實際交易次數: {performance['total_trades']}")
            
        except Exception as e:
            print(f"回測失敗: {e}")
    
    # 總結結果
    print("\n" + "="*60)
    print("不同交易頻率結果總結")
    print("="*60)
    
    if results:
        print(f"{'目標交易次數':<12} {'實際交易次數':<12} {'最終資金':<12} {'收益率':<10} {'最大回撤':<10} {'夏普比率':<10}")
        print("-" * 80)
        for result in results:
            print(f"{result['target_trades']:<12} {result['actual_trades']:<12} "
                  f"${result['final_capital']:<11,.0f} {result['total_return']:<10.2%} "
                  f"{result['max_drawdown']:<10.2%} {result['sharpe_ratio']:<10.3f}")

if __name__ == "__main__":
    # 設置隨機種子以確保結果可重現
    random.seed(42)
    
    # 測試減少交易頻率
    test_reduced_frequency()
    
    # 測試不同交易頻率
    test_different_frequencies()
