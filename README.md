# Order Book Simulator
This project is intended to collect order book data and use it for backtesting strategies with L2 order book data

## Notes
- To run the data collector use the command: `uv run python -m data.data_collector`

## Limitations
- Order book only updates every 100ms (changes are aggregated)
- Current temporary implementation converts Parquet file to CSV before processing in C++, this is a separation of concerns and will be changed in the future