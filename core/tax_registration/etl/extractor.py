"""CSV 資料擷取模組"""

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import Generator


class CSVExtractor:
    """負責從遠端 URL 下載 CSV 並分批讀取"""

    def __init__(self, url: str):
        self.url = url

    def fetch_chunks(self, chunk_size: int) -> Generator[pd.DataFrame, None, None]:
        """
        下載 CSV 並以 generator 方式分批返回 DataFrame。

        """
        session = self._create_session()

        response = session.get(self.url, stream=True, timeout=60)
        response.raise_for_status()

        return pd.read_csv(
            response.raw,
            encoding="utf-8",
            chunksize=chunk_size,
            dtype=str,
            na_values=["", "NULL", "null", "NA", "N/A"],
            keep_default_na=False,
        )

    def _create_session(self) -> requests.Session:
        """建立帶重試機制的 Session"""
        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session
