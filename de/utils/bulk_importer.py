"""Function to bulk copy to db"""

import csv
from de.utils.csv_downloader import download_csv


def print_first_few_lines(first=None):
    """Test function to print first few rows of data."""
    resp = download_csv()

    lines = resp.iter_lines(decode_unicode=True)

    reader = csv.DictReader(lines)

    print("欄位:", reader.fieldnames)
    print()

    for i, row in enumerate(reader, 1):
        if i > first:
            break
        print(f"第 {first} 筆:")
        for key, value in row.items():
            print(f"  {key}: {value}")
        print()
