# ==================== Metric Filters ====================
#
# Dashboard 需追蹤：
# 1. ERROR 數量 - 有多少錯誤發生
# 2. ETL 完成事件 - ETL 是否成功執行

# ---------- ERROR 計數 ----------
# 過濾條件：log 內容包含 "ERROR" 或 "level": "ERROR"（JSON 格式）
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${var.project_name}-error-count"
  log_group_name = aws_cloudwatch_log_group.etl.name

  # 匹配 JSON 格式的 ERROR log
  # Django log 格式：{"level": "ERROR", "message": "..."}
  pattern = "{ $.level = \"ERROR\" }"

  metric_transformation {
    name          = "ErrorCount"
    namespace     = "${var.project_name}/ETL"
    value         = "1"
    default_value = "0"
  }
}

# ---------- ETL 完成事件 ----------
# 過濾條件：log 內容包含 "etl_completed" 事件
resource "aws_cloudwatch_log_metric_filter" "etl_completed" {
  name           = "${var.project_name}-etl-completed"
  log_group_name = aws_cloudwatch_log_group.etl.name

  # 匹配 ETL 完成的 log
  # Django log：{"event": "etl_completed", ...}
  pattern = "{ $.event = \"etl_completed\" }"

  metric_transformation {
    name          = "ETLCompleted"
    namespace     = "${var.project_name}/ETL"
    value         = "1"
    default_value = "0"
  }
}

# ---------- ETL 失敗事件 ----------
resource "aws_cloudwatch_log_metric_filter" "etl_failed" {
  name           = "${var.project_name}-etl-failed"
  log_group_name = aws_cloudwatch_log_group.etl.name

  pattern = "{ $.event = \"etl_failed\" }"

  metric_transformation {
    name          = "ETLFailed"
    namespace     = "${var.project_name}/ETL"
    value         = "1"
    default_value = "0"
  }
}

# ---------- 處理筆數 ----------
# 從 etl_summary log 中提取 records_success 數值
resource "aws_cloudwatch_log_metric_filter" "records_processed" {
  name           = "${var.project_name}-records-processed"
  log_group_name = aws_cloudwatch_log_group.etl.name

  # 匹配 ETL summary log
  pattern = "{ $.event = \"etl_summary\" }"

  metric_transformation {
    name          = "RecordsProcessed"
    namespace     = "${var.project_name}/ETL"
    value         = "$.records_success" # 從 log 中取值
    default_value = "0"
  }
}