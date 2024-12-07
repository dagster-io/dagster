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

variable "task_role_arn" {
  description = "The ARN of the task role."
  type        = string
}

variable "execution_role_arn" {
  description = "The ARN of the execution role."
  type        = string
}

variable "namespace_id" {
  description = "The namespace ID for the service."
  type        = string
}

variable "service_name" {
  description = "Name of the code location service."
  type        = string
}

variable "dagster_home" {
  description = "Directory with dagster.yaml"
  type        = string
}

variable "module_name" {
  description = "The module name for the gRPC server."
  type        = string
}

variable "image" {
  description = "Docker image for the gRPC service."
  type        = string
}

variable "postgres_host" {
  description = "PostgreSQL host for Dagster."
  type        = string
}

variable "postgres_user" {
  description = "PostgreSQL user for Dagster."
  type        = string
}

variable "postgres_password" {
  description = "PostgreSQL password for Dagster."
  type        = string
}

variable "s3_bucket" {
  description = "The S3 bucket for storage and logs."
  type        = string
}

variable "log_group" {
  description = "The CloudWatch log group for the service."
  type        = string
}
