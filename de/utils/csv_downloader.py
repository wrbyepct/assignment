"""Utility functions to download csv."""

import requests


def download_csv():
    """Return ready-to-download stream response of csv."""
    url = "https://eip.fia.gov.tw/data/BGMOPEN1.csv"
    resp = requests.get(url=url, stream=True)  # Stream response is memory-effcient
    resp.encoding = "utf-8"  # deal with all language characters

    return resp
