from backtest_platform import BacktestEngine
from strategy_example import (
    simple_moving_average_strategy,
    rsi_strategy, 
    bollinger_bands_strategy,
    run_strategy_backtest,
    compare_strategies
)

def main():
    """主函數：展示如何使用內建策略"""
    
    print("="*60)
    print("虛擬貨幣回測平台 - 內建策略示例")
    print("="*60)
    
    # 數據文件路徑
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    
    print(f"使用數據文件: {data_file}")
    print("\n可用的內建策略:")
    print("1. 移動平均線策略 (MA Strategy)")
    print("2. RSI策略 (RSI Strategy)")
    print("3. 布林帶策略 (Bollinger Bands Strategy)")
    
    # 選擇策略
    print("\n" + "-"*40)
    print("選擇要測試的策略:")
    print("1. 測試單一策略")
    print("2. 比較所有策略")
    print("3. 退出")
    
    choice = input("請輸入選擇 (1-3): ").strip()
    
    if choice == "1":
        # 單一策略測試
        print("\n選擇策略:")
        print("1. 移動平均線策略")
        print("2. RSI策略")
        print("3. 布林帶策略")
        
        strategy_choice = input("請輸入策略編號 (1-3): ").strip()
        
        if strategy_choice == "1":
            print("\n正在測試移動平均線策略...")
            # 可以自定義參數
            params = {"short_window": 10, "long_window": 30}
            backtest, performance = run_strategy_backtest(data_file, simple_moving_average_strategy, params)
            
        elif strategy_choice == "2":
            print("\n正在測試RSI策略...")
            params = {"rsi_period": 14, "oversold": 30, "overbought": 70}
            backtest, performance = run_strategy_backtest(data_file, rsi_strategy, params)
            
        elif strategy_choice == "3":
            print("\n正在測試布林帶策略...")
            params = {"window": 20, "num_std": 2}
            backtest, performance = run_strategy_backtest(data_file, bollinger_bands_strategy, params)
            
        else:
            print("無效的選擇")
            
    elif choice == "2":
        # 比較所有策略
        print("\n正在比較所有策略...")
        compare_strategies(data_file)
        
    elif choice == "3":
        print("退出程序")
        return
        
    else:
        print("無效的選擇")

def quick_test():
    """快速測試所有策略"""
    print("快速測試所有內建策略...")
    
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    
    # 測試移動平均線策略
    print("\n" + "="*50)
    print("測試移動平均線策略")
    print("="*50)
    try:
        backtest, performance = run_strategy_backtest(
            data_file, 
            simple_moving_average_strategy, 
            {"short_window": 10, "long_window": 30}
        )
    except Exception as e:
        print(f"移動平均線策略執行失敗: {e}")
    
    # 測試RSI策略
    print("\n" + "="*50)
    print("測試RSI策略")
    print("="*50)
    try:
        backtest, performance = run_strategy_backtest(
            data_file, 
            rsi_strategy, 
            {"rsi_period": 14, "oversold": 30, "overbought": 70}
        )
    except Exception as e:
        print(f"RSI策略執行失敗: {e}")
    
    # 測試布林帶策略
    print("\n" + "="*50)
    print("測試布林帶策略")
    print("="*50)
    try:
        backtest, performance = run_strategy_backtest(
            data_file, 
            bollinger_bands_strategy, 
            {"window": 20, "num_std": 2}
        )
    except Exception as e:
        print(f"布林帶策略執行失敗: {e}")

if __name__ == "__main__":
    # 直接運行快速測試
    quick_test()
    
    # 如果想要互動式選擇，可以取消註釋下面的行
    # main()
