import pandas as pd

# 讀取 CSV 檔案
df = pd.read_csv("rsi_grid_search_results_sma.csv")

# 依照 score 由高到低排序
df_sorted = df.sort_values(by="score", ascending=False)

# 輸出排序後的結果（可以選擇存回檔案）
print(df_sorted)
# 或存成新的 CSV
df_sorted.to_csv("rsi_grid_search_results_sma.csv", index=False)