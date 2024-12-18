---
title: "Hybrid deployment"
sidebar_label: Hybrid
sidebar_position: 20
---

In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment.

:::note
For an overview of the Hybrid design, including security considerations, see [Dagster+ Hybrid architecture](architecture.md).
:::

## Get started

To get started with a Hybrid deployment, you'll need to:

1. Create a [Dagster+ organization](https://dagster.cloud/signup)
2. [Install a Dagster+ Hybrid agent](#dagster-hybrid-agents)
3. [Add a code location](/dagster-plus/deployment/code-locations), typically using a Git repository and CI/CD

## Dagster+ Hybrid agents

The Dagster+ agent is a long-lived process that polls Dagster+'s API servers for new work. Currently supported agents include:

 - [Kubernetes](/dagster-plus/deployment/deployment-types/hybrid/kubernetes)
 - [AWS ECS](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs/new-vpc)
 - [Docker](/dagster-plus/deployment/deployment-types/hybrid/docker)
 - [Local agent](/dagster-plus/deployment/deployment-types/hybrid/local)


## What you'll see in your environment

### Code location servers

Dagster+ runs your Dagster projects through code locations. To get started, follow this guide for [adding a code location](/dagster-plus/deployment/code-locations).

When you inform Dagster+ about a new code location, we enqueue instructions for your agent to launch a new code server. The agent uses your container image to launch a code server that interacts with your Dagster definitions. The agent will run one long-standing code server for each code location. Once the code server is running, the agent will send Dagster+ metadata about your Dagster definitions that Dagster+ uses to make orchestration decisions.


### Runs

Your definitions might include [automations](/guides/automate) that launch runs or materialize assets. Or your developers might launch runs directly with the web UI.

When a run needs to be launched, Dagster+ enqueues instructions for your agent to launch a new run. The next time your agent polls Dagster+ for new work, it will see instructions about how to launch your run. It will delegate those instructions to your code server and your code server will launch a run - a new run will typically require its own container.

Your agent will send Dagster+ metadata letting us know the run has been launched. Your run's container will also send Dagster+ metadata informing us of how the run is progressing. The Dagster+ backend services will monitor this stream of metadata to make additional orchestration decisions, monitor for failure, or send alerts.

## Best practices

### Security

You can do the following to make your Dagster+ Hybrid deployment more secure:
- [Disable log forwarding](/dagster-plus/deployment/management/settings/customizing-agent-settings#disabling-compute-logs)
- [Manage tokens](/dagster-plus/deployment/management/tokens/agent-tokens)
