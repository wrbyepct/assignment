output "iam_user_name" {
  description = "IAM User 名稱"
  value       = aws_iam_user.log_writer.name
}

output "aws_access_key_id" {
  description = "Access Key ID（複製到 .env.local）"
  value       = aws_iam_access_key.log_writer.id
}

output "aws_secret_access_key" {
  description = "Secret Access Key（複製到 .env.local）⚠️ 只顯示一次！"
  value       = aws_iam_access_key.log_writer.secret
  sensitive   = true # 預設隱藏，需用 terraform output -raw aws_secret_access_key 查看
}



output "log_group_name" {
  description = "CloudWatch Log Group 名稱"
  value       = aws_cloudwatch_log_group.etl.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.etl.arn
}


output "sns_topic_arn" {
  description = "SNS Topic ARN（用於告警通知）"
  value       = aws_sns_topic.etl_alerts.arn
}


output "dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.etl.dashboard_name}"
}


