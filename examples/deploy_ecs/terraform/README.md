# Dagster AWS ECS Deployment Example - Terraform

This example demonstrates how to deploy Dagster on AWS ECS using Terraform.

Two Terraform modules are provided:
- [dagster-deployment](./dagster-deployment): responsible for deploying the Dagster Daemon and Dagster Webserver as ECS services.
- [dagster-code-location](./dagster-code-location): responsible for deploying code locations as ECS services.

The example excepts the following resources to be used in the deployment:
- a VPC with public and private subnets
- a configured ECS cluster
- a Postgres database for storing the Dagster event log
- AWS CloudWatch log group for ECS task logs

During the deployment, the following resources are created:
- ECS services for the Dagster Daemon and Dagster Webserver
- ECS services for code locations
- AWS Application Load Balancer for the Dagster Webserver

It's possible to automatically create basic IAM roles and policies by setting `create_iam_roles` to `true` in the `dagster-deployment` module. However, it's recommended to create IAM roles and policies separately and pass them to the module as `task_role_arn` and `execution_role_arn`.

Both modules take a `dagster_home` argument, which is the path to the directory with `dagster.yaml` and `workspace.yaml` files. `workspace.yaml` only has to be present in the daemon and webserver containers.

---

This example should be considered as a starting point for deploying Dagster on AWS ECS. It is recommended to review the Terraform modules and adjust them to fit your specific requirements.
