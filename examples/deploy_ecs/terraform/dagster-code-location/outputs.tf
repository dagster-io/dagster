output "security_group_id" {
  description = "Security Group ID for the Code Location"
  value       = aws_security_group.code_location.id
}

output "task_definition_arn" {
  description = "Task Definition ARN for the Code Location"
  value       = aws_ecs_task_definition.code_location.arn
}
