from backtest_platform import BacktestEngine

backtest = BacktestEngine(
    initial_capital=10000,  # 初始資金 $10,000
    commission_rate=0.001,  # 手續費 0.1%
    symbol='BTCUSDT'
)

# 載入數據
backtest.load_data('kline_with_indicators/btcusdt_1m.csv')

# 生成信號（1=買入，0=不動作，-1=賣出）
signals = []

for i in range(len(backtest.data)):
    if i % 3 == 0:
        signals.append(1)
        continue
    elif i % 5 == 0:
        signals.append(-1)  # 假設每五個數據點賣出一次
    else:
        signals.append(0)  # 不動作
# 執行回測
performance = backtest.run_backtest(signals)

# 顯示結果
backtest.print_summary()
backtest.plot_results()
