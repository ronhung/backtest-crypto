# 虛擬貨幣回測與策略優化平台 - 完整流程文檔

## 📋 當前系統架構分析

### 核心組件

#### 1. 回測引擎 (`backtest_engine.py`)
- **功能**: 支持全倉和部分倉位策略的回測引擎
- **特點**: 
  - 等權勝率計算
  - FIFO沖銷單追蹤
  - 完整的績效指標計算
  - 視覺化圖表生成

#### 2. 策略庫 (`strategies`)
- **內建策略**:
  - `simple_moving_average_strategy`: 移動平均線策略
  - `rsi_strategy`: RSI策略
  - `bollinger_bands_strategy`: 布林帶策略
  - `buy_and_hold_strategy`: 買入並持有策略
- **特點**: 支持參數化配置，返回信號列表

#### 3. 參數優化模組 (`optimization`)
- **`brutal_search.py`**: 暴力搜索優化
- **`coordinate_search.py`**: 座標下降優化
- **`hyperband_brutal_search.py`**: Hyperband優化算法

#### 4. 數據庫 (`data`)
- **數據源**: Binance歷史數據

#### 5. 使用範例 (`usage_example.py`)
- **功能**: 策略測試、參數優化
- **特點**: 
  - 使用現有策略或自定義策略
  - 支援參數優化
  - 結果可視化



### 1. 文件結構

```
crypto_backtest/
├── core/
│   ├── __init__.py
│   ├── backtest_engine.py      # 回測引擎
│   └── performance.py          # 績效計算
├── strategies/
│   ├── base_strategy.py        # 策略基類
│   ├── technical_strategies.py # 技術指標策略
│   └── grid_strategies.py      # 網格策略
├── optimization/
│   ├── brutal_search.py        # 暴力搜索
│   ├── coordinate_search.py    # 座標搜索
│   └── hyperband_brutal_search.py # Hyperband
├── data/
│   ├── kline_data/             # 原始數據
│   ├── kline_with_indicators/  # 增加指標數據
├── usage_example.py            # 用法介紹
└── config.py                   # 配置設定
```

### 2. 回測使用流程

#### 1. 使用config 或是自訂回測平台參數
    class BacktestConfig:
    initial_capital: float = 10000
    commission_rate: float = 0.001
    symbol: str = 'BTCUSDT'
    data_percentage: float = 100.0  # 使用數據的百分比，預設100%表示使用全部數據

    @property
    def data_file(self):
        BASE_DIR = Path(__file__).parent
        return BASE_DIR / 'data/kline_with_indicators/btcusdt_1m.csv'
#### 2. 使用已存在策略或自訂策略
    def strategy():
        return signals 買入賣出信號
#### 3. 決定是否使用參數優化
    def brutal_search(
        obj_func,               # 目標函數
        param_space,            # Dict[str, Union[Tuple[float, float], Sequence[Any]]] 參數空間(支援上下界或清單)
        max_iter,               # 最大迭代次數
        int_params,             # 整數參數清單
        seed,                   # 隨機種子 (便於試驗複製)
        patience,               # 提前結束次數 (若結果未變好)
        greater_is_better,      # maximize obj_value
        verbose,                # 是否印出優化過程
        callback,               # 自訂每次迭代時額外操作
    ):
    return best_score, best_params, history #最佳結果與總歷史
#### 4. 進行回測
    run_backtest
        特點:
        1. 所有操作皆針對現貨市場，故無支援未持倉時賣出
        2. 支援小數信號，代表部分倉位交易
        3. 計算破產時長便於參數優化
        4. 回測引擎初始化支持自訂參數輸入或是由config.py引入
        5. 支援自訂data百分比回測，可只測試部分data，方便參數調整與切分train/test






