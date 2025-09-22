from core.backtest_engine import BacktestEngine
from config import BacktestConfig
from strategies.simple_moving_average_strategy import simple_moving_average_strategy
from optimization.brutal_search import brutal_search
import numpy as np
from optimization.hyperband_brutal_search import hyperband_search


def run_strategy_backtest(data_file: str = None, strategy_func=None, strategy_params: dict = None, config: BacktestConfig = None):
    """
    運行策略回測
    
    Args:
        data_file: 數據文件路徑（可省略，若提供 config 則優先使用 config.data_file）
        strategy_func: 策略函數
        strategy_params: 策略參數
        config: BacktestConfig 配置
    """
    # 準備配置
    cfg = config or BacktestConfig()
    effective_data_file = data_file or str(cfg.train_data_file)

    # 使用配置創建引擎
    backtest = BacktestEngine.from_config(cfg, data_file=effective_data_file)
    if backtest.data is None:
        print("數據載入失敗")
        return None, None
    
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
    performance = backtest.run_backtest(signals, percentage=100)
    
    # 顯示結果
    backtest.print_summary()
    
    # 繪製圖表
    # backtest.plot_results()
    
    return backtest, performance

def fitness_function(performance: dict) -> float:
    sharp_ratio = performance.get('sharpe_ratio', 0)
    total_return = performance.get('total_return', 0)
    max_drawdown = performance.get('max_drawdown', 1)
    dead_time = performance.get('dead_time_minutes', None)
    fitness = sharp_ratio * total_return / max(max_drawdown, 0.01) + dead_time
    return fitness

def obgect_function(params: dict) -> float:
    _, performance = run_strategy_backtest(strategy_func=simple_moving_average_strategy, strategy_params=params, config=BacktestConfig())
    fitness = fitness_function(performance)
    return fitness

def hyperband_objective(params: dict, percentage: float) -> float:
    backtest, performance = run_strategy_backtest(
        strategy_func=simple_moving_average_strategy,
        strategy_params=params,
        config=BacktestConfig()
    )
    # 使用 percentage 參數加速回測
    # 例如 BacktestEngine.run_backtest 可改成 percentage=percentage
    if backtest is not None:
        performance = backtest.run_backtest(
            signals=simple_moving_average_strategy(backtest.data, **params),
            percentage=percentage
        )
        fitness = fitness_function(performance)
        return fitness
    return -np.inf


if __name__ == "__main__":
    # 示例使用
    print("單一策略回測：run_strategy_backtest(data_file, strategy_func, params)")
    params = brutal_search(obgect_function, param_space={"short_window": (10, 100), "long_window": (30, 300), "k": (0.1, 1)}, max_iter=100, int_params={"short_window", "long_window"})
    hyper_params = hyperband_search(hyperband_objective, param_space={"short_window": (10, 100), "long_window": (30, 300), "k": (0.1, 1)}, max_iter=100, int_params={"short_window", "long_window"})
    run_strategy_backtest(strategy_func=simple_moving_average_strategy, strategy_params=hyper_params, config=BacktestConfig())