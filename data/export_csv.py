import argparse
import csv
from pathlib import Path
import pyarrow.compute as pc
import pyarrow.dataset as ds

def export_csv(input_path: Path, output_path: Path) -> None:
    # Accepts a single Parquet file or a directory of them (e.g. market_data/book)
    table = ds.dataset(input_path, format='parquet').to_table()
    # Stable sort: rows that share a recv_time_ns (one book update) keep their bid/ask level order
    table = table.take(pc.sort_indices(table, sort_keys=[('recv_time_ns', 'ascending')]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='') as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=table.column_names,
            lineterminator='\n'
        )
        writer.writeheader()
        writer.writerows(table.to_pylist())

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert order-book Parquet data to CSV"
    )
    parser.add_argument(
        'input',
        type=Path,
        help="Input Parquet file or directory"
    )
    parser.add_argument(
        'output',
        type=Path,
        help="Output CSV file"
    )
    arguments = parser.parse_args()
    export_csv(arguments.input, arguments.output)

if __name__ == '__main__':
    main()
