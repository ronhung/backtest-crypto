from backtest_platform import BacktestEngine
import random

# 設置隨機種子
random.seed(42)

def test_reduced_frequency():
    # 創建回測引擎
    backtest = BacktestEngine(initial_capital=10000, commission_rate=0.001, symbol='BTCUSDT')
    
    # 載入數據
    data_file = 'kline_with_indicators/btcusdt_1m.csv'
    if backtest.load_data(data_file):
        print('數據載入成功')
        
        # 生成原始信號
        original_signals = []
        for i in range(len(backtest.data)):
            if i % 3 == 0:
                original_signals.append(1)
            elif i % 5 == 0:
                original_signals.append(-1)
            else:
                original_signals.append(0)
        
        print(f'原始信號統計: 買入{original_signals.count(1)}, 賣出{original_signals.count(-1)}, 不動作{original_signals.count(0)}')
        
        # 減少交易頻率到1000次
        target_trades = 1000
        non_zero_indices = [i for i, s in enumerate(original_signals) if s != 0]
        signals_to_zero = len(non_zero_indices) - target_trades
        
        if signals_to_zero > 0:
            indices_to_zero = random.sample(non_zero_indices, signals_to_zero)
            for idx in indices_to_zero:
                original_signals[idx] = 0
        
        print(f'減少頻率後: 買入{original_signals.count(1)}, 賣出{original_signals.count(-1)}, 不動作{original_signals.count(0)}')
        
        # 執行回測
        try:
            performance = backtest.run_backtest(original_signals)
            print(f'\n回測結果:')
            print(f'  最終資金: ${performance["final_capital"]:,.2f}')
            print(f'  總收益率: {performance["total_return"]:.2%}')
            print(f'  最大回撤: {performance["max_drawdown"]:.2%}')
            print(f'  交易次數: {performance["total_trades"]}')
        except Exception as e:
            print(f'回測失敗: {e}')
    else:
        print('數據載入失敗')

if __name__ == "__main__":
    test_reduced_frequency()
