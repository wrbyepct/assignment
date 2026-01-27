# ==================== SNS Topic（告警通知）====================
#
# 流程：Alarm 觸發 → SNS Topic → Email

resource "aws_sns_topic" "etl_alerts" {
  name = "${var.project_name}-etl-alerts"

  tags = {
    Purpose = "ETL 告警通知"
  }
}

resource "aws_sns_topic_subscription" "email" {
  count = var.alarm_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.etl_alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

