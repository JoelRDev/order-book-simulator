import websockets
import asyncio
import requests
import json
import time
from decimal import Decimal
from data.parquet_writer import record_book, record_trade, book_buffer, trade_buffer

symbol = 'btcusdt'
DEPTH_URL = f'wss://fstream.binance.com/public/ws/{symbol}@depth@100ms'
TRADE_URL = f'wss://fstream.binance.com/market/ws/{symbol}@aggTrade'

last_receive_ns = 0

def receive_time_ns():
    # Strictly increasing local clock shared by both streams, used to merge them in replay
    global last_receive_ns
    last_receive_ns = max(time.time_ns(), last_receive_ns + 1)
    return last_receive_ns

def snapshot(symbol):
    url = f'https://fapi.binance.com/fapi/v1/depth?symbol={symbol.upper()}&limit=1000'
    return requests.get(url).json()

def straddle(snapshot, ws_event):
    return ws_event['U'] <= snapshot['lastUpdateId'] <= ws_event['u']

def build_book(snapshot):
    bids: dict[Decimal, Decimal] = {}
    asks: dict[Decimal, Decimal] = {}
    for level in snapshot['bids']:
        price = Decimal(level[0])
        quantity = Decimal(level[1])
        bids[price] = quantity
    for level in snapshot['asks']:
        price = Decimal(level[0])
        quantity = Decimal(level[1])
        asks[price] = quantity
    book = {'bids': bids, 'asks': asks}
    return book

def update_book(book, update):
    for side, levels in (('bids', update['b']), ('asks', update['a'])):
        for price_value, quantity_value in levels:
            price = Decimal(price_value)
            quantity = Decimal(quantity_value)
            if quantity == 0:
                book[side].pop(price, None)
            else:
                book[side][price] = quantity

async def stream_depth():
    while True:
        async with websockets.connect(DEPTH_URL) as ws:
            initial = await asyncio.to_thread(snapshot, symbol)
            book = build_book(initial)
            synced = False
            previous_u = None
            async for message in ws:
                recv_time_ns = receive_time_ns()
                event = json.loads(message)
                if not synced:
                    if event['u'] < initial['lastUpdateId']:
                        continue
                    if not straddle(initial, event):
                        continue
                    synced = True
                elif event['pu'] != previous_u:
                    break
                update_book(book, event)
                record_book(book, event, recv_time_ns)
                if book_buffer.should_flush():
                    book_buffer.flush()
                previous_u = event['u']

async def stream_trades():
    previous_id = None
    while True:
        async with websockets.connect(TRADE_URL) as ws:
            async for message in ws:
                recv_time_ns = receive_time_ns()
                trade = json.loads(message)
                if previous_id is not None and trade['a'] != previous_id + 1:
                    print(f"Trade gap: expected {previous_id + 1}, got {trade['a']}")
                record_trade(trade, recv_time_ns)
                if trade_buffer.should_flush():
                    trade_buffer.flush()
                previous_id = trade['a']

async def main():
    try:
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(stream_depth())
            tasks.create_task(stream_trades())
    finally:
        book_buffer.flush()
        trade_buffer.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Collector stopped")