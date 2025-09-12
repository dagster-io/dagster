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

:::info

For an overview of the Hybrid design, including security considerations, see [Dagster+ Hybrid architecture](/deployment/dagster-plus/hybrid/architecture).

:::

## Get started

To get started with a Hybrid deployment, you'll need to:

1. Create a [Dagster+ organization](https://dagster.cloud/signup)
2. [Install a Dagster+ Hybrid agent](#dagster-hybrid-agents)
3. [Add a code location](/deployment/code-locations), typically using a Git repository and CI/CD

:::note

If you are migrating from from Dagster+ Serverless, see the [Dagster+ Serverless to Hybrid migration guide](/migration/serverless-to-hybrid).

:::

## Dagster+ Hybrid agents

The Dagster+ agent is a long-lived process that polls Dagster+'s API servers for new work. Currently supported agents include:

- [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes)
- [AWS ECS](/deployment/dagster-plus/hybrid/amazon-ecs/new-vpc)
- [Docker](/deployment/dagster-plus/hybrid/docker)
- [Microsoft Azure](/deployment/dagster-plus/hybrid/azure)
- [Local agent](/deployment/dagster-plus/hybrid/local)

:::tip

If you're not sure which agent to use, we recommend the [Dagster+ Kubernetes agent](/deployment/dagster-plus/hybrid/kubernetes) in most cases.

:::

## What you'll see in your environment

### Agent

The Dagster+ agent acts as a message relay and executor that picks up messages from Dagster+ and launches or queries your user code.

#### Infrastructure management

- Launches and manages code servers for each code location
- Launches run workers (new containers/processes) when runs need to be executed
- Acts as the run launcher, spinning up isolated tasks/pods/processes for each run

#### Communication

- Receives messages and instructions from Dagster+ about what work needs to be done
- Sends metadata back to Dagster+ about launched runs and code server status

### Code location servers

Dagster+ runs your Dagster projects through code locations. To add a code location, see the [code locations documentation](/deployment/code-locations).

When you inform Dagster+ about a new code location, we enqueue instructions for your agent to launch a new code server. The agent uses your container image to launch a code server that interacts with your Dagster definitions. The agent will run one long-standing code server for each code location. Once the code server is running, the agent will send Dagster+ metadata about your Dagster definitions that Dagster+ uses to make orchestration decisions.

### Runs

Your definitions might include [automations](/guides/automate) that launch runs or materialize assets. Or your developers might launch runs directly with the web UI.

When a run needs to be launched, Dagster+ enqueues instructions for your agent to launch a new run. The next time your agent polls Dagster+ for new work, it will see instructions about how to launch your run. It will delegate those instructions to your code server and your code server will launch a run - a new run will typically require its own container.

Your agent will send Dagster+ metadata letting us know the run has been launched. Your run's container will also send Dagster+ metadata informing us of how the run is progressing. The Dagster+ backend services will monitor this stream of metadata to make additional orchestration decisions, monitor for failure, or send alerts.

## Best practices

### Security

You can do the following to make your Dagster+ Hybrid deployment more secure:

- [Disable log forwarding](/deployment/dagster-plus/management/customizing-agent-settings#disabling-compute-logs)
- [Manage tokens](/deployment/dagster-plus/management/tokens/agent-tokens)

### Recommended compute resources for new Dagster+ deployment

- Agent: 256 CPU, 1024 memory
- Code server: 256 CPU, 1024 memory
- Runs: 4 vCPU cores, 8-16 GB of RAM depending on the workload
