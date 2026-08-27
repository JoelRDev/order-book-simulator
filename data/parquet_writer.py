from pathlib import Path
import time
import pyarrow as pa
import pyarrow.parquet as pq

rows = []

def record_book(book, update, depth=10):
    bids = sorted(book['bids'].items(), reverse=True)[:depth]
    asks = sorted(book['asks'].items())[:depth]
    for side, levels in (('bid', bids), ('ask', asks)):
        for level, (price, quantity) in enumerate(levels):
            rows.append({
                'event_time_ms': update["E"],
                "update_id": update["u"],
                "side": side,
                "level": level,
                "price": float(price),
                "quantity": float(quantity),
            })

def flush():
    if not rows:
        return
    output = Path('market_data')
    output.mkdir(exist_ok=True)
    table = pa.Table.from_pylist(rows)
    filename = output / f'book-{time.time_ns()}.parquet'
    pq.write_table(table, filename, compression='zstd')
    rows.clear()