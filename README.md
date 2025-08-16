# 虛擬貨幣回測平台

這是一個專為虛擬貨幣設計的回測平台，支持1分鐘K線數據，手續費0.1%，全倉買賣策略。

## 功能特點

- **完整的回測引擎**：支持1分鐘K線數據回測
- **手續費計算**：買賣皆有0.1%手續費
- **全倉策略**：支持全倉買入/賣出策略
- **績效分析**：計算報酬率、夏普值、MDD等關鍵指標
- **視覺化圖表**：權益曲線、收益率、回撤分析、交易點位
- **多策略支持**：內建移動平均線、RSI、布林帶等策略

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 快速開始

### 1. 基本使用

```python
from backtest_platform import BacktestEngine

# 創建回測引擎
backtest = BacktestEngine(
    initial_capital=10000,  # 初始資金 $10,000
    commission_rate=0.001,  # 手續費 0.1%
    symbol='BTCUSDT'
)

# 載入數據
backtest.load_data('btcusdt_1m.csv')

# 生成信號（1=買入，0=不動作，-1=賣出）
signals = [1, 0, 0, -1, 0, 1, 0, -1, ...]

# 執行回測
performance = backtest.run_backtest(signals)

# 顯示結果
backtest.print_summary()
backtest.plot_results()
```

### 2. 使用內建策略

```python
from strategy_example import run_strategy_backtest, simple_moving_average_strategy

# 運行移動平均線策略
backtest, performance = run_strategy_backtest(
    data_file='btcusdt_1m.csv',
    strategy_func=simple_moving_average_strategy,
    strategy_params={'short_window': 10, 'long_window': 30}
)
```

### 3. 策略比較

```python
from strategy_example import compare_strategies

# 比較多個策略
compare_strategies('btcusdt_1m.csv')
```

## 數據格式

輸入數據應為CSV格式，包含以下列：

- `Open time`: 開盤時間
- `Open`: 開盤價
- `High`: 最高價
- `Low`: 最低價
- `Close`: 收盤價
- `Volume`: 成交量
- `Close time`: 收盤時間
- 其他列（可選）

## 信號格式

策略需要輸出信號列表，每個1分鐘K線對應一個信號：

- `1`: 買入全倉
- `0`: 不動作
- `-1`: 賣出全倉

## 績效指標

回測完成後會計算以下指標：

- **總收益率**: 整個回測期間的總收益
- **年化收益率**: 年化後的收益率
- **年化波動率**: 年化後的波動率
- **夏普比率**: 風險調整後的收益指標
- **最大回撤 (MDD)**: 最大回撤幅度
- **勝率**: 盈利交易的比例
- **交易次數**: 總交易次數

## 內建策略

### 1. 移動平均線策略
- 短期MA上穿長期MA時買入
- 短期MA下穿長期MA時賣出

### 2. RSI策略
- RSI從超賣區回升時買入
- RSI從超買區回落時賣出

### 3. 布林帶策略
- 價格觸及下軌時買入
- 價格觸及上軌時賣出

## 自定義策略

你可以創建自己的策略函數：

```python
def my_strategy(data: pd.DataFrame, param1: float, param2: int) -> list:
    """
    自定義策略
    
    Args:
        data: K線數據
        param1: 參數1
        param2: 參數2
    
    Returns:
        signals: 信號列表
    """
    signals = []
    
    # 你的策略邏輯
    for i in range(len(data)):
        # 根據你的邏輯生成信號
        if some_condition:
            signals.append(1)  # 買入
        elif another_condition:
            signals.append(-1)  # 賣出
        else:
            signals.append(0)  # 不動作
    
    return signals

# 使用自定義策略
backtest, performance = run_strategy_backtest(
    data_file='btcusdt_1m.csv',
    strategy_func=my_strategy,
    strategy_params={'param1': 0.5, 'param2': 20}
)
```

## 注意事項

1. **數據質量**: 確保輸入數據的完整性和準確性
2. **手續費**: 當前設定為0.1%，可根據實際情況調整
3. **滑點**: 當前模型假設按收盤價成交，實際交易可能有滑點
4. **流動性**: 全倉策略假設有足夠流動性，實際交易需考慮市場深度

## 文件結構

```
back_trading/
├── backtest_platform.py    # 主要回測引擎
├── strategy_example.py     # 策略示例
├── kline_data.py          # 數據處理
├── requirements.txt        # 依賴包
└── README.md              # 說明文檔
```

## 更新日誌

- v1.0.0: 初始版本，支持基本回測功能
- 支持多種技術指標策略
- 完整的績效分析
- 視覺化圖表展示

## 貢獻

歡迎提交Issue和Pull Request來改進這個回測平台！

## 免責聲明

本工具僅供學習和研究使用，不構成投資建議。實際交易請謹慎決策，自負盈虧。
