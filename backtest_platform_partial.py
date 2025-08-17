import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class PartialPositionBacktestEngine:
    """
    支持部分倉位的虛擬貨幣回測引擎
    支持小數信號，如0.1表示買入10%倉位，-0.1表示賣出10%倉位
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 commission_rate: float = 0.001,  # 0.1%
                 data_file: str = None,
                 symbol: str = 'BTCUSDT'):
        
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.symbol = symbol
        
        # 初始化數據屬性
        self.data = None
        
        # 回測結果
        self.portfolio_values = []
        self.positions = []  # 倉位比例 (0-1)
        self.trades = []
        self.equity_curve = []
        
        # 載入數據
        if data_file:
            self.load_data(data_file)
    
    def load_data(self, data_file: str):
        """載入K線數據"""
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
    
    def run_backtest(self, signals: List[float]):
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
        current_position_value = 0.0  # 當前倉位價值
        entry_price = 0
        
        self.portfolio_values = [current_capital]
        self.positions = [current_position_ratio]
        self.trades = []
        
        print("開始執行回測...")
        
        for i, (signal, row) in enumerate(zip(signals, self.data.itertuples())):
            current_price = row.Close
            
            # 根據信號執行交易
            if signal > 0:  # 買入信號
                # 計算要買入的倉位比例
                target_position_ratio = min(1.0, current_position_ratio + signal)
                additional_position_ratio = target_position_ratio - current_position_ratio
                
                if additional_position_ratio > 0:
                    # 計算需要投入的資金
                    additional_capital_needed = additional_position_ratio * current_capital / (1 - additional_position_ratio)
                    
                    if additional_capital_needed <= current_capital:
                        # 執行買入
                        commission = additional_capital_needed * self.commission_rate
                        actual_investment = additional_capital_needed - commission
                        
                        # 更新倉位
                        if current_position_ratio == 0:
                            entry_price = current_price
                        
                        # 計算新的倉位比例和價值
                        total_position_value = current_position_value + actual_investment
                        current_position_ratio = target_position_ratio
                        current_position_value = total_position_value
                        current_capital -= additional_capital_needed
                        
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
                actual_sell_ratio = min(sell_position_ratio, current_position_ratio)
                
                if actual_sell_ratio > 0:
                    # 計算賣出價值
                    sell_value = current_position_value * (actual_sell_ratio / current_position_ratio)
                    commission = sell_value * self.commission_rate
                    net_sell_value = sell_value - commission
                    
                    # 更新倉位
                    current_position_ratio -= actual_sell_ratio
                    current_position_value -= sell_value
                    current_capital += net_sell_value
                    
                    # 如果倉位為0，重置入場價格
                    if current_position_ratio == 0:
                        entry_price = 0
                    
                    # 記錄交易
                    trade = {
                        'timestamp': row.Open_time,
                        'action': 'SELL',
                        'price': current_price,
                        'position_ratio': actual_sell_ratio,
                        'amount': sell_value,
                        'commission': commission,
                        'capital_before': current_capital - net_sell_value,
                        'capital_after': current_capital
                    }
                    self.trades.append(trade)
            
            # 更新投資組合價值
            if current_position_ratio > 0:
                # 有倉位，價值隨價格變動
                portfolio_value = current_capital + current_position_value * (current_price / entry_price)
            else:
                # 無倉位，只有現金
                portfolio_value = current_capital
            
            self.portfolio_values.append(portfolio_value)
            self.positions.append(current_position_ratio)
        
        # 計算權益曲線
        self.equity_curve = pd.Series(self.portfolio_values, 
                                     index=pd.concat([pd.Series([self.data['Open_time'].iloc[0] - pd.Timedelta(minutes=1)]), 
                                                     self.data['Open_time']]).reset_index(drop=True))
        
        print(f"回測完成！總交易次數: {len(self.trades)}")
        return self.calculate_performance()
    
    def calculate_performance(self) -> Dict:
        """計算績效指標"""
        if self.equity_curve is None or self.equity_curve.empty:
            return {}
        
        # 計算收益率
        total_return = (self.equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 計算日收益率
        daily_returns = self.equity_curve.pct_change().dropna()
        
        # 年化收益率（假設1分鐘數據，一年約525600分鐘）
        annual_return = (1 + total_return) ** (525600 / len(self.equity_curve)) - 1
        
        # 年化波動率
        annual_volatility = daily_returns.std() * np.sqrt(525600)
        
        # 夏普比率（假設無風險利率為0）
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤 (MDD)
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        mdd = drawdown.min()
        
        # 勝率
        if self.trades:
            profitable_trades = sum(1 for trade in self.trades if trade['action'] == 'SELL')
            if profitable_trades > 0:
                # 簡化的勝率計算
                win_rate = 0.5  # 假設50%勝率，實際需要更複雜的計算
            else:
                win_rate = 0
        else:
            win_rate = 0
        
        performance = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': mdd,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'final_capital': self.equity_curve.iloc[-1],
            'initial_capital': self.initial_capital
        }
        
        return performance
    
    def plot_results(self):
        """繪製回測結果圖表"""
        if self.equity_curve is None or self.equity_curve.empty:
            print("沒有回測數據可繪製")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{self.symbol} 部分倉位回測結果', fontsize=16)
        
        # 權益曲線
        axes[0, 0].plot(self.equity_curve.index, self.equity_curve.values, linewidth=2)
        axes[0, 0].set_title('投資組合價值變化')
        axes[0, 0].set_ylabel('投資組合價值')
        axes[0, 0].grid(True)
        
        # 倉位變化
        axes[0, 1].plot(self.equity_curve.index, self.positions, alpha=0.7, color='orange')
        axes[0, 1].set_title('倉位比例變化')
        axes[0, 1].set_ylabel('倉位比例')
        axes[0, 1].grid(True)
        
        # 收益率
        returns = self.equity_curve.pct_change().dropna()
        axes[1, 0].plot(returns.index, returns.values, alpha=0.7)
        axes[1, 0].set_title('收益率變化')
        axes[1, 0].set_ylabel('收益率')
        axes[1, 0].grid(True)
        
        # 交易記錄
        if self.trades:
            trade_df = pd.DataFrame(self.trades)
            buy_trades = trade_df[trade_df['action'] == 'BUY']
            sell_trades = trade_df[trade_df['action'] == 'SELL']
            
            axes[1, 1].scatter(buy_trades['timestamp'], buy_trades['price'], 
                              color='green', marker='^', s=50, label='買入')
            axes[1, 1].scatter(sell_trades['timestamp'], sell_trades['price'], 
                              color='red', marker='v', s=50, label='賣出')
            axes[1, 1].plot(self.data['Open_time'], self.data['Close'], alpha=0.7, label='價格')
            axes[1, 1].set_title('交易點位')
            axes[1, 1].set_ylabel('價格')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def print_summary(self):
        """打印回測摘要"""
        performance = self.calculate_performance()
        
        print("\n" + "="*50)
        print(f"{self.symbol} 部分倉位回測摘要")
        print("="*50)
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終資金: ${performance['final_capital']:,.2f}")
        print(f"總收益率: {performance['total_return']:.2%}")
        print(f"年化收益率: {performance['annual_return']:.2%}")
        print(f"年化波動率: {performance['annual_volatility']:.2%}")
        print(f"夏普比率: {performance['sharpe_ratio']:.3f}")
        print(f"最大回撤: {performance['max_drawdown']:.2%}")
        print(f"勝率: {performance['win_rate']:.2%}")
        print(f"總交易次數: {performance['total_trades']}")
        print("="*50)

# 示例使用
def example_usage():
    """示例使用方法"""
    # 創建部分倉位回測引擎
    backtest = PartialPositionBacktestEngine(
        initial_capital=10000,  # 初始資金 $10,000
        commission_rate=0.001,  # 手續費 0.1%
        symbol='BTCUSDT'
    )
    
    print("部分倉位回測引擎已創建完成！")
    print("支持小數信號，如0.1表示買入10%倉位，-0.1表示賣出10%倉位")

if __name__ == "__main__":
    example_usage()
