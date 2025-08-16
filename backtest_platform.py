import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    """
    虛擬貨幣回測引擎
    支持1分鐘K線數據，手續費0.1%，全倉買賣策略
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 commission_rate: float = 0.001,  # 0.1%
                 data_file: str = None,
                 symbol: str = 'BTCUSDT'):
        
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.symbol = symbol
        
        # 回測結果
        self.portfolio_values = []
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        # 載入數據
        if data_file:
            self.load_data(data_file)
    
    def load_data(self, data_file: str):
        """載入K線數據"""
        try:
            self.data = pd.read_csv(data_file)
            # 轉換時間格式
            self.data['Open time'] = pd.to_datetime(self.data['Open time'])
            self.data['Close time'] = pd.to_datetime(self.data['Close time'])
            
            # 確保價格列為數值型
            price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in price_cols:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            print(f"成功載入數據: {len(self.data)} 條記錄")
            print(f"時間範圍: {self.data['Open time'].min()} 到 {self.data['Open time'].max()}")
            
        except Exception as e:
            print(f"載入數據失敗: {e}")
            return False
        return True
    
    def run_backtest(self, signals: List[int]):
        """
        執行回測
        
        Args:
            signals: 信號列表，1=買入全倉，0=不動作，-1=賣出全倉
        """
        if len(signals) != len(self.data):
            raise ValueError(f"信號數量({len(signals)})與數據數量({len(self.data)})不匹配")
        
        # 初始化
        current_capital = self.initial_capital
        current_position = 0  # 0=現金，1=全倉
        entry_price = 0
        
        self.portfolio_values = [current_capital]
        self.positions = [current_position]
        self.trades = []
        
        print("開始執行回測...")
        
        for i, (signal, row) in enumerate(zip(signals, self.data.itertuples())):
            current_price = row.Close
            
            # 根據信號執行交易
            if signal == 1 and current_position == 0:  # 買入信號且當前為現金
                # 計算可買入的數量（扣除手續費）
                buyable_amount = current_capital * (1 - self.commission_rate)
                current_position = 1
                entry_price = current_price
                
                # 記錄交易
                trade = {
                    'timestamp': row.Open_time,
                    'action': 'BUY',
                    'price': current_price,
                    'amount': buyable_amount,
                    'commission': current_capital * self.commission_rate,
                    'capital_before': current_capital,
                    'capital_after': buyable_amount
                }
                self.trades.append(trade)
                
                current_capital = buyable_amount
                
            elif signal == -1 and current_position == 1:  # 賣出信號且當前為全倉
                # 賣出全倉（扣除手續費）
                sell_amount = current_capital * (1 - self.commission_rate)
                current_position = 0
                
                # 記錄交易
                trade = {
                    'timestamp': row.Open_time,
                    'action': 'SELL',
                    'price': current_price,
                    'amount': sell_amount,
                    'commission': current_capital * self.commission_rate,
                    'capital_before': current_capital,
                    'capital_after': sell_amount
                }
                self.trades.append(trade)
                
                current_capital = sell_amount
                entry_price = 0
            
            # 更新投資組合價值
            if current_position == 1:
                # 全倉狀態，價值隨價格變動
                portfolio_value = current_capital * (current_price / entry_price)
            else:
                # 現金狀態
                portfolio_value = current_capital
            
            self.portfolio_values.append(portfolio_value)
            self.positions.append(current_position)
        
        # 計算權益曲線
        self.equity_curve = pd.Series(self.portfolio_values, 
                                     index=pd.concat([pd.Series([self.data['Open time'].iloc[0] - pd.Timedelta(minutes=1)]), 
                                                     self.data['Open time']]).reset_index(drop=True))
        
        print(f"回測完成！總交易次數: {len(self.trades)}")
        return self.calculate_performance()
    
    def calculate_performance(self) -> Dict:
        """計算績效指標"""
        if not self.equity_curve:
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
            profitable_trades = sum(1 for i in range(0, len(self.trades), 2) 
                                  if i + 1 < len(self.trades) and 
                                  self.trades[i+1]['capital_after'] > self.trades[i]['capital_after'])
            win_rate = profitable_trades / (len(self.trades) // 2) if len(self.trades) > 1 else 0
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
        if not self.equity_curve:
            print("沒有回測數據可繪製")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{self.symbol} 回測結果', fontsize=16)
        
        # 權益曲線
        axes[0, 0].plot(self.equity_curve.index, self.equity_curve.values, linewidth=2)
        axes[0, 0].set_title('投資組合價值變化')
        axes[0, 0].set_ylabel('投資組合價值')
        axes[0, 0].grid(True)
        
        # 收益率
        returns = self.equity_curve.pct_change().dropna()
        axes[0, 1].plot(returns.index, returns.values, alpha=0.7)
        axes[0, 1].set_title('收益率變化')
        axes[0, 1].set_ylabel('收益率')
        axes[0, 1].grid(True)
        
        # 回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        axes[1, 0].fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        axes[1, 0].plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        axes[1, 0].set_title('回撤分析')
        axes[1, 0].set_ylabel('回撤')
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
            axes[1, 1].plot(self.data['Open time'], self.data['Close'], alpha=0.7, label='價格')
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
        print(f"{self.symbol} 回測摘要")
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
    # 創建回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,  # 初始資金 $10,000
        commission_rate=0.001,  # 手續費 0.1%
        symbol='BTCUSDT'
    )
    
    # 載入數據（假設有數據文件）
    # backtest.load_data('btcusdt_1m.csv')
    
    # 生成示例信號（這裡需要根據你的策略生成）
    # signals = [1, 0, 0, -1, 0, 1, 0, -1, ...]  # 1=買入，0=不動作，-1=賣出
    
    # 執行回測
    # performance = backtest.run_backtest(signals)
    
    # 顯示結果
    # backtest.print_summary()
    # backtest.plot_results()
    
    print("回測平台已創建完成！")
    print("請使用 load_data() 載入數據，run_backtest() 執行回測")

if __name__ == "__main__":
    example_usage()
