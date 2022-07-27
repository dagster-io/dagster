---
title: Using Branch Deployments with Amazon ECS and GitHub Actions | Dagster Cloud
description: Develop and test in the cloud.
---

# Using Branch Deployments with Amazon ECS and GitHub Actions

Branch Deployments allow you to quickly and collaboratively develop your Dagster jobs. Testing a feature branch in your cloud environment is as simple as creating a branch in version control and kicking off a run in the corresponding Branch Deployment.

---

## Prerequisites

Utilizing Branch Deployments requires setting up two components, the Branch Deployment Agent and Continuous Integration (CI). You will need:

- Editor or Admin permissions on Dagster Cloud
- The ability to run a new Agent in your infrastructure
- Access to configure GitHub Actions or your own CI platform

---

## Step 1: Create and configure an agent

(/dagster-cloud/deployment/agents/amazon-ecs)

While you can use your existing production agent, we recommend creating a dedicated branch deployment agent. This ensures that your production instance isn't negatively impacted by the workload associated with branch deployments.

1. Create a new Amazon ECS agent:
   1. [Click here to spin up a new Amazon ECS agent](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://s3.amazonaws.com/dagster.cloud/cloudformation/ecs-agent-branch-deployments.yaml) using our CloudFormation template.

   2. Creating the CloudFormation stack may take a few minutes; refreshing the [AWS console Stacks page](https://console.aws.amazon.com/cloudformation/home#/stacks) will show its status.
2. Create an Amazon Elastic Registry (ECR) repository.
   - After the repository has been created, locate its URI and keep it somewhere handy.
    
3. Create IAM access keys.

---

## Step 2: GitHub app

---

## Step 3: Configure the GitHub repository

### Step 3.1: Add the Docker registry to cloud_workspace.yaml

In the `cloud_workspace.yaml` file, replace `build.registry` with the Docker registry used by the [agent you created in Step 1](#step-1-create-and-configure-an-agent).

For example:

```yaml
# cloud_workspace.yaml

locations:
  - location_name: example_location
    code_source:
      python_file: repo.py
    build:
      directory: ./example_location
      registry: 764506304434.dkr.ecr.us-east-1.amazonaws.com/branch-deployment-agent
```

### Step 3.2: Update GitHub Workflow files

In this step, you'll update the GitHub Workflow files in the repository to set up Docker registry access.

1. In the `.github/workflows/deploy.yml` file:

2. In the `.github/workflows/branch_deployments.yml` file:

### Step 3.3: Configure GitHub Action secrets

1. In the repository, click the **Settings** tab.
2. In the **Security** section of the sidebar, click **Secrets > Actions**.
3. Click **New repository secret**.
4. In the **Name** field, enter the name of the secret. For example, `DAGSTER_CLOUD_API_TOKEN`
5. In the **Value** field, paste the value of the secret.
6. Click **Add secret**.

Repeat steps 3-6 for each of the secrets required by your agent type.

<!-- 
ALL
	- DAGSTER_CLOUD_API_TOKEN
	- ORGANIZATION_ID

AWS ECS
	- AWS_ACCESS_KEY 
	- AWS_SECRET_ACCESS_KEY
 -->

### Step 3.4: Verify builds

---

## Step 4: 

---

## Next steps