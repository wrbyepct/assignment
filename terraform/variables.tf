# ==================== 基本設定 ====================

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "專案名稱"
  type        = string
  default     = "etl-log-demo"
}

variable "environment" {
  description = "環境名稱 (dev/staging/prod)s"
  type        = string
  default     = "dev"
}

# ==================== CloudWatch 設定 ====================

variable "log_group_name" {
  description = "CloudWatch Log Group 名稱"
  type        = string
  default     = "/docker/etl"
}

variable "log_retention_days" {
  description = "Log 保留天數（Free Tier: 5GB 免費儲存）"
  type        = number
  default     = 3 # 3 天，測試用；正式環境可改 30-90 天
}

# ==================== 告警設定 ====================

variable "alarm_email" {
  description = "告警通知 Email"
  type        = string
  default     = "" # 若為 empty 則不建立 SNS 訂閱
}