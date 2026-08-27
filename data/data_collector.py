import websockets
import asyncio
import requests
import json
from decimal import Decimal

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
        price = level[0]
        quantity = level[1]
        bids[price] = quantity
    for level in snapshot['asks']:
        price = level[0]
        quantity = level[1]
        asks[price] = quantity
    book = {'bids': bids, 'asks': asks}
    return book

async def main():
    url = f'wss://fstream.binance.com/ws/{symbol}@depth'
    async with websockets.connect(url) as ws:
        initial = await asyncio.to_thread(snapshot, symbol)
        async with asyncio.timeout(5): # Buffer events for 5 seconds before checking them
            async for message in ws:
                event = json.loads(message)
                if event['u'] < initial['lastUpdateId']:
                    continue
                if not straddle(initial, event):
                    raise RuntimeError('Straddling failed')
                book = build_book(initial)
                return initial, event

if __name__ == "__main__":
    asyncio.run(main())