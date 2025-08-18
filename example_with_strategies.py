from backtest_platform import BacktestEngine
from strategy_example import (
    simple_moving_average_strategy,
    rsi_strategy,
    bollinger_bands_strategy,
    buy_and_hold_strategy,
)
import random


def reduce_trading_frequency(signals, target_trades=1000):
    """隨機將非零信號歸零，將非零次數控制到 target_trades 左右"""
    non_zero_indices = [i for i, s in enumerate(signals) if s != 0]
    if len(non_zero_indices) <= target_trades:
        return signals
    # 固定隨機性（需要時可註解掉）
    random.seed(42)
    keep_indices = set(random.sample(non_zero_indices, target_trades))
    reduced = [s if (i in keep_indices or s == 0) else 0 for i, s in enumerate(signals)]
    return reduced


def run_strategy_backtest_reduced(data_file, strategy_func, strategy_params=None, target_trades=1000):
    """載入數據 → 產生信號 → 降頻 → 回測"""
    backtest = BacktestEngine(initial_capital=10000, commission_rate=0.001, symbol='BTCUSDT')
    if not backtest.load_data(data_file):
        print("數據載入失敗")
        return None, None

    signals = strategy_func(backtest.data, **strategy_params) if strategy_params else strategy_func(backtest.data)
    reduced_signals = reduce_trading_frequency(signals, target_trades)

    print(f"原始非零信號: {sum(1 for s in signals if s!=0)} → 降頻後非零信號: {sum(1 for s in reduced_signals if s!=0)}")

    performance = backtest.run_backtest(reduced_signals)
    backtest.print_summary()
    # 如不需圖，可註解下一行
    backtest.plot_results()
    return backtest, performance

def main():
    """主函數：展示如何使用內建策略"""
    
    print("="*60)
    print("虛擬貨幣回測平台 - 內建策略示例")
    print("="*60)
    
    # 數據文件路徑
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    
    print(f"使用數據文件: {data_file}")
    print("\n可用的內建策略:")
    print("1. 移動平均線策略 (MA)")
    print("2. RSI策略 (RSI)")
    print("3. 布林帶策略 (Bollinger)")
    print("4. 買入並持有 (Buy & Hold)")
    
    # 選擇策略
    print("\n" + "-"*40)
    print("選擇要測試的策略:")
    print("1. 測試單一策略（降頻至約1000筆）")
    print("2. 比較所有策略（降頻至約1000筆）")
    print("3. 退出")
    
    choice = input("請輸入選擇 (1-3): ").strip()
    
    if choice == "1":
        # 單一策略測試
        print("\n選擇策略:")
        print("1. 移動平均線策略")
        print("2. RSI策略")
        print("3. 布林帶策略")
        print("4. 買入並持有")
        
        strategy_choice = input("請輸入策略編號 (1-3): ").strip()
        
        if strategy_choice == "1":
            print("\n正在測試移動平均線策略（降頻）...")
            params = {"short_window": 10, "long_window": 30}
            run_strategy_backtest_reduced(data_file, simple_moving_average_strategy, params, target_trades=1000)

        elif strategy_choice == "2":
            print("\n正在測試RSI策略（降頻）...")
            params = {"rsi_period": 14, "oversold": 30, "overbought": 70}
            run_strategy_backtest_reduced(data_file, rsi_strategy, params, target_trades=1000)

        elif strategy_choice == "3":
            print("\n正在測試布林帶策略（降頻）...")
            params = {"window": 20, "num_std": 2}
            run_strategy_backtest_reduced(data_file, bollinger_bands_strategy, params, target_trades=1000)

        elif strategy_choice == "4":
            print("\n正在測試買入並持有（降頻；實際僅2筆非零信號）...")
            run_strategy_backtest_reduced(data_file, buy_and_hold_strategy, None, target_trades=1000)
            
        else:
            print("無效的選擇")
            
    elif choice == "2":
        # 比較所有策略
        print("\n正在比較所有策略（統一降頻至約1000筆）...")
        strategies = [
            ("MA", simple_moving_average_strategy, {"short_window": 10, "long_window": 30}),
            ("RSI", rsi_strategy, {"rsi_period": 14, "oversold": 30, "overbought": 70}),
            ("Bollinger", bollinger_bands_strategy, {"window": 20, "num_std": 2}),
            ("Buy&Hold", buy_and_hold_strategy, None),
        ]

        for name, fn, params in strategies:
            print("\n" + "-"*40)
            print(f"策略: {name}")
            run_strategy_backtest_reduced(data_file, fn, params, target_trades=1000)
        
    elif choice == "3":
        print("退出程序")
        return
        
    else:
        print("無效的選擇")

def quick_test():
    """快速測試所有策略"""
    print("快速測試所有內建策略...")
    
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    
    tests = [
        ("移動平均線（降頻）", simple_moving_average_strategy, {"short_window": 10, "long_window": 30}),
        ("RSI（降頻）", rsi_strategy, {"rsi_period": 14, "oversold": 30, "overbought": 70}),
        ("布林帶（降頻）", bollinger_bands_strategy, {"window": 20, "num_std": 2}),
        ("買入並持有（降頻）", buy_and_hold_strategy, None),
    ]

    for title, fn, params in tests:
        print("\n" + "="*50)
        print(f"測試{title}")
        print("="*50)
        try:
            run_strategy_backtest_reduced(data_file, fn, params, target_trades=1000)
        except Exception as e:
            print(f"{title} 執行失敗: {e}")

if __name__ == "__main__":
    # 直接運行快速測試
    quick_test()
    
    # 如果想要互動式選擇，可以取消註釋下面的行
    # main()
