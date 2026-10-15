from pathlib import Path
import time
import pyarrow as pa
import pyarrow.parquet as pq
from decimal import Decimal

BOOK_SCHEMA = pa.schema([
    ('recv_time_ns', pa.int64()),
    ('event_time_ms', pa.int64()),
    ('update_id', pa.int64()),
    ('side', pa.string()),
    ('level', pa.int8()),
    ('price_e8', pa.int64()),
    ('quantity_e8', pa.int64())
]).with_metadata({
    # Version on-disk format so that readers can reject incompatible/incorrect files
    b'format_version': b'2', # b changes to bytes value as opposed to unicode (expected by PyArrow). v2: added recv_time_ns
    b"symbol": b"BTCUSDT",
    b"depth": b"10",
    b"scale": b"100000000",
})

TRADE_SCHEMA = pa.schema([
    ('recv_time_ns', pa.int64()),
    ('event_time_ms', pa.int64()),
    ('trade_time_ms', pa.int64()),
    ('agg_trade_id', pa.int64()),
    ('price_e8', pa.int64()),
    ('quantity_e8', pa.int64()),
    ('normal_quantity_e8', pa.int64()), # Quantity excluding RPI order fills
    ('is_buyer_maker', pa.bool_()), # True -> seller was aggressor (trade hit the bid)
]).with_metadata({
    b'format_version': b'1',
    b"symbol": b"BTCUSDT",
    b"scale": b"100000000",
})

SCALE = Decimal('100000000')
OUTPUT = Path('market_data')

class ParquetBuffer:
    def __init__(self, name, schema, max_rows=20_000):
        self.name = name
        self.directory = OUTPUT / name
        self.schema = schema
        self.max_rows = max_rows
        self.rows = []

    def append(self, row):
        self.rows.append(row)

    def should_flush(self):
        return len(self.rows) >= self.max_rows

    def flush(self):
        if not self.rows:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pylist(self.rows, schema=self.schema)
        filename = self.directory / f'{self.name}-{time.time_ns()}.parquet'
        temporary = self.directory / f'.{filename.name}.tmp' # Hidden (. prefix), temporary (.tmp) file so readers only discover completed files
        pq.write_table(table, temporary, compression='zstd')
        temporary.replace(filename)
        self.rows.clear()

book_buffer = ParquetBuffer('book', BOOK_SCHEMA)
trade_buffer = ParquetBuffer('trades', TRADE_SCHEMA)

def record_book(book, update, recv_time_ns, depth=10):
    bids = sorted(book['bids'].items(), reverse=True)[:depth]
    asks = sorted(book['asks'].items())[:depth]
    for side, levels in (('bid', bids), ('ask', asks)):
        for level, (price, quantity) in enumerate(levels):
            book_buffer.append({
                'recv_time_ns': recv_time_ns,
                'event_time_ms': update["E"],
                "update_id": update["u"],
                "side": side,
                "level": level,
                "price_e8": int(price * SCALE),
                "quantity_e8": int(quantity * SCALE),
            })

def record_trade(trade, recv_time_ns):
    trade_buffer.append({
        'recv_time_ns': recv_time_ns,
        'event_time_ms': trade['E'],
        'trade_time_ms': trade['T'],
        'agg_trade_id': trade['a'],
        'price_e8': int(Decimal(trade['p']) * SCALE),
        'quantity_e8': int(Decimal(trade['q']) * SCALE),
        'normal_quantity_e8': int(Decimal(trade['nq']) * SCALE),
        'is_buyer_maker': trade['m'],
    })
