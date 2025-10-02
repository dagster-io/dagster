---
description: In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment.
sidebar_label: Hybrid deployment
sidebar_position: 400
title: Dagster+ Hybrid deployment
canonicalUrl: '/deployment/dagster-plus/hybrid'
slug: '/deployment/dagster-plus/hybrid'
tags: [dagster-plus-feature]
---

In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment.

For an overview of the Hybrid design, including security considerations, see [Dagster+ Hybrid architecture](/deployment/dagster-plus/hybrid/architecture).

## Getting started

To get started with a Hybrid deployment, you'll need to:

1. Create a [Dagster+ organization](https://dagster.cloud/signup).
2. Install a Dagster+ Hybrid [agent](/deployment/dagster-plus/hybrid/architecture#the-agent) in your environment:
    - [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes)
    - [AWS ECS](/deployment/dagster-plus/hybrid/amazon-ecs/new-vpc)
    - [Docker](/deployment/dagster-plus/hybrid/docker)
    - [Microsoft Azure](/deployment/dagster-plus/hybrid/azure)
3. [Add a code location](/deployment/code-locations/dagster-plus-code-locations) to your deployment, typically using a [Git repository and CI/CD](/deployment/dagster-plus/ci-cd/ci-cd-in-hybrid).

:::tip

If you're not sure which agent to use, we recommend the [Dagster+ Kubernetes agent](/deployment/dagster-plus/hybrid/kubernetes) in most cases.

:::

:::note

If you are migrating from from Dagster+ Serverless, see the [Dagster+ Serverless to Hybrid migration guide](/migration/serverless-to-hybrid).

:::

## Best practices

### Recommended compute resources

- **Agent:** 256 CPU, 1024 memory
- **Code server:** 256 CPU, 1024 memory
- **Runs:** 4 vCPU cores, 8-16 GB of RAM depending on the workload

### Security

To make your Dagster+ Hybrid deployment more secure, you can:

- [Disable log forwarding](/deployment/dagster-plus/management/customizing-agent-settings#disabling-compute-logs)
- [Manage tokens](/deployment/dagster-plus/management/tokens/agent-tokens)

