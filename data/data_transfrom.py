import pandas as pd


# 計算 MACD
def get_macd(df, short_window=12, long_window=26, signal_window=9):
    df['EMA_short'] = df['Close'].ewm(span=short_window, adjust=False).mean()
    df['EMA_long'] = df['Close'].ewm(span=long_window, adjust=False).mean()
    df['MACD'] = df['EMA_short'] - df['EMA_long']
    df['Signal'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal']
    return df

# 計算 RSV
def get_rsv(df, rsv_window=9):
    df['Lowest_Low'] = df['Low'].rolling(window=rsv_window).min()
    df['Highest_High'] = df['High'].rolling(window=rsv_window).max()
    df['RSV'] = (df['Close'] - df['Lowest_Low']) / (df['Highest_High'] - df['Lowest_Low']) * 100
    return df

# 計算 MA
def get_ma(df, ma_window=10):
    df['MA'] = df['Close'].rolling(window=ma_window).mean()
    return df



coin_list = ['BTCUSDT', 'ETHUSDT' ,'BNBUSDT' ,'XRPUSDT' ,'SOLUSDT'] 
interval_list = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'] 

for coin in coin_list:
    for interval in interval_list:
        output_file = f"kline_with_indicators\\{coin.lower()}_{interval}.csv"
        
        df = pd.read_csv(f"kline_data\\{coin.lower()}_{interval}.csv")

        df = get_macd(df)
        df = get_rsv(df)
        df = get_ma(df)

        df = df.drop(columns=['EMA_short', 'EMA_long', 'Signal', 'Lowest_Low', 'Highest_High'])

        # 儲存結果到新的 CSV 檔案
        df.to_csv(output_file, index=False)
        print(f"結果已儲存到 kline_with_indicators\\{coin.lower()}_{interval}.csv")