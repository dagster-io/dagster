---
title: "What's Dagster+?"
displayed_sidebar: "dagsterPlus"
sidebar_position: 1
---

# What's Dagster+?

Dagster+ is a managed orchestration platform built on top of Dagster's open source engine.

We run:
 - Dagster's web UI at https://dagster.plus
 - API servers at https://agent.dagster.plus
 - Metadata stores for data cataloging and cost insights
 - Backend services for orchestration, alerting, and more

You run:
 - Agents that listen to our API servers for new work
 - The compute resource for  your data assets

TODO: Architecture diagram?

## Agents

The Dagster+ agent is a long-lived process that polls Dagster+'s API servers for new work.

To run an agent, first grab a Dagster+ agent token. Next, launch an agent:

```
dagster-cloud agent run --agent-token=<your token>
```

We have guides for running your agents on:
 - [Kubernetes](guides/deployment/kubernetes)
 - [AWS ECS](/guides/deployment/ecs)
 - [Docker](/guide/deployment/docker)

And if operating additional infrastructure isn't your thing, we also offer [Dagster+ Serverless](/concepts/dagster-plus/deployment/serverless/): a fully managed Dagster+ offering where we'll run your agent and compute too.

### Managing code locations

When you inform Dagster+ about a new code location, we enqueue instructions for your agent to launch a new code server.

For example, let's add a code location. We include the name of the code location and a container image with our Dagster definitions:

TODO: Screenshot adding a code location

The next time your agent polls Dagster+ for new work, it will see instructions about how to launch your code location. Your agent uses your container image to launch a code server that it can use to interact with your Dagster definitions. Once the code server is running, your agent will send Dagster+ metadata about your Dagster definitions that we'll use to make orchestration decisions.

For more on code locations, see [Managing code locations with definitions](/guides/deployment/code-locations.md).

### Launching runs

Your definitions might include [automations](/guides/automation) that launch runs or materialize assets. Or your developers might launch runs directly with the web UI.

When a run needs to be launched, we enqueue instructions for your agents to launch a new run.

The next time your agent polls Dagster+ for new work, it will see instructions about how to launch your run. It will delegate those instructions to your code server and your code server will launch a run - typically in its own container.

Your agent will send Dagster+ metadata letting us know the run has been launched. Your run. Your run's container will send Dagster+ metadata informing us of how the run is progressing. Our backend services will monitor this stream of metadata to make additional orchestration decisions, monitor for failure, or send alerts.
