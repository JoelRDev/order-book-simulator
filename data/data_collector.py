import websockets
import asyncio
import requests
import json

symbol = 'btcusdt'

def snapshot(symbol):
    url = f'https://fapi.binance.com/fapi/v1/depth?symbol={symbol.upper()}&limit=1000'
    return requests.get(url).json()

def straddle(snapshot, ws_event):
    return ws_event['U'] <= snapshot['lastUpdateId'] <= ws_event['u']

async def main():
    url = f'wss://fstream.binance.com/ws/{symbol}@depth'
    async with websockets.connect(url) as ws:
        initial = await asyncio.to_thread(snapshot, symbol)
        async with asyncio.timeout(5):
            async for message in ws:
                event = json.loads(message)
                if event['u'] < initial['lastUpdateId']:
                    continue
                if straddle(initial, event):
                    return initial, event
                raise RuntimeError('Straddling failed')

if __name__ == "__main__":
    asyncio.run(main())