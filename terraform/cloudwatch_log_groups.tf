# ==================== CloudWatch Log Group ====================
#
# 架構：
#   /docker/etl (Log Group)
#   ├── console (Log Stream) ← awslogs driver 送的 stdout/stderr
#   └── file (Log Stream)    ← CloudWatch Agent 送的實體檔案

resource "aws_cloudwatch_log_group" "etl" {
  name              = var.log_group_name     # 預設: /docker/etl
  retention_in_days = var.log_retention_days # 預設: 3 天 for demo purpose

  tags = {
    Purpose = "ETL Docker container logs"
  }
}

# ==================== Log Streams ====================

# Console Log Stream（awslogs driver）
resource "aws_cloudwatch_log_stream" "console" {
  name           = "console"
  log_group_name = aws_cloudwatch_log_group.etl.name
}

# File Log Stream（CloudWatch Agent）
resource "aws_cloudwatch_log_stream" "file" {
  name           = "file"
  log_group_name = aws_cloudwatch_log_group.etl.name
}

