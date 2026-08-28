from pathlib import Path
import time
import pyarrow as pa
import pyarrow.parquet as pq
from decimal import Decimal

SCHEMA = pa.schema([
    ('event_time_ms', pa.int64()),
    ('update_id', pa.int64()),
    ('side', pa.string()),
    ('level', pa.int8()),
    ('price_e8', pa.int64()),
    ('quantity_e8', pa.int64())
]).with_metadata({
    # Version on-disk format so that readers can reject incompatible/incorrect files
    b'format_version': b'1', # b changes to bytes value as opposed to unicode (expected by PyArrow)
    b"symbol": b"BTCUSDT",
    b"depth": b"10",
    b"scale": b"100000000",
})

SCALE = Decimal('100000000')

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
                "price_e8": int(price * SCALE),
                "quantity_e8": int(quantity * SCALE),
            })

def flush():
    if not rows:
        return
    output = Path('market_data')
    output.mkdir(exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    filename = output / f'book-{time.time_ns()}.parquet'
    pq.write_table(table, filename, compression='zstd')
    rows.clear()

def should_flush():
    return len(rows) >= 20_000