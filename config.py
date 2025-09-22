from dataclasses import dataclass
from pathlib import Path

@dataclass
class BacktestConfig:
    initial_capital: float = 10000
    commission_rate: float = 0.001
    symbol: str = 'BTCUSDT'
    data_percentage: float = 100.0  # 使用數據的百分比，預設100%表示使用全部數據

    @property
    def data_file(self):
        BASE_DIR = Path(__file__).parent
        return BASE_DIR / 'data/kline_with_indicators/btcusdt_1m.csv'
    
    # @property
    # def train_data_file(self):
    #     """訓練數據文件（前80%）"""
    #     BASE_DIR = Path(__file__).parent
    #     return BASE_DIR / 'data/kline_with_indicators/btcusdt_1m_train.csv'
    
    # @property
    # def test_data_file(self):
    #     """測試數據文件（後20%）"""
    #     BASE_DIR = Path(__file__).parent
    #     return BASE_DIR / 'data/kline_with_indicators/btcusdt_1m_test.csv'