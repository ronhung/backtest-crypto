from backtest_platform import BacktestEngine
from strategy_example import (
    simple_moving_average_strategy,
    rsi_strategy,
    partial_rsi_strategy,
    bollinger_bands_strategy,
    buy_and_hold_strategy
)
import pandas as pd
import numpy as np
from scipy.optimize import minimize_scalar
from brutal_search import brutal_search

def grid_trading_strategy(data: pd.DataFrame, x: float = 0.005, y: float = 0.005) -> list:
    """
    網格交易策略 (fractional position signals)

    Args:
        data: K線數據，需包含 'Close'
        x: 下跌買入閾值 (比例，例如 0.02 = -2%)
        y: 上漲賣出閾值 (比例，例如 0.02 = +2%)

    Returns:
        signals: 信號列表 (浮點數，正=買入比例，負=賣出比例)
    """
    signals = [0]
    if len(data) == 0:
        return signals

    # 初始持倉 0.5
    position = 0
    count = 0
    # print(position)
    last_trade_price = data['Close'].iloc[0]
    n = len(data)

    for i in range(1, n):
        price = data['Close'].iloc[i]
        change_pct = (price - last_trade_price) / last_trade_price
        # print(position)

        signal = 0.0

        # 下跌超過 x% → 買入 0.1
        if change_pct <= -x and position < 0.9:
            signals.append(0.1)
            position += 0.1
            last_trade_price = price

        # 上漲超過 y% → 賣出 0.1
        elif change_pct >= y and position > -0.9:
            signals.append(-0.1)
            position -= 0.1
            last_trade_price = price

        # 如果到達邊界 (0 or 1) → 重置回 0.5
        elif position <= -0.999 or position >= 0.999:
            count += 1
            reset_signal =  - position
            # print(position, reset_signal)
            signals.append(reset_signal)
            position = 0
            last_trade_price = price
        else:
            signals.append(0)


    return signals

def run_strategy_backtest(data_file, strategy_func, strategy_params=None):
    """載入數據 → 產生信號 → 降頻 → 回測"""
    backtest = BacktestEngine(initial_capital=10000, commission_rate=0.001, symbol='BTCUSDT')
    if not backtest.load_data(data_file):
        print("數據載入失敗")
        return None, None

    signals = strategy_func(backtest.data, **strategy_params) if strategy_params else strategy_func(backtest.data)
    
    performance = backtest.run_backtest(signals)
    backtest.print_summary()
    # 如不需圖，可註解下一行
    # backtest.plot_results()
    return backtest, performance

def objective_function(params):
    """
    評估策略績效的函數
    這裡用 Sharpe ratio 當作目標，你可以換成其他指標
    """
    data_file = 'kline_with_indicators/btcusdt_1m_train.csv'
    _, performance = run_strategy_backtest(data_file, grid_trading_strategy, params)
    sharp_ratio = performance.get('sharpe_ratio', 0)
    total_return = performance.get('total_return', 0)
    max_drawdown = performance.get('max_drawdown', 1)
    fitness = sharp_ratio * total_return / max(max_drawdown, 0.01)
    return fitness
    
best_val, best_params = brutal_search(
    objective_function,
    {
        "x": (0.001, 1),
        "y": (0.001, 1)
    },
    tol=1e-4,
    max_iter=200,
    int_params=None
)


_, performance = run_strategy_backtest(
    'kline_with_indicators/btcusdt_1m_test.csv',grid_trading_strategy, best_params)
sharp_ratio = performance.get('sharpe_ratio', 0)
total_return = performance.get('total_return', 0)
max_drawdown = performance.get('max_drawdown', 1)
print("最佳參數:", best_params)
print("最佳目標函數值:", {**best_params, "fitness": best_val, "Sharpe_ratio": sharp_ratio, "total_return": total_return, "max_drawdown": max_drawdown})

# 存成 DataFrame
df = pd.DataFrame([{**best_params, "fitness": best_val, "Sharpe_ratio": sharp_ratio, "total_return": total_return, "max_drawdown": max_drawdown}])

# 存到 CSV (append mode)
df.to_csv("grid_brutal_results.csv", mode="a", index=False, header=not pd.io.common.file_exists("results.csv"))