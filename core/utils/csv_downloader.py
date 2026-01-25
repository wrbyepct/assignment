"""Utility functions to download csv."""

import requests
import csv


def download_csv():
    """Return ready-to-download reader of csv."""
    url = "https://eip.fia.gov.tw/data/BGMOPEN1.csv"
    resp = requests.get(
        url=url, stream=True, timeout=300
    )  # Stream response is memory-effcient
    resp.encoding = "utf-8"  # deal with all language characters

    lines = resp.iter_lines(decode_unicode=True)
    reader = csv.DictReader(lines)
    return reader
