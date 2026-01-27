# tax_registration/management/commands/import_business.py
import logging
from pathlib import Path
import pandas as pd
import requests
from contextlib import contextmanager
from typing import List
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

from core.tax_registration.models import (
    TaxRegistration,
    ETLJobRun,
    DataImportError,
    ImportProgress,
)

from core.tax_registration.etl.extractor import CSVExtractor
from core.tax_registration.etl.transformer import TaxDataTransformer
from core.tax_registration.etl.loader import BulkLoader


logger = logging.getLogger("tax_registration.etl")


class Command(BaseCommand):
    help = "匯入全國營業登記資料(優化版)"

    # 類別常數
    CSV_URL = "https://eip.fia.gov.tw/data/BGMOPEN1.csv"

    def __init__(self):
        super().__init__()
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "duplicates": 0,
            "skipped": 0,
        }
        self.job_run = None
        self.start_time = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10000,
            help="每批次處理筆數(建議 5000-20000)",
        )
        parser.add_argument(
            "--chunk-size", type=int, default=50000, help="CSV 讀取 chunk 大小"
        )
        parser.add_argument("--resume", action="store_true", help="從上次中斷處繼續")
        parser.add_argument(
            "--dry-run", action="store_true", help="只驗證資料不實際匯入"
        )
        parser.add_argument(
            "--truncate", action="store_true", help="清空現有資料後重新匯入(危險操作!)"
        )
        parser.add_argument(
            "--limit", type=int, default=None, help="限制處理筆數(測試用)"
        )
        parser.add_argument(
            "--auto", action="store_true", help="跳過確認提示（用於自動化排程）"
        )

    def handle(self, *args, **options):
        """主要進入點"""
        self.batch_size = options["batch_size"]
        self.chunk_size = options["chunk_size"]
        self.dry_run = options["dry_run"]
        self.resume = options["resume"]
        self.limit = options["limit"]
        self.auto = options["auto"]  # 存起來

        # 檢查是否有正在執行中的任務
        ongoing_job = ETLJobRun.objects.filter(
            status="running"
        ).exists()  # Already indexed, the query is fast

        if ongoing_job:
            self.stdout.write(self.style.ERROR("已有任務正在執行中，請稍後再試。"))
            return  # 終止執行

        if options["truncate"] and options["resume"]:
            raise CommandError(
                "❌ --truncate 和 --resume 不能同時使用\n"
                "   --truncate: 清空資料後重新匯入\n"
                "   --resume: 從上次中斷處繼續"
            )

        # 載入新資料前空 table
        if options["truncate"]:
            if not self._confirm_truncate():
                self.stdout.write(self.style.WARNING("操作已取消"))
                return
            self._truncate_tables()

        # 建立執行紀錄
        self.create_etl_job()

        try:
            self.handle_successful_etl_job()
        except Exception as e:
            self.handle_failed_etl_job(e)
        finally:
            self.job_run.completed_at = timezone.now()
            self.job_run.save()
            self._print_summary()

    def create_etl_job(self):
        """創建 ETL Job 並 log"""
        self.job_run = ETLJobRun.objects.create(
            status="running",
            batch_size=self.batch_size,
            chunk_size=self.chunk_size,
            data_source_url=self.CSV_URL,
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

    def handle_successful_etl_job(self):
        """執行 ETL Job, 更新成功結果, log 成功訊息"""
        with self._track_progress():
            self._run_etl()

        # 更新執行結果
        self.job_run.status = "success"
        self.job_run.records_total = self.stats["total"]
        self.job_run.records_processed = self.stats["success"]
        self.job_run.records_failed = self.stats["failed"]
        self.job_run.records_duplicated = self.stats["duplicates"]

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

    @contextmanager
    def _track_progress(self):
        """追蹤執行進度"""
        self.start_time = timezone.now()
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n{'=' * 60}\n開始執行 ETL (ID: {self.job_run.id})\n{'=' * 60}\n"
            )
        )
        yield  # _run_etl runs here
        duration = (timezone.now() - self.start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"\n執行時間: {duration:.2f} 秒"))

    def handle_failed_etl_job(self, error):
        """執行 ETL Job, 更新失敗結果, log 失敗訊息"""

        self.job_run.status = "failed"
        self.job_run.error_message = str(error)
        logger.exception(
            "ETL 任務失敗",
            extra={
                "event": "etl_failed",
                "job_run_id": self.job_run.id,
                "error": str(error),
            },
        )
        raise CommandError(f"執行失敗: {error}")

    def _run_etl(self):
        """ETL 主流程"""
        # 1. Extract: 下載資料
        self.stdout.write("📥 階段 1: 擷取資料...")

        try:
            extractor = CSVExtractor(self.CSV_URL)
            data_chunks = extractor.fetch_chunks(self.chunk_size)
        except requests.RequestException as e:
            raise CommandError(f"資料下載失敗: {e}")

        # 2. Transform & Load: 清理並載入
        self.transformer = TaxDataTransformer()
        self.loader = BulkLoader(self.batch_size)

        self.stdout.write("🔄 階段 2: 轉換並載入資料...")

        # 取得起始批次(斷點續傳)
        start_batch = 1
        if self.resume:
            progress = (
                self._get_progress()
            )  # 得到狀態停留在 running 中的任務的追蹤進度 instance
            if progress:
                start_batch = progress.last_successful_batch + 1
                self.stdout.write(f"  ⏩ 從批次 {start_batch} 繼續...")

        # 處理每個 chunk
        for chunk_num, df_chunk in enumerate(data_chunks, 1):
            # Garbage collection after every loop

            if chunk_num < start_batch:
                continue

            # 限制處理筆數(for testing)
            self.stdout.write(f"目前已處理 {self.stats['total']}")
            if self.limit and self.stats["total"] >= self.limit:
                self.stdout.write(
                    self.style.WARNING(f"  已達到限制 ({self.limit} 筆),停止處理")
                )
                break

            try:
                self._process_chunk(df_chunk, chunk_num)
            except Exception as e:
                logger.error(f"批次 {chunk_num} 處理失敗: {e}")
                self._save_error_batch(df_chunk, chunk_num, str(e))

                # 決定是否繼續
                if not self._should_continue_on_error():
                    raise

    def _process_chunk(self, df_chunk: pd.DataFrame, chunk_num: int):
        """處理單一 chunk"""
        original_count = len(df_chunk)

        self.stdout.write(f"\n📦 批次 {chunk_num}")
        self.stdout.write(f"  原始筆數: {original_count:,}")

        logger.info(
            "開始處理批次",
            extra={
                "event": "batch_started",
                "job_run_id": self.job_run.id,
                "batch_num": chunk_num,
                "raw_count": original_count,
            },
        )
        # Transform: 清理資料
        df_clean, errors = self.transformer.process(df_chunk, chunk_num)
        self.stdout.write(f"  清理: {original_count:,} → {len(df_clean):,} 筆")

        self.stats["failed"] += len(errors)
        self.stats["total"] += original_count

        # 統計重複筆數
        duplicates_count = sum(1 for e in errors if e["type"] == "DUPLICATE")
        self.stats["duplicates"] += duplicates_count

        # 記錄錯誤
        if errors:
            # If any row has error, record which batch it is in has error
            self._log_errors(errors, chunk_num)
            self.stdout.write(self.style.WARNING(f"  ⚠️  驗證失敗: {len(errors)} 筆"))

            logger.warning(
                "批次驗證有錯誤",
                extra={
                    "event": "batch_validation_errors",
                    "job_run_id": self.job_run.id,
                    "batch_num": chunk_num,
                    "error_count": len(errors),
                },
            )
        # Load: 載入資料庫
        if not df_clean.empty and not self.dry_run:
            success_count = self.loader.insert(df_clean)
            self.stats["success"] += success_count
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ 成功匯入: {success_count:,} 筆")
            )
            logger.info(
                "批次處理完成",
                extra={
                    "event": "batch_completed",
                    "job_run_id": self.job_run.id,
                    "batch_num": chunk_num,
                    "records_processed": success_count,
                },
            )
            # 更新進度
            self._update_progress(chunk_num)
        elif self.dry_run:
            self.stdout.write(
                self.style.NOTICE(f"  🔍 DRY RUN: 將匯入 {len(df_clean):,} 筆")
            )
            logger.info(
                "Dry run 批次預覽",
                extra={
                    "event": "batch_dry_run",
                    "job_run_id": self.job_run.id,
                    "batch_num": chunk_num,
                    "would_process": len(df_clean),
                },
            )

    """
    ===== Load ====
    """

    def _log_errors(self, errors: List[dict], chunk_num: int):
        """記錄錯誤到資料庫"""
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

    def _update_progress(self, batch_num: int):
        """更新進度"""
        progress, created = ImportProgress.objects.get_or_create(
            job_run=self.job_run, defaults={"total_batches": 0}
        )

        progress.last_successful_batch = batch_num
        progress.current_batch = batch_num
        progress.save()

    def _get_progress(self) -> ImportProgress:
        """取得進度(斷點續傳)"""
        try:
            # 找最近一次未完成的執行
            last_job = (
                ETLJobRun.objects.filter(status="running")
                .order_by("-started_at")
                .first()
            )

            if last_job:
                return ImportProgress.objects.filter(job_run=last_job).first()
        except Exception:
            pass
        return None

    def _save_error_batch(self, df: pd.DataFrame, batch_num: int, error: str):
        """儲存錯誤批次資料"""
        error_file = (
            f"./errors/error_batch_{batch_num}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        file_path = Path(error_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(error_file, index=False, encoding="utf-8-sig")
        self.stderr.write(self.style.ERROR(f"  錯誤資料已儲存: {error_file}"))

    def _print_summary(self):
        """輸出執行摘要"""
        duration = self.job_run.duration_seconds or 0
        success_rate = self.job_run.success_rate

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\n{'=' * 60}\n執行摘要\n{'=' * 60}\n")
        )

        self.stdout.write(f"執行 ID:      {self.job_run.id}")
        self.stdout.write(f"狀態:         {self.job_run.get_status_display()}")
        self.stdout.write(f"執行時間:     {duration:.2f} 秒")
        self.stdout.write("\n處理統計:")
        self.stdout.write(f"  總筆數:     {self.stats['total']:,}")
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✅ 成功:    {self.stats['success']:,} ({success_rate:.2f}%)"
            )
        )

        if self.stats["failed"] > 0:
            self.stdout.write(
                self.style.ERROR(f"  ❌ 失敗:    {self.stats['failed']:,}")
            )

        if self.stats["duplicates"] > 0:
            self.stdout.write(
                self.style.WARNING(f"  🔄 重複:    {self.stats['duplicates']:,}")
            )

        self.stdout.write(f"\n{'=' * 60}\n")

        # 提示查看詳細錯誤
        if self.stats["failed"] > 0:
            self.stdout.write(
                self.style.NOTICE(
                    f"\n💡 查看詳細錯誤:\n"
                    f"   python manage.py shell\n"
                    f"   >>> from tax_registration.models import DataImportError\n"
                    f"   >>> DataImportError.objects.filter(job_run_id={self.job_run.id})\n"
                )
            )
        # === 結構化 log 給 CloudWatch ===
        logger.info(
            "ETL 執行摘要",
            extra={
                "event": "etl_summary",
                "job_run_id": self.job_run.id,
                "status": self.job_run.status,
                "duration_seconds": round(duration, 2),
                "success_rate": round(success_rate, 2),
                "records_total": self.stats["total"],
                "records_success": self.stats["success"],
                "records_failed": self.stats["failed"],
                "records_duplicates": self.stats["duplicates"],
            },
        )

    def _confirm_truncate(self) -> bool:
        """確認清空資料"""
        if self.auto:
            return True  # 自動化模式直接通過

        count = TaxRegistration.objects.count()
        self.stdout.write(
            self.style.WARNING(f"\n⚠️  警告:即將刪除 {count:,} 筆營業登記資料!")
        )

        answer = input("確定要繼續嗎? (yes/no): ")
        return answer.lower() == "yes"

    def _truncate_tables(self):
        """清空資料表"""
        self.stdout.write("🗑️  清空資料表...")

        # Faster deletion
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE tax_registration CASCADE;")
            cursor.execute("TRUNCATE TABLE business_industry CASCADE;")

        self.stdout.write(self.style.SUCCESS("  ✅ 完成"))

    def _should_continue_on_error(self) -> bool:
        """詢問是否繼續"""
        if self.dry_run:
            return True

        answer = input("\n發生錯誤,是否繼續下一批次? (yes/no): ")
        return answer.lower() == "yes"
