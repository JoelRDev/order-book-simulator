import pandas as pd

df = pd.read_parquet('market_data')
print(df.info())
print(df.head())
print(df.describe())