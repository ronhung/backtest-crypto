import pandas as pd

def simple_moving_average_strategy(data: pd.DataFrame, short_window: int = 10, long_window: int = 30, k: int = 1) -> list:
    """
    簡單移動平均線策略
    
    Args:
        data: K線數據
        short_window: 短期移動平均線週期
        long_window: 長期移動平均線週期
    
    Returns:
        signals: 信號列表，1=買入，0=不動作，-1=賣出
    """
    signals = []
    
    # 計算移動平均線
    short_ma = data['Close'].rolling(window=short_window).mean()
    long_ma = data['Close'].rolling(window=long_window).mean()
    
    for i in range(len(data)):
        if i < long_window:
            signals.append(0)  # 數據不足，不動作
        else:
            # 金叉：短期MA上穿長期MA
            if short_ma.iloc[i] > long_ma.iloc[i] and short_ma.iloc[i-1] <= long_ma.iloc[i-1]:
                signals.append(k)  # 買入信號
            # 死叉：短期MA下穿長期MA
            elif short_ma.iloc[i] < long_ma.iloc[i] and short_ma.iloc[i-1] >= long_ma.iloc[i-1]:
                signals.append(-1*k)  # 賣出信號
            else:
                signals.append(0)  # 不動作
    
    return signals