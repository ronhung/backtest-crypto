import pandas as pd

def bollinger_bands_strategy(data: pd.DataFrame, window: int = 20, num_std: float = 2) -> list:
    """
    布林帶策略
    
    Args:
        data: K線數據
        window: 移動平均線週期
        num_std: 標準差倍數
    
    Returns:
        signals: 信號列表
    """
    signals = []
    
    # 計算布林帶
    ma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper_band = ma + (std * num_std)
    lower_band = ma - (std * num_std)
    
    for i in range(len(data)):
        if i < window:
            signals.append(0)
        else:
            current_price = data['Close'].iloc[i]
            current_upper = upper_band.iloc[i]
            current_lower = lower_band.iloc[i]
            
            # 價格觸及下軌，可能反彈
            if current_price <= current_lower:
                signals.append(1)  # 買入信號
            # 價格觸及上軌，可能回落
            elif current_price >= current_upper:
                signals.append(-1)  # 賣出信號
            else:
                signals.append(0)
    
    return signals