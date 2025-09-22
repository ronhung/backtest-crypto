import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any


class PerformanceAnalyzer:
    """
    績效分析模組
    負責計算各種績效指標和生成分析報告
    """
    
    def __init__(self, equity_curve: pd.Series, closed_positions: List[Dict], 
                 initial_capital: float, trades: List[Dict], 
                 config: Any = None):
        """
        初始化績效分析器
        
        Args:
            equity_curve: 權益曲線數據
            closed_positions: 已完成的沖銷單列表
            initial_capital: 初始資金
            trades: 交易記錄列表
            config: 配置對象，用於自定義分析參數
        """
        self.equity_curve = equity_curve
        self.closed_positions = closed_positions
        self.initial_capital = initial_capital
        self.trades = trades
        if self.equity_curve[self.equity_curve < 0.1].first_valid_index() is not None:
            self.dead_time = self.equity_curve[self.equity_curve < 0.1].first_valid_index() - self.equity_curve.index[0]
        else:
            self.dead_time = self.equity_curve.index[-1] - self.equity_curve.index[0]
        self.dead_time_minutes = self.dead_time.total_seconds() / 60
        self.config = config
    
    @classmethod
    def from_engine(cls, engine, config: Any = None):
        """
        從回測引擎創建績效分析器
        
        Args:
            engine: BacktestEngine 實例
            config: 可選的配置對象
        
        Returns:
            PerformanceAnalyzer: 績效分析器實例
        """
        return cls(
            equity_curve=engine.equity_curve,
            closed_positions=engine.closed_positions,
            initial_capital=engine.initial_capital,
            trades=engine.trades,
            config=config
        )
    
    def calculate_performance(self) -> Dict:
        """計算績效指標"""
        if self.equity_curve is None or self.equity_curve.empty:
            return {}
        
        # 計算收益率
        total_return = (self.equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 計算日收益率
        daily_returns = self.equity_curve.pct_change().dropna()
        
        # 根據實際數據時間段計算年化收益率
        if len(self.equity_curve) > 1:
            # 計算實際時間跨度
            start_time = self.equity_curve.index[0]
            end_time = self.equity_curve.index[-1]
            time_span = end_time - start_time
            
            # 計算年化倍數（一年365天）
            days_in_year = 365
            total_days = time_span.total_seconds() / (24 * 3600)  # 轉換為天數
            
            if total_days > 0:
                annual_multiplier = days_in_year / total_days
                annual_return = (1 + total_return) ** annual_multiplier - 1
                
                # 年化波動率
                annual_volatility = daily_returns.std() * np.sqrt(365*24*60)
            else:
                annual_return = 0
                annual_volatility = 0
                annual_multiplier = 0
                total_days = 0
        else:
            annual_return = 0
            annual_volatility = 0
            annual_multiplier = 0
            total_days = 0
        
        # 夏普比率（假設無風險利率為0）
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤 (MDD)
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        mdd = drawdown.min()
        
        # 新的勝率計算：資金加權勝率 (profit) / (profit + loss)
        if self.closed_positions:
            profitable_amount = sum(pos['net_profit'] for pos in self.closed_positions if pos['net_profit'] > 0)
            unprofitable_amount = sum(-1* pos['net_profit'] for pos in self.closed_positions if pos['net_profit'] <= 0)
            total_positions = len(self.closed_positions)
            win_rate = profitable_amount / (profitable_amount + unprofitable_amount) if (profitable_amount + unprofitable_amount) > 0 else 0
            
            # 計算平均盈虧
            profits = [pos['net_profit'] for pos in self.closed_positions]
            costs = [pos['buy_price'] * pos['quantity'] for pos in self.closed_positions]
            avg_profit = np.mean(profits)
            avg_profit_percentage = sum(profits) / sum(costs) # 加權平均獲利比
            
            # 計算最大單筆盈虧
            max_profit = max([pos['net_profit'] for pos in self.closed_positions])
            max_loss = min([pos['net_profit'] for pos in self.closed_positions])
            
        else:
            win_rate = 0
            avg_profit = 0
            avg_profit_percentage = 0
            max_profit = 0
            max_loss = 0
            total_positions = 0
        
        performance = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': mdd,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'total_positions': total_positions,  # 新增：總沖銷單數
            'avg_profit': avg_profit,  # 新增：平均盈虧
            'avg_profit_percentage': avg_profit_percentage,  # 新增：平均盈虧百分比
            'max_profit': max_profit,  # 新增：最大單筆盈利
            'max_loss': max_loss,  # 新增：最大單筆虧損
            'final_capital': self.equity_curve.iloc[-1],
            'initial_capital': self.initial_capital,
            'time_span_days': total_days,  # 新增：時間跨度（天）
            'annual_multiplier': annual_multiplier,  # 新增：年化倍數
            'dead_time': self.dead_time,
            'dead_time_minutes': self.dead_time_minutes,
        }
        
        return performance
    
    def get_position_details(self) -> pd.DataFrame:
        """
        獲取沖銷單詳細信息
        
        Returns:
            DataFrame: 包含所有沖銷單的詳細信息
        """
        if not self.closed_positions:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.closed_positions)
        df['hold_duration'] = df['sell_timestamp'] - df['buy_timestamp']
        df['profit_percentage'] = df['net_profit'] / (df['buy_price'] * df['quantity'])
        
        return df
    
    def plot_results(self, symbol: str, positions: List[float], data: pd.DataFrame):
        """繪製回測結果圖表"""
        if self.equity_curve is None or self.equity_curve.empty:
            print("沒有回測數據可繪製")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{symbol} Backtest Results', fontsize=16)
        
        # 權益曲線
        axes[0, 0].plot(self.equity_curve.index, self.equity_curve.values, linewidth=2)
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Equity')
        axes[0, 0].grid(True)
        
        # 倉位變化
        axes[0, 1].plot(self.equity_curve.index, positions, alpha=0.7, color='orange')
        axes[0, 1].set_title('Position Size')
        axes[0, 1].set_ylabel('Position')
        axes[0, 1].grid(True)
        
        # 收益率
        returns = self.equity_curve.pct_change().dropna()
        axes[1, 0].plot(returns.index, returns.values, alpha=0.7)
        axes[1, 0].set_title('Returns')
        axes[1, 0].set_ylabel('Return')
        axes[1, 0].grid(True)
        
        # 交易記錄
        if self.trades:
            trade_df = pd.DataFrame(self.trades)
            buy_trades = trade_df[trade_df['action'] == 'BUY']
            sell_trades = trade_df[trade_df['action'] == 'SELL']
            
            axes[1, 1].scatter(buy_trades['timestamp'], buy_trades['price'], 
                              color='green', marker='^', s=50, label='Buy')
            axes[1, 1].scatter(sell_trades['timestamp'], sell_trades['price'], 
                              color='red', marker='v', s=50, label='Sell')
            axes[1, 1].plot(data['Open_time'], data['Close'], alpha=0.7, label='Price')
            axes[1, 1].set_title('Trades')
            axes[1, 1].set_ylabel('Price')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def print_summary(self, symbol: str):
        """打印回測摘要"""
        performance = self.calculate_performance()
        
        print("\n" + "="*50)
        print(f"{symbol} 回測摘要")
        print("="*50)
        print(f"初始資金: ${performance['initial_capital']:,.2f}")
        print(f"最終資金: ${performance['final_capital']:,.2f}")
        print(f"總收益率: {performance['total_return']:.2%}")
        print(f"年化收益率: {performance['annual_return']:.2%}")
        print(f"年化波動率: {performance['annual_volatility']:.2%}")
        print(f"夏普比率: {performance['sharpe_ratio']:.3f}")
        print(f"最大回撤: {performance['max_drawdown']:.2%}")
        print(f"勝率: {performance['win_rate']:.2%}")
        print(f"總交易次數: {performance['total_trades']}")
        print(f"總沖銷單數: {performance['total_positions']}")
        print(f"平均盈虧: ${performance['avg_profit']:.2f}")
        print(f"平均盈虧百分比: {performance['avg_profit_percentage']:.2%}")
        print(f"最大單筆盈利: ${performance['max_profit']:.2f}")
        print(f"最大單筆虧損: ${performance['max_loss']:.2f}")
        print(f"時間跨度: {performance['time_span_days']:.1f} 天")
        print(f"破產時長: {performance['dead_time_minutes']:.1f} 分鐘")
        print("="*50)
