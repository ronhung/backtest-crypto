from backtest_platform import BacktestEngine
from strategy_example import (
    simple_moving_average_strategy,
    rsi_strategy,
    partial_rsi_strategy,
    bollinger_bands_strategy,
    buy_and_hold_strategy,
)
import pandas as pd

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
    backtest.plot_results()
    return backtest, performance

# 讀取並排序
df = pd.read_csv("rsi_grid_search_results_rsi.csv")
df_sorted = df.sort_values(by="score", ascending=False)

# 取出前 10 筆
top10_rsi = df_sorted.head(10)

# 讀取並排序
df = pd.read_csv("rsi_grid_search_results_sma.csv")
df_sorted = df.sort_values(by="score", ascending=False)

# 取出前 10 筆
top10_sma = df_sorted.head(10)

def objective_function(result: dict) -> float:
    """
    評估策略績效的函數
    這裡用 Sharpe ratio 當作目標，你可以換成其他指標
    """
    return result.get('total_return', 0)

def best_sma_strategy_selection(top_param):
    data_file = 'kline_with_indicators/btcusdt_1m_test.csv'
    best_score = -float("inf")
    best_params = None
    results = []

    for row in top_param.itertuples():
        params = {
            "short_window": row.short_window,
            "long_window": row.long_window
        }

        print(f"測試參數: {params}")
        _, performance = run_strategy_backtest(data_file, simple_moving_average_strategy, params)
        print(f"績效: {performance}")
        print("-"*30)
        # 評估績效
        score = objective_function(performance)

        results.append((params, score))

        if score > best_score:
            best_score = score
            best_params = params

    print("最佳參數:", best_params)
    print("最佳績效:", best_score)
    print(results)
    df = pd.DataFrame([
        {**params, "score": float(score)} for params, score in results
    ])
    df.to_csv("rsi_grid_search_results_test_sma.csv", index=False)

def best_rsi_strategy_selection(top_param):
    data_file = 'kline_with_indicators/btcusdt_1m_train.csv'
    best_score = -float("inf")
    best_params = None
    results = []

    for row in top_param.itertuples():
        params = {
        "rsi_period": row.rsi_period,
        "oversold": row.oversold,
        "overbought": row.overbought
        }

        print(f"測試參數: {params}")
        _, performance = run_strategy_backtest(data_file, rsi_strategy, params)
        print(f"績效: {performance}")
        print("-"*30)

        # 評估績效
        score = objective_function(performance)

        results.append((params, score))

        if score > best_score:
            best_score = score
            best_params = params

    print("最佳參數:", best_params)
    print("最佳績效:", best_score)
    print(results)
    df = pd.DataFrame([
        {**params, "score": float(score)} for params, score in results
    ])
    df.to_csv("rsi_grid_search_results_train_rsi.csv", index=False)

def test_sma(short_window, long_window):
    data_file = 'kline_with_indicators/btcusdt_1m_test.csv'
    params = {
        "short_window": short_window,
        "long_window": long_window
    }
    _, performance = run_strategy_backtest(data_file, simple_moving_average_strategy, params)
    print(f"績效: {performance}")

    _, performance = run_strategy_backtest(data_file, buy_and_hold_strategy, None)
    print(f"績效: {performance}")


if __name__ == "__main__":
    # 直接運行快速測試
    # quick_test()
    
    # 如果想要互動式選擇，可以取消註釋下面的行
    # main()

    # best_sma_strategy_selection(top10_sma)
    # print("="*50)
    # best_rsi_strategy_selection(top10_rsi)
    # print("="*50)
    # data_file = 'kline_with_indicators/btcusdt_1m_test.csv'
    # _, result = run_strategy_backtest(data_file, buy_and_hold_strategy , None)
    # print(result)

    test_sma(3600, 28800)

