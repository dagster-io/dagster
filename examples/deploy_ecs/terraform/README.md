# Dagster AWS ECS Deployment Example - Terraform

This example demonstrates how to deploy Dagster on AWS ECS using Terraform.

Two Terraform modules are provided:
- [dagster-deployment](./dagster-deployment): responsible for deploying the Dagster Daemon and Dagster Webserver as ECS services.
- [dagster-code-location](./dagster-code-location): responsible for deploying code locations as ECS services.

The example is opinionated and expects the Dagster deployment to use the following:
- an S3 bucket for storing artifacts and logs
- a Postgres database for storing the Dagster event log

It should be easy to modify the Terraform modules to use different storage solutions.
