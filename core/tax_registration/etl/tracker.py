"""ETL 進度追蹤與狀態管理模組"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from django.utils import timezone

from core.tax_registration.models import (
    ETLJobRun,
    DataImportError,
    ImportProgress,
)


logger = logging.getLogger("tax_registration.etl")


class ETLTracker:
    """負責 ETL 執行狀態、進度追蹤、錯誤記錄"""

    def __init__(
        self,
        batch_size: int,
        chunk_size: int,
        data_source_url: str,
        dry_run: bool = False,
    ):
        self.batch_size = batch_size
        self.chunk_size = chunk_size
        self.data_source_url = data_source_url
        self.dry_run = dry_run

        self.job_run: Optional[ETLJobRun] = None
        self.start_time: Optional[datetime] = None
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "duplicates": 0,
            "skipped": 0,
        }

    def start(self) -> ETLJobRun:
        """創建 ETL Job 並記錄開始"""
        self.start_time = timezone.now()
        self.job_run = ETLJobRun.objects.create(
            status="running",
            batch_size=self.batch_size,
            chunk_size=self.chunk_size,
            data_source_url=self.data_source_url,
        )

        logger.info(
            "ETL 任務開始",
            extra={
                "event": "etl_started",
                "job_run_id": self.job_run.id,
                "batch_size": self.batch_size,
                "chunk_size": self.chunk_size,
                "dry_run": self.dry_run,
            },
        )

        return self.job_run

    def complete(self):
        """標記 ETL 成功完成"""
        self.job_run.status = "success"
        self.job_run.records_total = self.stats["total"]
        self.job_run.records_processed = self.stats["success"]
        self.job_run.records_failed = self.stats["failed"]
        self.job_run.records_duplicated = self.stats["duplicates"]
        self.job_run.completed_at = timezone.now()
        self.job_run.save()

        logger.info(
            "ETL 任務完成",
            extra={
                "event": "etl_completed",
                "job_run_id": self.job_run.id,
                "status": "success",
                "records_total": self.stats["total"],
                "records_processed": self.stats["success"],
                "records_failed": self.stats["failed"],
            },
        )

    def fail(self, error: Exception):
        """標記 ETL 失敗"""
        self.job_run.status = "failed"
        self.job_run.error_message = str(error)
        self.job_run.completed_at = timezone.now()
        self.job_run.save()

        logger.exception(
            "ETL 任務失敗",
            extra={
                "event": "etl_failed",
                "job_run_id": self.job_run.id,
                "error": str(error),
            },
        )

    def record_errors(self, errors: List[dict], chunk_num: int):
        """記錄錯誤到資料庫"""
        if not errors:
            return

        error_records = [
            DataImportError(
                job_run=self.job_run,
                batch_number=chunk_num,
                error_type=err["type"],
                error_message=err["message"],
                raw_data=err,
            )
            for err in errors[
                :100
            ]  # Limit recording 100 errors to prevent stressful db write
        ]  # If it's over 100 error then it indicates the raw data is problematic

        DataImportError.objects.bulk_create(error_records, ignore_conflicts=True)

    def update_progress(self, chunk_num: int):
        """更新處理進度"""
        progress, _ = ImportProgress.objects.get_or_create(
            job_run=self.job_run,
            defaults={"total_batches": 0},
        )

        progress.last_successful_batch = chunk_num
        progress.current_batch = chunk_num
        progress.save()

    def get_resume_batch(self) -> int:
        """取得斷點續傳的起始批次"""
        try:
            last_job = ETLJobRun.objects.latest("started_at")

            if last_job.status == "running":
                progress = ImportProgress.objects.filter(job_run=last_job).first()
                if progress:
                    return progress.last_successful_batch + 1
        except Exception:
            pass

        return 1

    def save_error_batch(self, df: pd.DataFrame, chunk_num: int, error: str):
        """儲存錯誤批次資料到 CSV"""
        error_file = (
            f"./errors/error_batch_{chunk_num}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        file_path = Path(error_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(error_file, index=False, encoding="utf-8-sig")

        return error_file

    def add_total(self, count: int):
        """增加總處理筆數"""
        self.stats["total"] += count

    def add_success(self, count: int):
        """增加成功筆數"""
        self.stats["success"] += count

    def add_failed(self, count: int):
        """增加失敗筆數"""
        self.stats["failed"] += count

    def add_duplicates(self, count: int):
        """增加重複筆數"""
        self.stats["duplicates"] += count
