import pandas as pd

def rsi_strategy(data: pd.DataFrame, rsi_period: int = 14, oversold: float = 30, overbought: float = 70) -> list:
    """
    RSI策略
    
    Args:
        data: K線數據
        rsi_period: RSI計算週期
        oversold: 超賣閾值
        overbought: 超買閾值
    
    Returns:
        signals: 信號列表
    """
    signals = []
    
    # 計算RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    for i in range(len(data)):
        if i < rsi_period:
            signals.append(0)
        else:
            current_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1] if i > 0 else 50
            
            # RSI從超賣區回升
            if prev_rsi < oversold and current_rsi >= oversold:
                signals.append(1)  # 買入信號
            # RSI從超買區回落
            elif prev_rsi > overbought and current_rsi <= overbought:
                signals.append(-1)  # 賣出信號
            else:
                signals.append(0)
    
    return signals