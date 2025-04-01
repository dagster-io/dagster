resource "aws_cloudwatch_log_group" "ecs_task_log_group" {
  count = var.create_log_group ? 1 : 0
  name_prefix = "/ecs/dagster-"
  retention_in_days = 7
}

locals {
  log_group = var.create_log_group ? aws_cloudwatch_log_group.ecs_task_log_group[0].name : var.log_group
}
