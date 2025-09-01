import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
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
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        # 新增：沖銷單追蹤
        self.open_positions = []  # 未平倉的買入記錄
        self.closed_positions = []  # 已完成的沖銷單
        
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
    
    def _process_sell_trade(self, sell_quantity: float, sell_price: float, timestamp, commission: float):
        """
        處理賣出交易，計算沖銷單盈虧
        
        Args:
            sell_quantity: 賣出數量
            sell_price: 賣出價格
            timestamp: 賣出時間
            commission: 手續費
        """
        remaining_sell_quantity = sell_quantity
        closed_positions_in_trade = []
        
        # 按照FIFO原則處理賣出
        while remaining_sell_quantity > 0 and self.open_positions:
            # 取最早買入的倉位
            open_position = self.open_positions[0]
            
            # 計算本次沖銷的數量
            close_quantity = min(remaining_sell_quantity, open_position['remaining_quantity'])
            
            # 計算盈虧
            buy_price = open_position['price']
            buy_commission = open_position['commission']
            sell_commission = commission * (close_quantity / sell_quantity)  # 按比例分配手續費
            
            # 計算淨盈虧（扣除買賣手續費）
            gross_profit = (sell_price - buy_price) * close_quantity
            net_profit = gross_profit - buy_commission - sell_commission
            
            # 創建沖銷單記錄
            closed_position = {
                'buy_timestamp': open_position['timestamp'],
                'sell_timestamp': timestamp,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'quantity': close_quantity,
                'buy_commission': buy_commission,
                'sell_commission': sell_commission,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'is_profitable': net_profit > 0
            }
            
            closed_positions_in_trade.append(closed_position)
            self.closed_positions.append(closed_position)
            
            # 更新未平倉數量
            if close_quantity == open_position['remaining_quantity']:
                # 完全平倉，移除該記錄
                self.open_positions.pop(0)
            else:
                # 部分平倉，更新剩餘數量
                open_position['remaining_quantity'] -= close_quantity
            
            remaining_sell_quantity -= close_quantity
        
        return closed_positions_in_trade
    
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
        current_position = 0.0  # 當前倉位
        
        self.portfolio_values = [current_capital]
        self.positions = [current_position_ratio]
        self.trades = []
        
        # 重置沖銷單追蹤
        self.open_positions = []
        self.closed_positions = []
        
        print("開始執行回測...")
        
        for i, (signal, row) in enumerate(zip(signals, self.data.itertuples())):
            current_price = row.Close
            
            # 根據信號執行交易
            if signal > 0:  # 買入信號
                # 計算要買入的倉位比例
                target_position_ratio = min(1.0, current_position_ratio + signal)
                current_assest = current_capital + current_position * current_price
                real_position_ratio = (current_position * current_price) / current_assest
                if target_position_ratio >  real_position_ratio:  # 目標倉位比大於目前真實倉位比
                    # 計算需要投入的資金，以達到目標倉位比例 (position_ratio累加即為交易後總倉位比例)
                    current_assest = current_capital + current_position * current_price
                    target_position_value = target_position_ratio * current_assest
                    current_position_value = current_position * current_price
                    additional_capital_needed = target_position_value - current_position_value

                    
                    if additional_capital_needed <= current_capital:
                        # 執行買入
                        commission = additional_capital_needed * self.commission_rate
                        actual_investment = (additional_capital_needed - commission) / current_price
                        
                        # 計算新的倉位比例和價值
                        actual_investment_ratio = target_position_ratio - current_position_ratio
                        total_position = current_position + actual_investment
                        current_position_ratio = target_position_ratio
                        current_position = total_position
                        current_capital -= (additional_capital_needed + commission)
                        
                        # 記錄交易
                        trade = {
                            'timestamp': row.Open_time,
                            'action': 'BUY',
                            'price': current_price,
                            'position_ratio': actual_investment_ratio,
                            'amount': actual_investment,
                            'commission': commission,
                            'capital_before': current_capital + additional_capital_needed,
                            'capital_after': current_capital
                        }
                        self.trades.append(trade)
                        
                        # 追蹤買入倉位（用於沖銷單計算）
                        self.open_positions.append({
                            'timestamp': row.Open_time,
                            'price': current_price,
                            'quantity': actual_investment,
                            'commission': commission,
                            'remaining_quantity': actual_investment
                        })
                
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
                    closed_positions = self._process_sell_trade(sell_position, current_price, row.Open_time, commission)
                    
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
                        'closed_positions': closed_positions  # 新增：沖銷單信息
                    }
                    self.trades.append(trade)
            
            # 更新投資組合價值
            if current_position_ratio > 0:
                # 有倉位，價值隨價格變動
                portfolio_value = current_capital + current_position * current_price
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
        print(f"總沖銷單數: {len(self.closed_positions)}")
        return self.calculate_performance()
    
    def calculate_performance(self) -> Dict:
        """計算績效指標"""
        if self.equity_curve is None or self.equity_curve.empty:
            return {}
        
        # 計算收益率
        total_return = (self.equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 計算日收益率
        kline_timespan = self.equity_curve.index[1] - self.equity_curve.index[0]
        kline_days = kline_timespan.total_seconds() / (24 * 3600)
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
                annual_volatility = daily_returns.std() *  np.sqrt(365*24*60)
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
            'annual_multiplier': annual_multiplier  # 新增：年化倍數
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
    
    def plot_results(self):
        """繪製回測結果圖表"""
        if self.equity_curve is None or self.equity_curve.empty:
            print("沒有回測數據可繪製")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{self.symbol} Backtest Results', fontsize=16)
        
        # 權益曲線
        axes[0, 0].plot(self.equity_curve.index, self.equity_curve.values, linewidth=2)
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Equity')
        axes[0, 0].grid(True)
        
        # 倉位變化
        axes[0, 1].plot(self.equity_curve.index, self.positions, alpha=0.7, color='orange')
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
            axes[1, 1].plot(self.data['Open_time'], self.data['Close'], alpha=0.7, label='Price')
            axes[1, 1].set_title('Trades')
            axes[1, 1].set_ylabel('Price')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def print_summary(self):
        """打印回測摘要"""
        performance = self.calculate_performance()
        
        print("\n" + "="*60)
        print(f"{self.symbol} 部分倉位回測摘要")
        print("="*60)
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終資金: ${performance['final_capital']:,.2f}")
        print(f"總收益率: {performance['total_return']:.2%}")
        print(f"年化收益率: {performance['annual_return']:.2%}")
        print(f"年化波動率: {performance['annual_volatility']:.2%}")
        print(f"夏普比率: {performance['sharpe_ratio']:.3f}")
        print(f"最大回撤: {performance['max_drawdown']:.2%}")
        print(f"勝率 (等權): {performance['win_rate']:.2%}")
        print(f"總交易次數: {performance['total_trades']}")
        print(f"總沖銷單數: {performance['total_positions']}")
        print(f"平均盈虧: ${performance['avg_profit']:.2f}")
        print(f"平均盈虧百分比: {performance['avg_profit_percentage']:.2%}")
        # 根據實際情況顯示最大單筆盈利
        if performance['max_profit'] > 0:
            print(f"最大單筆盈利: ${performance['max_profit']:.2f}")
        else:
            print("最大單筆盈利: 無盈利交易")
        
        # 根據實際情況顯示最大單筆虧損
        if performance['max_loss'] < 0:
            print(f"最大單筆虧損: ${performance['max_loss']:.2f}")
        else:
            print("最大單筆虧損: 無虧損交易")
        print("="*60)
    
    def print_position_details(self):
        """打印沖銷單詳細信息"""
        if not self.closed_positions:
            print("沒有沖銷單記錄")
            return
        
        df = self.get_position_details()
        
        print("\n" + "="*80)
        print("沖銷單詳細信息")
        print("="*80)
        print(f"總沖銷單數: {len(df)}")
        print(f"盈利單數: {len(df[df['is_profitable']])}")
        print(f"虧損單數: {len(df[~df['is_profitable']])}")
        print(f"勝率: {len(df[df['is_profitable']]) / len(df):.2%}")
        
        print("\n前10筆沖銷單:")
        display_cols = ['buy_timestamp', 'sell_timestamp', 'buy_price', 'sell_price', 
                       'quantity', 'net_profit', 'is_profitable']
        print(df[display_cols].head(10).to_string(index=False))
        
        print("\n統計摘要:")
        print(f"平均持倉時間: {df['hold_duration'].mean()}")
        print(f"平均盈虧: ${df['net_profit'].mean():.2f}")
        print(f"平均盈虧百分比: {df['profit_percentage'].mean():.2%}")
        # 根據實際情況顯示最大盈利
        max_profit = df['net_profit'].max()
        if max_profit > 0:
            print(f"最大盈利: ${max_profit:.2f}")
        else:
            print("最大盈利: 無盈利交易")
        
        # 根據實際情況顯示最大虧損
        max_loss = df['net_profit'].min()
        if max_loss < 0:
            print(f"最大虧損: ${max_loss:.2f}")
        else:
            print("最大虧損: 無虧損交易")

# 示例使用
def example_usage():
    """示例使用方法"""
    # 創建部分倉位回測引擎
    backtest = BacktestEngine(
        initial_capital=10000,  # 初始資金 $10,000
        commission_rate=0.001,  # 手續費 0.1%
        symbol='BTCUSDT'
    )
    
    print("部分倉位回測引擎已創建完成！")
    print("支持小數信號，如0.1表示買入10%倉位，-0.1表示賣出10%倉位")
    print("新增功能：等權勝率計算和沖銷單追蹤")

if __name__ == "__main__":
    example_usage()
