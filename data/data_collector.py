import websockets
import asyncio
import requests
import json

symbol = 'btcusdt'

def snapshot(symbol):
    url = f'https://fapi.binance.com/fapi/v1/depth?symbol={symbol.upper()}&limit=1000'
    return requests.get(url).json()

async def diff_stream(symbol):
    url = f'wss://fstream.binance.com/ws/{symbol}@depth'
    async with websockets.connect(url) as ws:
        async for message in ws:
            event = json.loads(message)
            yield event

def straddle(snapshot, ws_event):
    if ws_event['U'] <= snapshot['lastUpdateId'] <= ws_event['u']:
        return True

async def main():
    initial = snapshot(symbol)
    try:
        async with asyncio.timeout(5):
            async for event in diff_stream(symbol):
                if straddle(initial, event):
                    break
            else:
                return
    except TimeoutError:
        return

if __name__ == "__main__":
    asyncio.run(main())