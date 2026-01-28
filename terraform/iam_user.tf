

resource "aws_iam_user" "log_writer" {
  name = "${var.project_name}-log-writer"

  tags = {
    Purpose = "Docker log collection awslogs and CloudWatch Agent"
  }
}

resource "aws_iam_user_policy_attachment" "log_writer_policy" {
  user       = aws_iam_user.log_writer.name
  policy_arn = aws_iam_policy.cloudwatch_logs_write.arn
}

resource "aws_iam_access_key" "log_writer" {
  user = aws_iam_user.log_writer.name
}

