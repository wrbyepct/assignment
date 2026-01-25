# Register your models here.
from django.contrib import admin
from .models import (
    TaxRegistration,
    BusinessIndustry,
    ETLJobRun,
    DataImportError,
    ImportProgress,
)


# --- 1. Inline 配置：在營業登記頁面直接顯示/編輯行業項目 ---
class BusinessIndustryInline(admin.TabularInline):
    model = BusinessIndustry
    extra = 1  # 預設多顯示一個空白列供新增
    fields = ("order", "industry_code", "industry_name")


# --- 2. 營業登記 Admin ---
@admin.register(TaxRegistration)
class TaxRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "ban",
        "business_name",
        "business_type",
        "is_use_invoice",
        "capital_amount",
        "created_at",
    )
    search_fields = ("ban", "business_name", "business_address")
    list_filter = ("is_use_invoice", "business_type", "data_source_date")
    readonly_fields = ("created_at", "updated_at")
    inlines = [BusinessIndustryInline]  # 嵌入行業別

    # 按照更新時間排序
    ordering = ("-updated_at",)


# --- 3. ETL 執行紀錄 Admin (著重於監控) ---
class DataImportErrorInline(admin.StackedInline):
    model = DataImportError
    extra = 0
    readonly_fields = (
        "batch_number",
        "error_type",
        "error_message",
        "raw_data",
        "created_at",
    )
    can_delete = False  # 錯誤紀錄通常不建議手動刪除


class ImportProgressInline(admin.StackedInline):
    model = ImportProgress
    readonly_fields = (
        "current_batch",
        "total_batches",
        "last_successful_batch",
        "updated_at",
    )
    can_delete = False


@admin.register(ETLJobRun)
class ETLJobRunAdmin(admin.ModelAdmin):
    list_display = (
        "started_at",
        "status",
        "records_total",
        "records_processed",
        "records_failed",
        "duration_display",
    )
    list_filter = ("status", "started_at")
    readonly_fields = ("started_at", "completed_at", "duration_display")
    inlines = [ImportProgressInline, DataImportErrorInline]

    @admin.display(description="執行耗時")
    def duration_display(self, obj):
        seconds = obj.duration_seconds
        return f"{seconds:.2f} 秒" if seconds else "-"


# --- 4. 其他輔助模型 ---
@admin.register(BusinessIndustry)
class BusinessIndustryAdmin(admin.ModelAdmin):
    list_display = ("business", "industry_code", "industry_name", "order")
    search_fields = (
        "business__ban",
        "business__business_name",
        "industry_code",
        "industry_name",
    )
    list_filter = ("industry_code",)


@admin.register(DataImportError)
class DataImportErrorAdmin(admin.ModelAdmin):
    list_display = ("job_run", "batch_number", "error_type", "created_at")
    list_filter = ("error_type", "created_at")
    readonly_fields = (
        "job_run",
        "batch_number",
        "error_type",
        "error_message",
        "raw_data",
        "created_at",
    )


@admin.register(ImportProgress)
class ImportProgressAdmin(admin.ModelAdmin):
    list_display = ("job_run", "current_batch", "total_batches", "updated_at")
