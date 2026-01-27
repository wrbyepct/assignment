"""資料轉換與驗證模組"""

import pandas as pd
from typing import Tuple, List


class TaxDataTransformer:
    """負責清理與驗證稅籍資料"""

    def process(
        self, df: pd.DataFrame, chunk_num: int
    ) -> Tuple[pd.DataFrame, List[dict]]:
        """
        清理並驗證資料。

        """
        errors = []

        # 1. 移除完全空白的行
        df = df.dropna(how="all")

        # 2. 驗證必填欄位
        required_cols = ["統一編號", "營業人名稱"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"缺少必要欄位: {missing_cols}")

        # 3. 清理統一編號
        df["統一編號"] = df["統一編號"].fillna("").str.strip()

        # 4. 驗證統一編號格式
        invalid_mask = (df["統一編號"].str.len() != 8) | (~df["統一編號"].str.isdigit())

        # 記錄格式錯誤
        for _, row in df[invalid_mask].iterrows():
            errors.append(
                {
                    "type": "INVALID_BAN",
                    "batch": chunk_num,
                    "ban": row["統一編號"],
                    "message": f"統一編號格式錯誤: {row['統一編號']}",
                }
            )

        df = df[~invalid_mask].copy()

        # 5. 處理重複資料
        duplicates_mask = df.duplicated(subset=["統一編號"], keep="first")
        duplicates_count = duplicates_mask.sum()

        if duplicates_count > 0:
            for idx in df[duplicates_mask].index:
                errors.append(
                    {
                        "type": "DUPLICATE",
                        "batch": chunk_num,
                        "ban": df.loc[idx, "統一編號"],
                        "message": f"重複的統一編號: {df.loc[idx, '統一編號']}",
                    }
                )

        df = df[~duplicates_mask].copy()

        # 6. 清理其他欄位
        df = self._clean_fields(df)

        return df, errors

    def _clean_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理各欄位"""
        # 總機構統一編號
        df["總機構統一編號"] = df["總機構統一編號"].fillna("").str.strip()
        df.loc[df["總機構統一編號"] == "", "總機構統一編號"] = None

        # 公司名稱
        df["營業人名稱"] = df["營業人名稱"].fillna("").str.strip()

        # 地址
        df["營業地址"] = df["營業地址"].fillna("").str.strip()

        # 設立日期
        df["設立日期"] = df["設立日期"].fillna("").str.strip()

        # 組織別
        df["組織別名稱"] = df["組織別名稱"].fillna("").str.strip()

        # 資本額
        df["資本額"] = (
            pd.to_numeric(
                df["資本額"].fillna("0").str.replace(",", ""),
                errors="coerce",
            )
            .fillna(0)
            .astype("int64")
        )

        # 使用統一發票
        df["使用統一發票"] = (
            df["使用統一發票"]
            .map({"Y": True, "y": True, "N": False, "n": False})
            .fillna(False)
        )

        # 行業代號與名稱
        for i in ["", "1", "2", "3"]:
            code_col = f"行業代號{i}" if i else "行業代號"
            name_col = f"名稱{i}" if i else "名稱"

            if code_col in df.columns:
                df[code_col] = df[code_col].fillna("").str.strip()
            if name_col in df.columns:
                df[name_col] = df[name_col].fillna("").str.strip()

        return df
