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

variable "create_iam_roles" {
  description = "Whether to create IAM roles and policies."
  type        = bool
}

variable "execution_role_arn" {
  description = "The ARN of the execution role."
  type        = string
  default     = null
}

variable "task_role_arn" {
  description = "The ARN of the task role."
  type        = string
  default     = null
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
  sensitive   = true
}

variable "dagster_home" {
  description = "Directory with dagster.yaml"
  type        = string
}

variable "environment" {
  description = "List of environment variables for ECS tasks."
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secrets" {
  description = "List of secrets to pass to the ECS task as environment variables."
  type = list(object({
    name       = string
    value_from = string
  }))
  default = []
}

variable "log_group" {
  description = "The CloudWatch log group for the service."
  type        = string
}
