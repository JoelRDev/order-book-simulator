import websockets
import asyncio
import requests

ws_stream = 'wss://fstream.binance.com/public/ws/!bookTicker'
api_url = 'https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=1000'

res = requests.get(api_url).json()
bids = res['bids']
print(bids)