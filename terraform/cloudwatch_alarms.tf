# ==================== CloudWatch Alarms ====================
#
# 告警規則：
# 1. 5 分鐘內出現 >= 5 個 ERROR → 告警
# 2. ETL 失敗 → 告警

# ---------- ERROR 數量告警 ----------
resource "aws_cloudwatch_metric_alarm" "high_error_count" {
  alarm_name          = "${var.project_name}-high-error-count"
  alarm_description   = "5 分鐘內 ERROR 數量超過 5 次" 
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1 # 評估 1 個週期
  metric_name         = "ErrorCount"
  namespace           = "${var.project_name}/ETL"
  period              = 300 # 5 分鐘 (300 秒)
  statistic           = "Sum"
  threshold           = 5              # >= 5 個 ERROR (測試用)
  treat_missing_data  = "notBreaching" # 沒資料時不觸發

  # 觸發時通知 SNS
  alarm_actions = [aws_sns_topic.etl_alerts.arn]
  ok_actions    = [aws_sns_topic.etl_alerts.arn] # 恢復時也通知

  tags = {
    Purpose = "監控 ETL 錯誤數量"
  }
}

# ---------- ETL 失敗告警 ----------
resource "aws_cloudwatch_metric_alarm" "etl_failed" {
  alarm_name          = "${var.project_name}-etl-failed"
  alarm_description   = "ETL 任務執行失敗"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ETLFailed"
  namespace           = "${var.project_name}/ETL"
  period              = 60 # 1 分鐘
  statistic           = "Sum"
  threshold           = 1 # 只要有 1 次失敗就告警
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.etl_alerts.arn]

  tags = {
    Purpose = "監控 ETL 執行狀態"
  }
}