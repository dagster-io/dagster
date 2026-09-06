---
description: In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment.
sidebar_label: Hybrid deployment
sidebar_position: 500
title: Dagster+ Hybrid deployment
canonicalUrl: '/deployment/dagster-plus/hybrid'
slug: '/deployment/dagster-plus/hybrid'
tags: [dagster-plus-feature]
---

import HybridResources from '@site/docs/partials/\_HybridResources.md';
import HybridAgentRecommendation from '@site/docs/partials/\_HybridAgentRecommendation.md';

In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment. Hybrid deployments are containerized: your code runs inside containers managed by an agent you operate. Kubernetes is a common choice, but not required. The Docker agent provides a lighter-weight alternative for teams that don't need Kubernetes orchestration.

For an overview of the Hybrid design, including security considerations, see [Dagster+ Hybrid architecture](/deployment/dagster-plus/hybrid/architecture).

## Getting started

To get started with a Hybrid deployment, you'll need to:

1. Create a [Dagster+ organization](https://dagster.cloud/signup).
2. Install a Dagster+ Hybrid [agent](/deployment/dagster-plus/hybrid/architecture#the-agent) in your environment:
   - [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes) (supports AKS on Azure, EKS on AWS, GKE on GCP, and other clusters)
   - [AWS ECS](/deployment/dagster-plus/hybrid/amazon-ecs/new-vpc)
   - [Docker](/deployment/dagster-plus/hybrid/docker) (runs containers directly without Kubernetes; can be paired with Azure Container Registry (ACR) on an Azure VM for a lightweight Azure setup)
   - [Microsoft Azure](/deployment/dagster-plus/hybrid/azure)
3. [Create a Dagster project](/guides/build/projects/creating-projects) and add it to your deployment, typically using a [Git repository and CI/CD](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

<HybridAgentRecommendation />

:::note

If you are migrating from from Dagster+ Serverless, see the [Dagster+ Serverless to Hybrid migration guide](/migration/serverless-to-hybrid).

:::

## Run isolation

Dagster+ Hybrid deployments support both isolated and non-isolated runs. Isolated runs execute in their own container with dedicated resources, while non-isolated runs use the persistent code location server for faster iteration during development or for time-sensitive jobs that don't require extensive compute. Because you control the code location server's resources in Hybrid, you can size them for the non-isolated runs you expect; running these jobs from a dedicated code location is recommended so they don't impact other processes. For details, see [Run isolation](/deployment/dagster-plus/run-isolation).

## Best practices

### Recommended compute resources

<HybridResources />

### Security

To make your Dagster+ Hybrid deployment more secure, you can:

- [Disable log forwarding](/deployment/dagster-plus/management/customizing-agent-settings#disabling-compute-logs)
- [Manage tokens](/deployment/dagster-plus/management/tokens/agent-tokens)

## Frequently asked questions

### Can the Dagster+ agent and code location versions be different?

Yes. The agent and code location versions can be updated independently, but they must follow a specific upgrade order:

- Always upgrade the agent **before** upgrading code locations. The agent maintains backward compatibility with older code versions.
- Never use a code location version that is newer than your agent version, as this can cause compatibility issues.
