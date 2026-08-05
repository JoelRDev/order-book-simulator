import websockets
import asyncio
import requests
import json

symbol = 'btcusdt'

def snapshot(symbol):
    symbol.upper()
    url = f'https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=1000'
    res = requests.get(url).json()

async def diff_stream(symbol):
    url = f'wss://fstream.binance.com/ws/{symbol}@depth'
    async with websockets.connect(url) as ws:
        async for message in ws:
            event = json.loads(message)
            yield event

async def main():
    pass