# Dagster AWS ECS Deployment Example - Terraform

This example demonstrates how to deploy Dagster on AWS ECS using Terraform.

Two Terraform modules are provided:
- [dagster-deployment](./dagster-deployment): responsible for deploying the Dagster Daemon and Dagster Webserver as ECS services.
- [dagster-code-location](./dagster-code-location): responsible for deploying code locations as ECS services.

The example expects the following resources to be used in the deployment:
- a VPC with public and private subnets
- a configured ECS cluster
- a Postgres database for storing the Dagster event log

During the deployment, the following resources are created:
- IAM roles and policies for ECS tasks (optional, can be provided instead)
- CloudWatch log group for the ECS tasks (optional, can be provided instead)
- ECS services for the Dagster Daemon and Dagster Webserver
- ECS services for code locations
- AWS Application Load Balancer for the Dagster Webserver (optional, can be provided instead)

By default, the `dagster-deployment` automatically creates basic IAM roles and policies for the ECS tasks, and deploys an AWS Application Load Balancer for the Dagster Webserver. **This will make the Dagster Webserver accessible from the public internet**, which is useful for a quickstart, testing or development purposes. Make sure to use public subnets for `webserver_subnet_ids` if you want to access the webserver from the internet.

However, it is recommended to create IAM roles and policies separately and pass them to the module as `task_role_arn` and `execution_role_arn`. Also, if you want to restrict access to the webserver, you can set `create_lb` to `false` and configure the ALB manually.

Both modules take a `dagster_home` argument, which is the path to the directory with `dagster.yaml` and `workspace.yaml` files. `workspace.yaml` only has to be present in the daemon and webserver containers.

---

This example should be considered as a starting point for deploying Dagster on AWS ECS. It is recommended to review the Terraform modules and adjust them to fit your specific requirements.
