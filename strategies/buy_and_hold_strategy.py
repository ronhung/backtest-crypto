import pandas as pd

def buy_and_hold_strategy(data: pd.DataFrame) -> list:
    """
    買入並持有策略：開頭買入，最後賣出
    Returns: 信號列表（第0根=1，最後一根=-1，其餘=0）
    """
    n = len(data)
    if n == 0:
        return []
    signals = [0] * n
    signals[0] = 1
    signals[-1] = -1
    return signals
