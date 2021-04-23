# dagster-k8s-test-infra

## Running Integration Tests Locally

Currently, the Integration Tests cannot be run locally without AWS Credentials. Make sure you have `AWS_ACCOUNT_ID`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` set in your environment.

Many of the integration tests run [Kubernetes in Docker](https://kind.sigs.k8s.io). These tests can be relatively resource intensive and you might want to modify Docker to allow for more resources (6 CPUs, 16 GB of memory instead of the defaults).
