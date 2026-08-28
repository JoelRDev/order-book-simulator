import pandas as pd
import pyarrow.dataset as ds

dataset = ds.data('market_data', format='parquet')
table = dataset.to_table(
    filter=ds.field('event_time_ms') >= 1_700_000_000_000
)
df = table.to_pandas()
print(df.info())
print(df.head())
print(df.describe())