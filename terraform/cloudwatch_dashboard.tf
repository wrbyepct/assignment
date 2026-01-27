# ==================== CloudWatch Dashboard ====================
#
# Dashboard 包含：
# 1. ERROR 數量趨勢圖
# 2. ETL 執行狀態（成功/失敗）
# 3. 處理筆數
# 4. 最近的 Log 事件

resource "aws_cloudwatch_dashboard" "etl" {
  dashboard_name = "${var.project_name}-etl-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # ========== 第一列：標題 ==========
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# 🚀 ETL 監控 Dashboard"
        }
      },

      # ========== 第二列：關鍵指標 ==========
      # ERROR 數量
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "❌ ERROR 數量"
          region = var.aws_region
          metrics = [
            ["${var.project_name}/ETL", "ErrorCount", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },

      # ETL 完成次數
      {
        type   = "metric"
        x      = 8
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "✅ ETL 完成次數"
          region = var.aws_region
          metrics = [
            ["${var.project_name}/ETL", "ETLCompleted", { stat = "Sum", period = 300, color = "#2ca02c" }],
            ["${var.project_name}/ETL", "ETLFailed", { stat = "Sum", period = 300, color = "#d62728" }]
          ]
          view = "timeSeries"
        }
      },

      # 處理筆數
      {
        type   = "metric"
        x      = 16
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "📊 處理筆數"
          region = var.aws_region
          metrics = [
            ["${var.project_name}/ETL", "RecordsProcessed", { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },

      # ========== 第三列：Log 查詢 ==========
      {
        type   = "log"
        x      = 0
        y      = 7
        width  = 24
        height = 6
        properties = {
          title  = "📋 最近的 Log 事件"
          region = var.aws_region
          query  = "SOURCE '${var.log_group_name}' | fields @timestamp, @message | sort @timestamp desc | limit 50"
        }
      },

      # ========== 第四列：告警狀態 ==========
      {
        type   = "alarm"
        x      = 0
        y      = 13
        width  = 24
        height = 3
        properties = {
          title = "🚨 告警狀態"
          alarms = [
            aws_cloudwatch_metric_alarm.high_error_count.arn,
            aws_cloudwatch_metric_alarm.etl_failed.arn
          ]
        }
      }
    ]
  })
}

