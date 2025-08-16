import pandas as pd
import numpy as np
from backtest_platform import BacktestEngine

def simple_moving_average_strategy(data: pd.DataFrame, short_window: int = 10, long_window: int = 30) -> list:
    """
    簡單移動平均線策略
    
    Args:
        data: K線數據
        short_window: 短期移動平均線週期
        long_window: 長期移動平均線週期
    
    Returns:
        signals: 信號列表，1=買入，0=不動作，-1=賣出
    """
    signals = []
    
    # 計算移動平均線
    short_ma = data['Close'].rolling(window=short_window).mean()
    long_ma = data['Close'].rolling(window=long_window).mean()
    
    for i in range(len(data)):
        if i < long_window:
            signals.append(0)  # 數據不足，不動作
        else:
            # 金叉：短期MA上穿長期MA
            if short_ma.iloc[i] > long_ma.iloc[i] and short_ma.iloc[i-1] <= long_ma.iloc[i-1]:
                signals.append(1)  # 買入信號
            # 死叉：短期MA下穿長期MA
            elif short_ma.iloc[i] < long_ma.iloc[i] and short_ma.iloc[i-1] >= long_ma.iloc[i-1]:
                signals.append(-1)  # 賣出信號
            else:
                signals.append(0)  # 不動作
    
    return signals

def rsi_strategy(data: pd.DataFrame, rsi_period: int = 14, oversold: float = 30, overbought: float = 70) -> list:
    """
    RSI策略
    
    Args:
        data: K線數據
        rsi_period: RSI計算週期
        oversold: 超賣閾值
        overbought: 超買閾值
    
    Returns:
        signals: 信號列表
    """
    signals = []
    
    # 計算RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    for i in range(len(data)):
        if i < rsi_period:
            signals.append(0)
        else:
            current_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1] if i > 0 else 50
            
            # RSI從超賣區回升
            if prev_rsi < oversold and current_rsi >= oversold:
                signals.append(1)  # 買入信號
            # RSI從超買區回落
            elif prev_rsi > overbought and current_rsi <= overbought:
                signals.append(-1)  # 賣出信號
            else:
                signals.append(0)
    
    return signals

def bollinger_bands_strategy(data: pd.DataFrame, window: int = 20, num_std: float = 2) -> list:
    """
    布林帶策略
    
    Args:
        data: K線數據
        window: 移動平均線週期
        num_std: 標準差倍數
    
    Returns:
        signals: 信號列表
    """
    signals = []
    
    # 計算布林帶
    ma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper_band = ma + (std * num_std)
    lower_band = ma - (std * num_std)
    
    for i in range(len(data)):
        if i < window:
            signals.append(0)
        else:
            current_price = data['Close'].iloc[i]
            current_upper = upper_band.iloc[i]
            current_lower = lower_band.iloc[i]
            
            # 價格觸及下軌，可能反彈
            if current_price <= current_lower:
                signals.append(1)  # 買入信號
            # 價格觸及上軌，可能回落
            elif current_price >= current_upper:
                signals.append(-1)  # 賣出信號
            else:
                signals.append(0)
    
    return signals

def run_strategy_backtest(data_file: str, strategy_func, strategy_params: dict = None):
    """
    運行策略回測
    
    Args:
        data_file: 數據文件路徑
        strategy_func: 策略函數
        strategy_params: 策略參數
    """
    # 創建回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,  # 初始資金 $10,000
        commission_rate=0.001,  # 手續費 0.1%
        symbol='BTCUSDT'
    )
    
    # 載入數據
    if not backtest.load_data(data_file):
        print("數據載入失敗")
        return
    
    # 生成信號
    if strategy_params:
        signals = strategy_func(backtest.data, **strategy_params)
    else:
        signals = strategy_func(backtest.data)
    
    print(f"生成信號數量: {len(signals)}")
    print(f"買入信號: {signals.count(1)}")
    print(f"賣出信號: {signals.count(-1)}")
    print(f"不動作: {signals.count(0)}")
    
    # 執行回測
    performance = backtest.run_backtest(signals)
    
    # 顯示結果
    backtest.print_summary()
    
    # 繪製圖表
    backtest.plot_results()
    
    return backtest, performance

def compare_strategies(data_file: str):
    """比較不同策略的表現"""
    strategies = {
        "移動平均線策略": (simple_moving_average_strategy, {"short_window": 10, "long_window": 30}),
        "RSI策略": (rsi_strategy, {"rsi_period": 14, "oversold": 30, "overbought": 70}),
        "布林帶策略": (bollinger_bands_strategy, {"window": 20, "num_std": 2})
    }
    
    results = {}
    
    for strategy_name, (strategy_func, params) in strategies.items():
        print(f"\n正在測試 {strategy_name}...")
        try:
            backtest, performance = run_strategy_backtest(data_file, strategy_func, params)
            results[strategy_name] = performance
        except Exception as e:
            print(f"{strategy_name} 執行失敗: {e}")
            results[strategy_name] = None
    
    # 比較結果
    print("\n" + "="*80)
    print("策略比較結果")
    print("="*80)
    
    comparison_data = []
    for strategy_name, performance in results.items():
        if performance:
            comparison_data.append({
                '策略名稱': strategy_name,
                '總收益率': f"{performance['total_return']:.2%}",
                '年化收益率': f"{performance['annual_return']:.2%}",
                '夏普比率': f"{performance['sharpe_ratio']:.3f}",
                '最大回撤': f"{performance['max_drawdown']:.2%}",
                '勝率': f"{performance['win_rate']:.2%}",
                '交易次數': performance['total_trades']
            })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
    else:
        print("沒有成功的策略回測結果")

if __name__ == "__main__":
    # 示例使用
    print("策略示例文件已創建完成！")
    print("\n可用的策略函數：")
    print("1. simple_moving_average_strategy() - 移動平均線策略")
    print("2. rsi_strategy() - RSI策略")
    print("3. bollinger_bands_strategy() - 布林帶策略")
    print("\n使用方法：")
    print("1. 單一策略回測：run_strategy_backtest(data_file, strategy_func, params)")
    print("2. 策略比較：compare_strategies(data_file)")
    
    # 如果有數據文件，可以取消註釋下面的代碼來測試
    # data_file = "btcusdt_1m.csv"
    # compare_strategies(data_file)
