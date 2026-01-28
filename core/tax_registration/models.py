# tax_registration/models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.db.models.functions import Now


class TaxRegistration(models.Model):
    """營業登記主表"""

    # 基本資訊
    ban = models.CharField(
        "統一編號",
        max_length=8,
        primary_key=True,
        validators=[
            RegexValidator(regex=r"^\d{8}$", message="統一編號必須是 8 位數字")
        ],
    )

    headquarters_ban = models.CharField(
        "總機構統一編號",
        max_length=8,
        blank=True,
        null=True,
        validators=[
            RegexValidator(regex=r"^\d{8}$", message="總機構統一編號必須是 8 位數字")
        ],
        db_index=True,
    )

    business_name = models.CharField("營業人名稱", max_length=255, db_index=True)

    business_address = models.CharField("營業地址", max_length=500, blank=True)

    # 財務資訊
    capital_amount = models.BigIntegerField(
        "資本額", default=0, validators=[MinValueValidator(0)], db_index=True
    )

    # 設立資訊
    business_setup_date = models.CharField(
        "設立日期", max_length=8, blank=True, help_text="格式: YYYYMMDD"
    )

    business_type = models.CharField(
        "組織別名稱", max_length=50, blank=True, db_index=True
    )

    is_use_invoice = models.BooleanField(
        "使用統一發票",
        default=False,
    )

    # 系統欄位
    created_at = models.DateTimeField(
        "建立時間",
        auto_now_add=True,
        db_default=Now(),
        db_index=True,
    )

    updated_at = models.DateTimeField(
        "更新時間",
        auto_now=True,
        db_default=Now(),
    )

    data_source_date = models.DateField(
        "資料來源日期",
        null=True,
        blank=True,
        auto_now_add=True,
        db_default=Now(),
        help_text="CSV 檔案的日期",
    )

    class Meta:
        db_table = "tax_registration"
        verbose_name = "營業登記"
        verbose_name_plural = "營業登記"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.ban} - {self.business_name}"


class BusinessIndustry(models.Model):
    """營業項目(行業別)"""

    business = models.ForeignKey(
        TaxRegistration,
        on_delete=models.CASCADE,
        related_name="industries",
        verbose_name="營業人",
    )

    industry_code = models.CharField(
        "行業代號",
        max_length=20,
        blank=True,
        db_index=True,  # 查詢"所有從事某行業的公司"
    )

    industry_name = models.CharField("行業名稱", max_length=255, blank=True)

    order = models.PositiveSmallIntegerField(
        "順序", default=1, help_text="第1、2、3、4個行業"
    )

    class Meta:
        db_table = "business_industry"
        verbose_name = "營業項目"
        verbose_name_plural = "營業項目"
        ordering = ["business", "order"]

        constraints = [
            models.UniqueConstraint(
                fields=["business", "industry_code"], name="unique_business_industry"
            )
        ]
        # 複合索引:查詢效能優化
        indexes = [
            # 查詢"所有從事某行業的公司"
            models.Index(fields=["industry_code", "business"], name="idx_ind_code_biz"),
        ]

    def __str__(self):
        return f"{self.business.ban} - {self.industry_name}"


class ETLJobRun(models.Model):
    """ETL 執行紀錄"""

    STATUS_CHOICES = [
        ("running", "執行中"),
        ("success", "成功"),
        ("failed", "失敗"),
        ("partial", "部分成功"),
    ]

    started_at = models.DateTimeField("開始時間", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新時間", auto_now_add=True, db_index=True)

    completed_at = models.DateTimeField("完成時間", null=True, blank=True)

    status = models.CharField(
        "狀態", max_length=20, choices=STATUS_CHOICES, default="running", db_index=True
    )

    records_total = models.IntegerField("總筆數", default=0)

    records_processed = models.IntegerField("處理成功筆數", default=0)

    records_failed = models.IntegerField("失敗筆數", default=0)

    records_duplicated = models.IntegerField("重複筆數", default=0)

    error_message = models.TextField("錯誤訊息", blank=True)

    batch_size = models.IntegerField("批次大小", default=10000)

    chunk_size = models.IntegerField("Chunk 大小", default=50000)

    data_source_url = models.URLField("資料來源網址", blank=True)

    class Meta:
        db_table = "etl_job_run"
        verbose_name = "ETL執行紀錄"
        verbose_name_plural = "ETL執行紀錄"
        ordering = ["-started_at"]

    def __str__(self):
        duration = ""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            duration = f" ({delta.total_seconds():.2f}秒)"
        return f"{self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}{duration}"

    @property
    def duration_seconds(self):
        """執行時長(秒)"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self):
        """成功率"""
        if self.records_total > 0:
            return (self.records_processed / self.records_total) * 100
        return 0


class DataImportError(models.Model):
    """
    資料匯入錯誤紀錄

    Record duplicated rows or rows with invalid ban.
    """

    job_run = models.ForeignKey(
        ETLJobRun,
        on_delete=models.CASCADE,
        related_name="errors",
        verbose_name="ETL執行",
    )

    batch_number = models.IntegerField("批次編號")

    error_type = models.CharField("錯誤類型", max_length=50, db_index=True)

    error_message = models.TextField("錯誤訊息")

    raw_data = models.JSONField(
        "原始資料", null=True, blank=True, help_text="導致錯誤的原始資料(JSON格式)"
    )

    created_at = models.DateTimeField("建立時間", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "data_import_error"
        verbose_name = "匯入錯誤紀錄"
        verbose_name_plural = "匯入錯誤紀錄"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["error_type", "created_at"], name="idx_err_type_time"),
        ]

    def __str__(self):
        return f"批次{self.batch_number} - {self.error_type}"


class ImportProgress(models.Model):
    """匯入進度追蹤(支援斷點續傳)"""

    job_run = models.OneToOneField(
        ETLJobRun,
        on_delete=models.CASCADE,
        related_name="progress",
        verbose_name="ETL執行",
    )

    last_successful_batch = models.IntegerField("最後成功批次", default=0)

    total_batches = models.IntegerField("總批次數", default=0)

    current_batch = models.IntegerField("當前批次", default=0)

    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        db_table = "import_progress"
        verbose_name = "匯入進度"
        verbose_name_plural = "匯入進度"

    def __str__(self):
        return f"進度: {self.current_batch}/{self.total_batches}"

    @property
    def progress_percentage(self):
        """進度百分比"""
        if self.total_batches > 0:
            return (self.current_batch / self.total_batches) * 100
        return 0
