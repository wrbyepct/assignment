"""資料載入模組"""

import csv
from io import StringIO
from typing import List

import pandas as pd
from django.db import connection, transaction

from core.tax_registration.models import BusinessIndustry


class BulkLoader:
    """負責批次匯入資料到 PostgreSQL"""

    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size

    def insert(self, df: pd.DataFrame) -> int:
        """
        匯入資料到資料庫

        """
        with transaction.atomic():
            # 準備並匯入主表
            tax_records = self._prepare_tax_records(df)
            count = self._bulk_insert_copy(tax_records)

            # 匯入行業資料
            industry_records = self._prepare_industry_records(df)
            if industry_records:
                self._bulk_insert_industries(industry_records)

            return count

    def _prepare_tax_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """準備 TaxRegistration 記錄"""
        return df[
            [
                "統一編號",
                "總機構統一編號",
                "營業人名稱",
                "營業地址",
                "資本額",
                "設立日期",
                "組織別名稱",
                "使用統一發票",
            ]
        ].copy()

    def _bulk_insert_copy(self, df: pd.DataFrame) -> int:
        """使用 PostgreSQL COPY 批次匯入"""
        buffer = StringIO()

        df_ordered = df.copy()

        # 處理 NULL 值
        df_ordered["總機構統一編號"] = df_ordered["總機構統一編號"].replace(
            {None: "\\N", "": "\\N"}
        )

        # 寫入 CSV
        df_ordered.to_csv(
            buffer,
            index=False,
            header=False,
            sep="\t",
            na_rep="\\N",
            quoting=csv.QUOTE_MINIMAL,
            escapechar="\\",
            doublequote=False,
        )
        buffer.seek(0)

        # COPY 匯入
        with connection.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "tax_registration",
                sep="\t",
                null="\\N",
                columns=(
                    "ban",
                    "headquarters_ban",
                    "business_name",
                    "business_address",
                    "capital_amount",
                    "business_setup_date",
                    "business_type",
                    "is_use_invoice",
                ),
            )

        return len(df_ordered)

    def _prepare_industry_records(self, df: pd.DataFrame) -> List[BusinessIndustry]:
        """準備行業記錄 for bulk insert"""
        records = []

        for _, row in df.iterrows():
            ban = row["統一編號"]

            # 處理最多 4 組行業, 如有未來有需要再添加
            for i, suffix in enumerate(["", "1", "2", "3"], 1):
                code_col = f"行業代號{suffix}" if suffix else "行業代號"
                name_col = f"名稱{suffix}" if suffix else "名稱"

                if code_col in row and row[code_col]:
                    records.append(
                        BusinessIndustry(
                            business_id=ban,
                            industry_code=row[code_col],
                            industry_name=row.get(name_col, ""),
                            order=i,
                        )
                    )

        return records

    def _bulk_insert_industries(self, records: List[BusinessIndustry]):
        """批次匯入行業資料"""
        BusinessIndustry.objects.bulk_create(
            records,
            batch_size=self.batch_size,
            ignore_conflicts=True,
        )
