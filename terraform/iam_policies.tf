# ==================== CloudWatch Logs 寫入權限 ====================
#
# 權限說明：
# - CreateLogGroup: 自動建立 Log Group（若不存在）
# - CreateLogStream: 自動建立 Log Stream（若不存在）
# - PutLogEvents: 寫入 log 事
# - DescribeLogGroups/Streams: 查詢現有的 groups/streams

data "aws_iam_policy_document" "cloudwatch_logs_write" {
  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]

    # 限制只能寫入特定 Log Group，符合最小權限原則
    resources = [
      "arn:aws:logs:${var.aws_region}:*:log-group:${var.log_group_name}",
      "arn:aws:logs:${var.aws_region}:*:log-group:${var.log_group_name}:*",
    ]
  }
}

# 建立 IAM Policy
resource "aws_iam_policy" "cloudwatch_logs_write" {
  name        = "${var.project_name}-cloudwatch-logs-write"
  description = "允許寫入 CloudWatch Logs（供 Docker log 收集使用）"
  policy      = data.aws_iam_policy_document.cloudwatch_logs_write.json
}