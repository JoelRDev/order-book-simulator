import websockets
import asyncio
import requests
import json
from decimal import Decimal
from data.parquet_writer import record_book, flush, should_flush

symbol = 'btcusdt'

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

async def main():
    url = f'wss://fstream.binance.com/ws/{symbol}@depth'
    try:
        while True:
            async with websockets.connect(url) as ws:
                initial = await asyncio.to_thread(snapshot, symbol)
                book = build_book(initial)
                synced = False
                previous_u = None
                async for message in ws:
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
                    record_book(book, event)
                    if should_flush():
                        flush()
                    previous_u = event['u']
    finally:
        flush()

if __name__ == "__main__":
    asyncio.run(main())