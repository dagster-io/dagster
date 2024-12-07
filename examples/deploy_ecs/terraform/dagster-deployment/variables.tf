variable "region" {
  description = "The AWS region."
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC."
  type        = string
}

variable "subnets" {
  description = "List of subnets for ECS tasks."
  type        = list(string)
}

variable "ecs_cluster_id" {
  description = "ECS Cluster ID."
  type        = string
}

variable "execution_role_arn" {
  description = "The ARN of the execution role."
  type        = string
}

variable "task_role_arn" {
  description = "The ARN of the task role."
  type        = string
}

variable "dagster_image" {
  description = "Docker image for Dagster services."
  type        = string
}

variable "postgres_host" {
  description = "PostgreSQL host for Dagster."
  type        = string
}

variable "postgres_password" {
  description = "PostgreSQL password for Dagster."
  type        = string
}

variable "dagster_home" {
  description = "Directory with dagster.yaml"
  type        = string
}

variable "log_group" {
  description = "The CloudWatch log group for the service."
  type        = string
}

variable "s3_bucket" {
  description = "The S3 bucket for storage and logs."
  type        = string
}
