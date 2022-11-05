# Deploying to AWS ECS Using Docker Compose

This directory contains annotated files for deploying Dagster with an EcsRunLauncher to AWS ECS using Docker Compose. You can use these as a reference for configuring your own Dagster ECS deployment.

## Prerequisites

1. [Install Docker](https://docs.docker.com/cloud/ecs-integration/#prerequisites)
2. [Create an AWS account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)
3. [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
4. [Configure IAM permissions](https://docs.docker.com/cloud/ecs-integration/#requirements)
5. [Create a Docker ECS context](https://docs.docker.com/cloud/ecs-integration/#create-aws-context):
  ```sh
  docker context create ecs dagster-ecs
  ```
6. [Create ECR Repositories](https://docs.aws.amazon.com/cli/latest/reference/ecr/create-repository.html) for our images:
  ```sh
  aws ecr create-repository --repository-name deploy_ecs/dagit
  aws ecr create-repository --repository-name deploy_ecs/daemon
  aws ecr create-repository --repository-name deploy_ecs/user_code
  ```
7. [Log in to your ECR Registry](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html) (ensure that the $AWS_REGION environment variable is set to your registry's AWS region):
  ```sh
  export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --output text | cut -f1)
  export REGISTRY_URL=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
  aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY_URL
  ```

## Build and Push Images

Our docker-compose.yaml builds all of its images from local multi-stage Dockerfile. To expose these images to ECS, we first need to build them and then push them to the ECR Repositories we created:

1. `docker compose build`
2. `docker compose push`

## Deploying Dagster

```sh
docker --context dagster-ecs compose --project-name dagster up
```

The first time you run this command, Docker will provision the necessary resources to run your stack on ECS. `--context dagster-ecs` tells Docker to run the containers on the Docker ECS context that we created. `--project-name dagster` tells Docker how to name the stack.

One of the resources Docker creates is an AWS ELB Load Balancer. You can access Dagit on port 3000 of the Load Balancer's URL. To find the Load Balancer's URL, look for the [Load Balancer tagged with our project name](https://console.aws.amazon.com/ec2/v2/home#LoadBalancers:tag:com.docker.compose.project=dagster-ecs).

Subsequent runs of this command will [execute a rolling update](https://docs.docker.com/cloud/ecs-integration/#rolling-update) of the stack.

## Destroying

Once you're done experimenting with this reference deployment, you should destroy the AWS resources it creates.

```sh
docker --context dagster-ecs compose --project-name dagster down
```

This will stop your running services and tear down any infrastructure Docker provisioned on your behalf.
