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

def test_signal_conversion():
    """測試信號轉換的影響"""
    
    print("="*60)
    print("測試信號轉換：從離散信號(1,0,-1)到部分信號(0.1,0,-0.1)")
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
    
    # 減少交易頻率
    print("\n減少交易頻率...")
    reduced_signals = reduce_trading_frequency(original_signals, target_trades=1000)
    
    print(f"減少頻率後信號統計:")
    print(f"  買入信號(1): {reduced_signals.count(1)}")
    print(f"  賣出信號(-1): {reduced_signals.count(-1)}")
    print(f"  不動作(0): {reduced_signals.count(0)}")
    
    # 生成轉換後的信號 (0.1, 0, -0.1)
    print("\n生成轉換後的部分信號...")
    partial_signals = []
    for signal in reduced_signals:
        if signal == 1:
            partial_signals.append(0.1)  # 買入10%倉位
        elif signal == -1:
            partial_signals.append(-0.1)  # 賣出10%倉位
        else:
            partial_signals.append(0)
    
    print(f"轉換後信號統計:")
    print(f"  買入信號(0.1): {partial_signals.count(0.1)}")
    print(f"  賣出信號(-0.1): {partial_signals.count(-0.1)}")
    print(f"  不動作(0): {partial_signals.count(0)}")
    
    # 測試減少頻率後的原始信號
    print("\n" + "="*50)
    print("測試減少頻率後的離散信號 (1, 0, -1)")
    print("="*50)
    try:
        performance_reduced = backtest.run_backtest(reduced_signals)
        backtest.print_summary()
    except Exception as e:
        print(f"減少頻率後信號回測失敗: {e}")
    
    # 注意：原始回測引擎不支持小數信號，會報錯
    print("\n" + "="*50)
    print("測試轉換後的部分信號 (0.1, 0, -0.1)")
    print("="*50)
    print("注意：原始回測引擎不支持小數信號，會報錯")
    
    try:
        performance_partial = backtest.run_backtest(partial_signals)
        backtest.print_summary()
    except Exception as e:
        print(f"部分信號回測失敗: {e}")
        print("\n這證明了原始回測引擎需要修改才能支持部分倉位策略")

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
    
    for target_trades in frequencies:
        print(f"\n" + "="*40)
        print(f"測試目標交易次數: {target_trades}")
        print("="*40)
        
        # 減少交易頻率
        reduced_signals = reduce_trading_frequency(base_signals, target_trades)
        
        # 執行回測
        try:
            performance = backtest.run_backtest(reduced_signals)
            print(f"最終資金: ${performance['final_capital']:,.2f}")
            print(f"總收益率: {performance['total_return']:.2%}")
            print(f"最大回撤: {performance['max_drawdown']:.2%}")
            print(f"實際交易次數: {performance['total_trades']}")
        except Exception as e:
            print(f"回測失敗: {e}")

def analyze_signal_differences():
    """分析兩種信號的差異"""
    
    print("\n" + "="*60)
    print("信號差異分析")
    print("="*60)
    
    print("1. 原始信號 (1, 0, -1):")
    print("   - 1: 買入全倉")
    print("   - 0: 不動作")
    print("   - -1: 賣出全倉")
    print("   - 特點：激進，每次交易都是全倉操作")
    
    print("\n2. 轉換後信號 (0.1, 0, -0.1):")
    print("   - 0.1: 買入10%倉位")
    print("   - 0: 不動作")
    print("   - -0.1: 賣出10%倉位")
    print("   - 特點：保守，每次交易只調整部分倉位")
    
    print("\n3. 主要差異:")
    print("   - 風險控制：部分倉位策略風險更低")
    print("   - 靈活性：可以逐步建倉和減倉")
    print("   - 交易頻率：可能需要更多交易來達到相同效果")
    print("   - 手續費：更多交易意味著更多手續費")
    
    print("\n4. 適用場景:")
    print("   - 原始信號：適合趨勢明確的市場")
    print("   - 部分信號：適合震盪市場和風險厭惡型投資者")
    
    print("\n5. 交易頻率控制的重要性:")
    print("   - 過高頻率：手續費累積，回撤嚴重")
    print("   - 適中頻率：平衡收益和風險")
    print("   - 過低頻率：可能錯失機會")

if __name__ == "__main__":
    # 設置隨機種子以確保結果可重現
    random.seed(42)
    
    # 測試信號轉換
    test_signal_conversion()
    
    # 測試不同交易頻率
    test_different_frequencies()
    
    # 分析信號差異
    analyze_signal_differences()
