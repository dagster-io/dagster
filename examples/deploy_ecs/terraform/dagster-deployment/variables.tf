variable "region" {
  description = "The AWS region."
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC."
  type        = string
}

variable "daemon_subnet_ids" {
  description = "List of subnet ids for the Dagster Daemon ECS task."
  type        = list(string)
}

variable "webserver_subnet_ids" {
  description = "List of subnet ids for the Dagster Webserver ECS task."
  type        = list(string)
}

variable "ecs_cluster_id" {
  description = "ECS Cluster ID."
  type        = string
}

variable "create_iam_roles" {
  description = "Whether to create IAM roles and policies."
  type        = bool
  default     = true
}

variable "execution_role_arn" {
  description = "The ARN of the execution role. Provide this if create_iam_roles is false."
  type        = string
  default     = null
}

variable "task_role_arn" {
  description = "The ARN of the task role. Provide this if create_iam_roles is false."
  type        = string
  default     = null
}

variable "create_lb" {
  description = "Whether to create a load balancer."
  type        = bool
  default     = true
}

variable "lb_target_group_arn" {
  description = "The ARN of the target group for the load balancer. Provide this if create_lb is false."
  type        = string
  default     = null
}

variable "assign_public_ip" {
  description = "Whether to assign a public IP to the ECS tasks. Warning: this might will expose the tasks to the internet."
  type        = bool
  default     = true
}

variable "create_log_group" {
  description = "Whether to create a CloudWatch log group."
  type        = bool
  default     = true
}

variable "log_group" {
  description = "The CloudWatch log group for the tasks. Provide this if create_log_group is false."
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
