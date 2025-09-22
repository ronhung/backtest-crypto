import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import warnings
from .performance import PerformanceAnalyzer
from config import BacktestConfig

warnings.filterwarnings('ignore')

class BacktestEngine:
    """
    支持部分倉位的虛擬貨幣回測引擎
    支持小數信號，如0.1表示買入10%倉位，-0.1表示賣出10%倉位
    """
    
    def __init__(self, 
                 initial_capital: Optional[float] = None,
                 commission_rate: Optional[float] = None,
                 data_file: Optional[str] = None,
                 symbol: Optional[str] = None,
                 data_percentage: Optional[float] = None,
                 config: Optional[BacktestConfig] = None):
        """
        初始化回測引擎
        
        Args:
            initial_capital: 初始資金
            commission_rate: 手續費率
            data_file: 數據文件路徑
            symbol: 交易對符號
            data_percentage: 使用數據的百分比
            config: 配置對象，如果提供則優先使用配置中的值
        """
        # 如果提供了配置對象，優先使用配置中的值
        if config is not None:
            self.initial_capital = initial_capital if initial_capital is not None else config.initial_capital
            self.commission_rate = commission_rate if commission_rate is not None else config.commission_rate
            self.symbol = symbol if symbol is not None else config.symbol
            self.data_percentage = data_percentage if data_percentage is not None else config.data_percentage
            self.data_file = data_file if data_file is not None else str(config.data_file)
        else:
            # 使用預設值或傳入的參數
            self.initial_capital = initial_capital if initial_capital is not None else 10000
            self.commission_rate = commission_rate if commission_rate is not None else 0.001
            self.symbol = symbol if symbol is not None else 'BTCUSDT'
            self.data_percentage = data_percentage if data_percentage is not None else 100.0
            self.data_file = data_file
        
        # 初始化數據屬性
        self.data = None
        
        # 回測結果
        self.portfolio_values = []
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        # 新增：沖銷單追蹤
        self.open_positions = []  # 未平倉的買入記錄
        self.closed_positions = []  # 已完成的沖銷單
        
        # 載入數據
        if self.data_file:
            self.load_data(self.data_file)
    
    @classmethod
    def from_config(cls, config: BacktestConfig, **kwargs):
        """
        從配置對象創建回測引擎
        
        Args:
            config: BacktestConfig 配置對象
            **kwargs: 額外的參數，會覆蓋配置中的值
        
        Returns:
            BacktestEngine: 配置好的回測引擎實例
        """
        return cls(
            initial_capital=kwargs.get('initial_capital', config.initial_capital),
            commission_rate=kwargs.get('commission_rate', config.commission_rate),
            data_file=kwargs.get('data_file', str(config.data_file)),
            symbol=kwargs.get('symbol', config.symbol),
            data_percentage=kwargs.get('data_percentage', config.data_percentage),
            config=config
        )
    
    def load_data(self, data_file: str):
        """
        載入K線數據
        
        Args:
            data_file: 數據文件路徑
            percentage: 使用數據的百分比，預設100表示使用全部數據
                       例如：50表示使用前50%的數據
        """
        try:
            self.data = pd.read_csv(data_file)
            
            # 轉換時間格式 - 統一使用下劃線命名以確保與itertuples()兼容
            self.data['Open_time'] = pd.to_datetime(self.data['Open time'])
            self.data['Close_time'] = pd.to_datetime(self.data['Close time'])
            
            # 確保價格列為數值型
            price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in price_cols:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            print(f"成功載入數據: {len(self.data)} 條記錄")
            print(f"時間範圍: {self.data['Open_time'].min()} 到 {self.data['Open_time'].max()}")
            return True
            
        except Exception as e:
            print(f"載入數據失敗: {e}")
            self.data = None
            return False
    
    def run_backtest(self, signals: List[float], percentage: float = 100.0):
        """
        執行回測
        
        Args:
            signals: 信號列表，正值=買入比例，負值=賣出比例，0=不動作
                    例如：0.1表示買入10%倉位，-0.1表示賣出10%倉位
        """
        if self.data is None:
            raise ValueError("請先載入數據")
        
        if len(signals) != len(self.data):
            raise ValueError(f"信號數量({len(signals)})與數據數量({len(self.data)})不匹配")
        
        # 初始化
        current_capital = self.initial_capital
        current_position_ratio = 0.0  # 當前倉位比例 (0-1)
        current_position = 0.0  # 當前倉位
        
        self.portfolio_values = [current_capital]
        self.positions = [current_position_ratio]
        self.trades = []
        
        # 重置沖銷單追蹤
        self.open_positions = []
        self.closed_positions = []
        
        print("開始執行回測...")
        
        target_length = int(len(self.data) * percentage / 100.0)
        signals = signals[:target_length]
        data = self.data.head(target_length)

        for i, (signal, row) in enumerate(zip(signals, data.itertuples())):
            current_price = row.Close
            
            # 根據信號執行交易
            if signal > 0:  # 買入信號
                # 計算要買入的倉位比例
                target_position_ratio = min(1.0, current_position_ratio + signal)
                additional_position_ratio = target_position_ratio - current_position_ratio
                
                if additional_position_ratio > 0:
                    # 計算需要投入的資金
                    additional_capital_needed = additional_position_ratio * current_capital / (1 - current_position_ratio)
                    
                    if additional_capital_needed <= current_capital:
                        # 執行買入
                        commission = additional_capital_needed * self.commission_rate
                        actual_investment = (additional_capital_needed - commission)/ current_price
                        
                        
                        # 計算新的倉位比例和價值
                        total_position = current_position + actual_investment
                        current_position_ratio = target_position_ratio
                        current_position = total_position
                        current_capital -= additional_capital_needed
                        
                        # 處理買入交易並記錄沖銷單
                        self._process_buy_trade(actual_investment, current_price, row.Open_time, commission)
                        
                        # 記錄交易
                        trade = {
                            'timestamp': row.Open_time,
                            'action': 'BUY',
                            'price': current_price,
                            'position_ratio': additional_position_ratio,
                            'amount': actual_investment,
                            'commission': commission,
                            'capital_before': current_capital + additional_capital_needed,
                            'capital_after': current_capital
                        }
                        self.trades.append(trade)
                
            elif signal < 0:  # 賣出信號
                # 計算要賣出的倉位比例
                sell_position_ratio = abs(signal)
                target_position_ratio = max(0.0, current_position_ratio - sell_position_ratio)
                current_assest = current_capital + current_position * current_price
                real_position_ratio = (current_position * current_price) / current_assest
                if target_position_ratio < real_position_ratio:  # 目標倉位比小於目前真實倉位比

                    # 計算賣出價值
                    target_position = target_position_ratio * current_assest / current_price
                    sell_position = current_position - target_position
                    sell_value = sell_position * current_price
                    commission = sell_value * self.commission_rate
                    net_sell_value = sell_value - commission
                    
                    # 更新倉位
                    actual_sell_position_ratio = current_position_ratio - target_position_ratio
                    current_position_ratio = target_position_ratio
                    current_position -= sell_position
                    current_capital += net_sell_value
                    
                    # 處理沖銷單並計算盈虧
                    self._process_sell_trade(sell_position, current_price, row.Open_time, commission)
                    
                    # 記錄交易（包含沖銷單信息）
                    trade = {
                        'timestamp': row.Open_time,
                        'action': 'SELL',
                        'price': current_price,
                        'position_ratio': actual_sell_position_ratio,
                        'amount': sell_value,
                        'commission': commission,
                        'capital_before': current_capital - net_sell_value,
                        'capital_after': current_capital,
                        'closed_positions': self.closed_positions  # 新增：沖銷單信息
                    }
                    self.trades.append(trade)
            
            # 更新投資組合價值
            if current_position_ratio > 0:
                # 有倉位，價值隨價格變動
                portfolio_value = current_capital + current_position * current_price
            else:
                # 無倉位，只有現金
                portfolio_value = current_capital
            if self.portfolio_values == 0:
                self.portfolio_values.extend([portfolio_value] * (len(self.data) - i))
                self.positions.extend([current_position_ratio] * (len(self.data) - i))
                break
            self.portfolio_values.append(portfolio_value)
            self.positions.append(current_position_ratio)
        
        # 計算權益曲線
        self.equity_curve = pd.Series(self.portfolio_values, 
                                     index=pd.concat([pd.Series([self.data['Open_time'].iloc[0] - pd.Timedelta(minutes=1)]), 
                                                     self.data['Open_time']]).reset_index(drop=True))
        
        print(f"回測完成！總交易次數: {len(self.trades)}")
        print(f"總沖銷單數: {len(self.closed_positions)}")
        
        # 使用PerformanceAnalyzer計算績效
        analyzer = PerformanceAnalyzer(
            self.equity_curve, 
            self.closed_positions, 
            self.initial_capital, 
            self.trades,
            config=getattr(self, 'config', None)
        )
        
        return analyzer.calculate_performance()
    
    def _process_buy_trade(self, quantity: float, price: float, timestamp, commission: float):
        """處理買入交易，記錄到未平倉列表"""
        self.open_positions.append({
            'quantity': quantity,
            'buy_price': price,
            'buy_timestamp': timestamp,
            'commission': commission
        })
    
    def _process_sell_trade(self, sell_quantity: float, sell_price: float, timestamp, commission: float):
        """處理賣出交易，使用FIFO原則處理沖銷單"""
        remaining_sell = sell_quantity
        
        while remaining_sell > 0 and self.open_positions:
            # 取最早的買入記錄
            buy_record = self.open_positions[0]
            buy_quantity = buy_record['quantity']
            buy_price = buy_record['buy_price']
            buy_timestamp = buy_record['buy_timestamp']
            buy_commission = buy_record['commission']
            
            if buy_quantity <= remaining_sell:
                # 完全沖銷這筆買入
                sell_quantity_for_this_buy = buy_quantity
                remaining_sell -= buy_quantity
                self.open_positions.pop(0)  # 移除已完全沖銷的買入記錄
            else:
                # 部分沖銷這筆買入
                sell_quantity_for_this_buy = remaining_sell
                buy_record['quantity'] -= remaining_sell  # 更新剩餘數量
                remaining_sell = 0
            
            # 計算這筆沖銷單的盈虧
            gross_profit = (sell_price - buy_price) * sell_quantity_for_this_buy
            total_commission = buy_commission * (sell_quantity_for_this_buy / buy_quantity) + commission * (sell_quantity_for_this_buy / sell_quantity)
            net_profit = gross_profit - total_commission
            
            # 記錄沖銷單
            self.closed_positions.append({
                'quantity': sell_quantity_for_this_buy,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'buy_timestamp': buy_timestamp,
                'sell_timestamp': timestamp,
                'gross_profit': gross_profit,
                'commission': total_commission,
                'net_profit': net_profit
            })
    
    def calculate_performance(self) -> Dict:
        """計算績效指標（向後兼容）"""
        analyzer = PerformanceAnalyzer(
            self.equity_curve, 
            self.closed_positions, 
            self.initial_capital, 
            self.trades,
            config=getattr(self, 'config', None)
        )
        return analyzer.calculate_performance()
    
    def get_position_details(self) -> pd.DataFrame:
        """獲取沖銷單詳細信息（向後兼容）"""
        analyzer = PerformanceAnalyzer(
            self.equity_curve, 
            self.closed_positions, 
            self.initial_capital, 
            self.trades,
            config=getattr(self, 'config', None)
        )
        return analyzer.get_position_details()
    
    def plot_results(self):
        """繪製回測結果圖表（向後兼容）"""
        analyzer = PerformanceAnalyzer(
            self.equity_curve, 
            self.closed_positions, 
            self.initial_capital, 
            self.trades,
            config=getattr(self, 'config', None)
        )
        analyzer.plot_results(self.symbol, self.positions, self.data)
    
    def print_summary(self):
        """打印回測摘要（向後兼容）"""
        analyzer = PerformanceAnalyzer(
            self.equity_curve, 
            self.closed_positions, 
            self.initial_capital, 
            self.trades,
            config=getattr(self, 'config', None)
        )
        analyzer.print_summary(self.symbol)
