---
title: "Hybrid deployment"
displayed_sidebar: "dagsterPlus"
sidebar_position: 2
---

# Hybrid deployment

In a Dagster+ Hybrid deployment, the orchestration control plane is run by Dagster+ while your Dagster code is executed within your environment.

[comment]: <> (TODO: Architecture diagram)

## Get started

To get started with a Hybrid deployment you'll need to:

1. Create a [Dagster+ organization](https://dagster.cloud/signup)
2. Install a Dagster+ Hybrid Agent
3. [Add a code location](/dagster-plus/deployment/code-locations), typically using a Git repository and CI/CD

## Dagster+ Hybrid agents

The Dagster+ agent is a long-lived process that polls Dagster+'s API servers for new work.

See the following guides for setting up an agent:
 - [Kubernetes](/dagster-plus/deployment/hybrid/agents/kubernetes)
 - [AWS ECS](/dagster-plus/deployment/hybrid/agents/amazon-ecs-new-vpc)
 - [Docker](/dagster-plus/deployment/hybrid/agents/docker)
 - [Locally](/dagster-plus/deployment/hybrid/agents/local)


## What you'll see in your environment

### Code location servers

Dagster+ runs your Dagster projects through code locations. To get started, follow this guide for [adding a code location](/dagster-plus/deployment/code-locations).

When you inform Dagster+ about a new code location, we enqueue instructions for your agent to launch a new code server. The agent uses your container image to launch a code server that interacts with your Dagster definitions. The agent will run one long-standing code server for each code location. Once the code server is running, the agent will send Dagster+ metadata about your Dagster definitions that Dagster+ uses to make orchestration decisions.


### Runs

Your definitions might include [automations](/guides/automation) that launch runs or materialize assets. Or your developers might launch runs directly with the web UI.

When a run needs to be launched, Dagster+ enqueues instructions for your agent to launch a new run. The next time your agent polls Dagster+ for new work, it will see instructions about how to launch your run. It will delegate those instructions to your code server and your code server will launch a run - a new run will typically require its own container.

Your agent will send Dagster+ metadata letting us know the run has been launched. Your run's container will also send Dagster+ metadata informing us of how the run is progressing. The Dagster+ backend services will monitor this stream of metadata to make additional orchestration decisions, monitor for failure, or send alerts.

## Security

Dagster+ hybrid relies on a shared security model.

The Dagster+ control plane is SOC 2 Type II certified and follows best practices such as:
- encrypting data at rest (AES 256) and in transit (TLS 1.2+)
- highly available, with disaster recovery and backup strategies
- only manages metadata such as pipeline names, execution status, and run duration

The execution environment is managed by the customer:
- your code never leaves your environment
- all connections to databases, file systems, and other resources are made from your environment
- the execution environment only requires egress access to Dagster+

Common security considerations in Dagster+ hybrid include:
- [disabling log forwarding](/todo)
- [managing tokens](/todo)
