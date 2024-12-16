output "security_group_id" {
  description = "Security Group ID for Dagster"
  value       = aws_security_group.dagster.id
}
