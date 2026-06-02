---
title: Set up Kubernetes agents
description: Install and configure Dagster+ hybrid agents with Helm for each environment
sidebar_position: 30
---

Dagster+ Hybrid runs a lightweight agent in your Kubernetes cluster. The agent polls Dagster+ for work, launches run pods, and streams logs back — your code never leaves your infrastructure.

Each environment gets its own agent installed in its own namespace, with values files that reflect the environment's resource requirements.

## Step 1: Add the Helm chart repository

```shell
helm repo add dagster-cloud https://dagster-io.github.io/helm-user-cloud
helm repo update
```

## Step 2: Create agent tokens

Each agent authenticates with an API token scoped to its deployment. Create a token for each environment in the Dagster+ UI under **Organization Settings → Tokens**, then store each token as a Kubernetes secret:

```shell
kubectl create namespace dagster-dev
kubectl create secret generic dagster-cloud-agent-token \
  --from-literal=DAGSTER_CLOUD_AGENT_TOKEN=<dev-token> \
  -n dagster-dev

kubectl create namespace dagster-staging
kubectl create secret generic dagster-cloud-agent-token \
  --from-literal=DAGSTER_CLOUD_AGENT_TOKEN=<staging-token> \
  -n dagster-staging

kubectl create namespace dagster-prod
kubectl create secret generic dagster-cloud-agent-token \
  --from-literal=DAGSTER_CLOUD_AGENT_TOKEN=<prod-token> \
  -n dagster-prod
```

## Step 3: Create environment secrets for user code

The Helm values files reference a per-environment Kubernetes secret (`dagster-dev-env`, `dagster-staging-env`, `dagster-prod-env`) that injects connection strings into run pods. Create these secrets now, substituting your actual connection details:

```shell
kubectl create secret generic dagster-dev-env \
  -n dagster-dev \
  --from-literal=SOURCE_DATABASE_URL='postgres://dev-host/mydb' \
  --from-literal=WAREHOUSE_URL='snowflake://dev/warehouse'

kubectl create secret generic dagster-staging-env \
  -n dagster-staging \
  --from-literal=SOURCE_DATABASE_URL='postgres://staging-host/mydb' \
  --from-literal=WAREHOUSE_URL='snowflake://staging/warehouse'

kubectl create secret generic dagster-prod-env \
  -n dagster-prod \
  --from-literal=SOURCE_DATABASE_URL='postgres://prod-host/mydb' \
  --from-literal=WAREHOUSE_URL='snowflake://prod/warehouse'
```

These values are automatically available as environment variables in every run pod. The assets read them with `os.getenv("SOURCE_DATABASE_URL")` and `os.getenv("WAREHOUSE_URL")`, so each environment targets its own data sources without any code changes.

## Step 4: Configure each environment

The Helm values files capture the differences between environments. Common things to tune per environment: replica count, run resource limits, server TTL, branch deployment support, and which node pool to schedule on.

### Dev

The dev agent runs a single replica, reclaims idle servers quickly, and serves branch deployments:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/helm/dagster-agent/values-dev.yaml"
  language="yaml"
  title="helm/dagster-agent/values-dev.yaml"
/>

### Staging

Staging mirrors prod behavior but with lighter resources. Branch deployments are disabled — only code merged to `staging` is tested here:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/helm/dagster-agent/values-staging.yaml"
  language="yaml"
  title="helm/dagster-agent/values-staging.yaml"
/>

### Prod

Prod runs two agent replicas for high availability. The server TTL is long (24 h) to keep code servers warm, and a Pod Disruption Budget (PDB) prevents the agent from being evicted during node maintenance:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/helm/dagster-agent/values-prod.yaml"
  language="yaml"
  title="helm/dagster-agent/values-prod.yaml"
/>

## Step 5: Install the agents

Run `helm upgrade --install` for each environment. Using `--install` means the same command works for both the initial install and future upgrades:

```shell
# Dev
helm upgrade --install dagster-agent-dev dagster-cloud/dagster-cloud-agent \
  -n dagster-dev --create-namespace \
  -f helm/dagster-agent/values-dev.yaml

# Staging
helm upgrade --install dagster-agent-staging dagster-cloud/dagster-cloud-agent \
  -n dagster-staging --create-namespace \
  -f helm/dagster-agent/values-staging.yaml

# Prod
helm upgrade --install dagster-agent-prod dagster-cloud/dagster-cloud-agent \
  -n dagster-prod --create-namespace \
  -f helm/dagster-agent/values-prod.yaml
```

## Step 6: Verify the agents are running

Check that the agent pods started and connected to Dagster+:

```shell
kubectl get pods -n dagster-dev
kubectl logs -n dagster-dev -l app=dagster-cloud-agent --tail=50
```

In the Dagster+ UI, navigate to **Deployment → Agents** and confirm each agent shows as **Active**.

:::tip

If you're using Workload Identity (GKE) or IAM Roles for Service Accounts (EKS), add the appropriate annotation to the `serviceAccount.annotations` field in each values file. This lets run pods access cloud resources (e.g., BigQuery, S3) without storing credentials as secrets.

:::

## Next steps

Continue this example with [setting up CI/CD](/examples/full-pipelines/dagster-plus-deployment/cicd).
