output "task_definition_arn" {
  description = "Task Definition ARN for the Code Location"
  value       = aws_ecs_task_definition.code_location.arn
}
