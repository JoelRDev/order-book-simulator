import pandas as pd
import pyarrow.dataset as ds

dataset = ds.dataset('market_data', format='parquet')
table = dataset.to_table(
    filter=ds.field('event_time_ms') >= 1_700_000_000_000
)

df = table.to_pandas()

print(df.info())
print(df.head())
print(df.describe())

# TODO: Add outputs to assertions to clarify error source, output # of snapshots evaluated at end

assert table.num_rows % 20 == 0
assert table['price_e8'].null_count == 0
assert table['quantity_e8'].null_count == 0
assert set(table['side'].to_pylist()) == {'bid', 'ask'}

for update_id, snapshot in df.groupby('update_id'):
    bids = snapshot[snapshot['side'] == 'bid'].sort_values('level')
    asks = snapshot[snapshot['side'] == 'ask'].sort_values('level')

    assert len(bids) == 10
    assert len(asks) == 10

    best_bid = bids.iloc[0]['price_e8']
    best_ask = asks.iloc[0]['price_e8']

    assert best_bid < best_ask