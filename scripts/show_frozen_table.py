"""Display existing frozen CSV values; no aggregation or scientific recomputation."""
import argparse
import csv
from pathlib import Path

TABLES = {'main': 'TABLE_1_DATA.csv', 'control': 'CONTROL_TABLE_DATA.csv', 'path': 'M3_RESULT_TABLE_DATA.csv'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', choices=TABLES, required=True)
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / 'studies/mlbd2026_wrong_label_organization/results' / TABLES[args.table]
    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.reader(handle))
    print('| ' + ' | '.join(rows[0]) + ' |')
    print('| ' + ' | '.join('---' for _ in rows[0]) + ' |')
    for row in rows[1:]:
        print('| ' + ' | '.join(cell.replace('|', '&#124;') for cell in row) + ' |')


if __name__ == '__main__':
    main()
