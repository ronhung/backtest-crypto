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
from coordinate_search import coordinate_search


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
    _, performance = run_strategy_backtest(data_file, simple_moving_average_strategy, params)
    return performance.get('sharpe_ratio', 0)
    

best_params, best_objval = coordinate_search(
    objective_function,
    x0 = {
    "short_window": 3600,
    "long_window": 28800,
    "k": 1
    },
    tol=1e-2,
    max_iter=50,
    int_params={"short_window", "long_window"}
)

print("最佳參數:", best_params)
print("最佳目標函數值 (Sharpe ratio):", best_objval)