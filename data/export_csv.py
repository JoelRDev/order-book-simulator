import argparse
import csv
from pathlib import Path
import pyarrow.parquet as pq

COLUMNS = [
    'event_time_ms',
    'update_id',
    'side',
    'level',
    'price_e8',
    'quantity_e8',
]

def export_csv(input_path: Path, output_path: Path) -> None:
    table = pq.read_table(input_path, columns=COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='') as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=COLUMNS,
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
        help="Input Parquet file"
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