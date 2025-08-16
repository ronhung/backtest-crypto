import requests 
import pandas as pd 
import time 
from datetime import datetime, timedelta 
INTERVAL_IN_SECONDS = { 
    '1m': 60, 
    '5m': 300, 
    '15m': 900, 
    '30m': 1800, 
    '1h': 3600, 
    '4h': 14400, 
    '1d': 86400 
} 
 
def get_binance_klines(symbol='BTCUSDT', interval='1m', limit=1000, start_time=None, end_time=None): 
    url = 'https://api.binance.com/api/v3/klines' 
    params = { 
        'symbol': symbol, 
        'interval': interval, 
        'limit': limit 
    } 
 
    if start_time: 
        params['startTime'] = int(start_time) 
    if end_time: 
        params['endTime'] = int(end_time) 
 
    response = requests.get(url, params=params) 
    if response.status_code != 200: 
        print(f"Error {response.status_code}: {response.text}") 
        return pd.DataFrame() 
     
    data = response.json() 
    df = pd.DataFrame(data, columns=[ 
        'Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 
        'Close time', 'Quote asset volume', 'Number of trades', 
        'Taker buy base volume', 'Taker buy quote volume', 'Ignore' 
    ]) 
     
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms') 
    df['Close time'] = pd.to_datetime(df['Close time'], unit='ms') 
 
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']: 
        df[col] = df[col].astype(float) 
 
    return df 
 
def download_all_binance(symbol='BTCUSDT', interval= '1m',  start_date='2020-01-01', end_date=None, output_csv='btc_1min.csv'): 
    if end_date is None: 
        end_date = datetime.now().strftime('%Y-%m-%d') 
 
    start_time = pd.to_datetime(start_date) 
    end_time = pd.to_datetime(end_date) 
    seconds_per_interval = INTERVAL_IN_SECONDS.get(interval) 
    delta = timedelta(seconds=seconds_per_interval * 1000) 
 
    all_data = [] 
 
    print(f"ð Downloading {symbol} {interval} data from {start_date} to {end_date}...") 
    program_start = time.time()
 
    while start_time < end_time: 
        start_ts = int(start_time.timestamp() * 1000) 
        end_ts = int((start_time + delta).timestamp() * 1000) 
         
        df = get_binance_klines(symbol=symbol, interval=interval, limit=1000, start_time=start_ts, end_time=end_ts) 
        if df.empty: 
            print(f"No data returned at {start_time}") 
            break 
         
        all_data.append(df) 
        print(f"Downloaded: {df.iloc[0]['Open time']} to {df.iloc[-1]['Open time']}") 
 
        start_time += delta 
        time.sleep(0.4) 
 
    result = pd.concat(all_data, ignore_index=True) 
    result.to_csv(output_csv, index=False) 
 
    program_end = time.time()
    elapsed = program_end - program_start 
    minutes = elapsed // 60 
    seconds = elapsed % 60 
 
    print(f"\nð All data saved to {output_csv}, total rows: {len(result)}") 
    print(f"Total time: {int(minutes)} minutes {int(seconds)} seconds") 
 
coin_list = ['BTCUSDT', 'ETHUSDT' ,'BNBUSDT' ,'XRPUSDT' ,'SOLUSDT'] 
interval_list = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'] 
for coin in coin_list: 
    for interval in interval_list: 
             
        output_file = f"{coin.lower()}_{interval}.csv" 
        download_all_binance( 
            symbol=coin, 
            interval=interval,  
            start_date='2021-01-01',  
            end_date='2025-07-29',  
            output_csv=output_file 
        )