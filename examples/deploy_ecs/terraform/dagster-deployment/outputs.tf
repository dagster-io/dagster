output "security_group_id" {
  description = "Security Group ID for Dagster"
  value       = aws_security_group.dagster.id
}

output "task_role_arn" {
  description = "Task Role ARN for Dagster"
  value       = local.task_role_arn
}

output "execution_role_arn" {
  description = "Execution ARN Name for Dagster"
  value       = local.execution_role_arn
}
