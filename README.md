# 虛擬貨幣回測平台

專為虛擬貨幣設計的回測平台，支持全倉和部分倉位策略，具備完整的績效分析和等權勝率計算功能。

## 🚀 核心功能

- **等權勝率計算**: 每個沖銷單權重相同，準確反映策略表現
- **智能沖銷單追蹤**: 支持分批加倉和減倉，FIFO原則處理
- **雙引擎支持**: 全倉策略引擎 + 部分倉位引擎
- **完整績效分析**: 收益率、夏普比率、最大回撤、勝率等指標
- **內建策略庫**: 移動平均線、RSI、布林帶等常用策略

## 📦 安裝

```bash
pip install -r requirements.txt
```

## 🎯 快速開始

### 部分倉位策略（推薦）

```python
from backtest_platform import BacktestEngine

# 創建回測引擎
backtest = BacktestEngine(initial_capital=100000, commission_rate=0.001)

# 載入數據
backtest.load_data('btcusdt_1h.csv')

# 小數信號：0.3=買入30%倉位，-0.2=賣出20%倉位
signals = [0.3, 0, 0.2, 0, 0, -0.2, 0, 0.1, 0, 0, -0.3, 0, 0, -0.1]

# 執行回測
performance = backtest.run_backtest(signals)

# 顯示結果
backtest.print_summary()
backtest.print_position_details()  # 沖銷單詳細信息
```

### 全倉策略

```python
# 整數信號：1=買入全倉，0=不動作，-1=賣出全倉
signals = [1, 0, 0, -1, 0, 1, 0, -1]

performance = backtest.run_backtest(signals)
backtest.print_summary()
```

### 使用內建策略

```python
from strategy_example import run_strategy_backtest, simple_moving_average_strategy

# 運行移動平均線策略
backtest, performance = run_strategy_backtest(
    data_file='btcusdt_1h.csv',
    strategy_func=simple_moving_average_strategy,
    strategy_params={'short_window': 10, 'long_window': 30}
)
```

## 🔍 等權勝率計算

### 核心概念

- **沖銷單**: 一個買入交易和對應賣出交易組成的完整交易對
- **等權計算**: 每個沖銷單在勝率計算中權重相同
- **FIFO原則**: 先進先出處理賣出，支持分批平倉

### 勝率計算邏輯

```
勝率 = 盈利沖銷單數 / 總沖銷單數
```

### 分批交易示例

買進 1 BTC，分批賣出 0.4 + 0.6 BTC
→ 拆分成兩筆獨立沖銷單，每筆權重相同

## 📊 績效指標

### 基礎指標
- **總收益率**: 整個回測期間的總收益
- **年化收益率**: 年化後的收益率
- **夏普比率**: 風險調整後的收益指標
- **最大回撤 (MDD)**: 最大回撤幅度

### 等權勝率指標
- **勝率 (等權)**: 盈利沖銷單比例
- **總沖銷單數**: 完成的交易對數量
- **平均盈虧**: 每筆沖銷單的平均盈虧
- **最大單筆盈利**: 最大盈利交易（無盈利時顯示"無盈利交易"）
- **最大單筆虧損**: 最大虧損交易（無虧損時顯示"無虧損交易"）

## 📈 內建策略

- **移動平均線策略**: 短期MA上穿長期MA時買入，下穿時賣出
- **RSI策略**: RSI從超賣區回升時買入，從超買區回落時賣出
- **布林帶策略**: 價格觸及下軌時買入，觸及上軌時賣出

## 🎛️ 交易頻率控制

避免過度交易，優化策略表現：

```python
from test_reduced_frequency import reduce_trading_frequency

# 將交易次數控制在1000次左右
reduced_signals = reduce_trading_frequency(original_signals, target_trades=1000)
```

## 📁 數據格式

CSV格式，包含：`Open time`, `Open`, `High`, `Low`, `Close`, `Volume`, `Close time`

## 📝 信號格式

### 離散信號（全倉策略）
- `1`: 買入全倉
- `0`: 不動作
- `-1`: 賣出全倉

### 小數信號（部分倉位策略）
- `0.1`: 買入10%倉位
- `0.5`: 買入50%倉位
- `0`: 不動作
- `-0.1`: 賣出10%倉位
- `-0.5`: 賣出50%倉位

## 🧪 測試和示例

### 運行測試
```bash
python test_win_rate.py          # 等權勝率計算測試
python test_loss_scenario.py     # 虧損場景測試
```

### 運行示例
```bash
python example_win_rate.py       # 基本使用示例
python demo_display_improvement.py  # 顯示效果演示
```

## 📋 文件結構

```
backtest-crypto/
├── backtest_platform.py           # 主要回測引擎（支持等權勝率計算）
├── strategy_example.py            # 內建策略示例
├── test_win_rate.py              # 等權勝率計算測試
├── example_win_rate.py           # 等權勝率使用示例
├── demo_display_improvement.py   # 顯示效果演示
└── requirements.txt               # 依賴包
```

## 🔄 更新日誌

- **v2.0**: 新增等權勝率計算功能
- **v2.1**: 優化沖銷單追蹤算法
- **v2.2**: 增加詳細盈虧分析功能
- **v2.3**: 改進顯示邏輯（無盈利/虧損時顯示友好提示）
- **v2.4**: 改進年化收益率計算（根據實際數據時間段計算）

## 💡 使用建議

1. **初學者**: 從基本使用示例開始，了解等權勝率計算
2. **策略開發**: 使用內建策略作為模板，開發自定義策略
3. **風險控制**: 使用交易頻率控制，避免過度交易
4. **進階分析**: 利用沖銷單詳細信息，深入分析策略表現

## ⚠️ 注意事項

- 確保輸入數據的完整性和準確性
- 手續費設定為0.1%，可根據實際情況調整
- 過高交易頻率會導致手續費累積，建議控制在1000-2000次交易
- 小數信號支持更靈活的倉位管理，推薦使用

## 📞 貢獻

歡迎提交Issue和Pull Request來改進這個回測平台！

## ⚖️ 免責聲明

本工具僅供學習和研究使用，不構成投資建議。實際交易請謹慎決策，自負盈虧。
