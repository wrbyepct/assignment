from django.db import models


class TaxRegistration(models.Model):
    ban = models.CharField("統一編號", max_length=8, primary_key=True, db_index=True)
    headquarters_ban = models.CharField(
        "總機構統一編號", max_length=8, blank=True, null=True
    )
    business_name = models.CharField("營業人名稱", max_length=200, db_index=True)
    business_address = models.CharField("營業地址", max_length=255)

    capital_amount = models.IntegerField("資本額", null=True, blank=True)
    established_date = models.CharField("設立日期", max_length=7)  # YYYMMDD 民國日期
    business_type = models.CharField("組織別", max_length=100)
    is_use_invoice = models.BooleanField("使用統一發票", default=False)

    industry_code = models.CharField("行業代號", max_length=10, db_index=True)
    industry_name = models.CharField("行業名稱", max_length=100)

    industry_code_1 = models.CharField(
        "行業代號1", max_length=10, blank=True, null=True
    )
    industry_name_1 = models.CharField(
        "行業名稱1", max_length=100, blank=True, null=True
    )

    industry_code_2 = models.CharField(
        "行業代號2", max_length=10, blank=True, null=True
    )
    industry_name_2 = models.CharField(
        "行業名稱2", max_length=100, blank=True, null=True
    )

    industry_code_3 = models.CharField(
        "行業代號3", max_length=10, blank=True, null=True
    )
    industry_name_3 = models.CharField(
        "行業名稱3", max_length=100, blank=True, null=True
    )

    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        verbose_name = "營業登記"
        verbose_name_plural = "營業登記"
        indexes = [
            models.Index(fields=["business_name"]),
            models.Index(fields=["industry_code"]),
        ]

    def __str__(self):
        return f"{self.ban} - {self.business_name}"
