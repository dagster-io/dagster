---
title: 'Dagster+ Hybrid architecture'
displayed_sidebar: 'dagsterPlus'
sidebar_position: 10
---

# Dagster+ Hybrid architecture

The Hybrid architecture is the most flexible and secure way to deploy Dagster+. It allows you to run your user code in your environment while leveraging Dagster+'s infrastructure for orchestration and metadata management

<details>
  <summary>Pre-requisites</summary>

Before you begin, you should have:

- A [Dagster+ account](/dagster-plus/getting-started)
- [Basic familiarity with Dagster](/getting-started/quickstart)

</details>

---

## Hybrid architecture overview

A **hybrid deployment** utilizes a combination of your infrastructure and Dagster-hosted backend services.

The Dagster backend services - including the web frontend, GraphQL API, metadata database, and daemons (responsible for executing schedules and sensors) - are hosted in Dagster+. You are responsible for running an [agent](/todo) in your environment.

![Dagster+ Hybrid deployment architecture](/img/placeholder.svg)

Work is enqueued for your agent when:

- Users interact with the web front end,
- The GraphQL API is queried, or
- Schedules and sensors tick

The agent polls the agent API to see if any work needs to be done and launches user code as appropriate to fulfill requests. User code then streams metadata back to the agent API (GraphQL over HTTPS) to make it available in Dagster+.

All user code runs within your environment, in isolation from Dagster system code.

---

## The agent

Because the agent communicates with the Dagster+ control plane over the agent API, it's possible to support agents that operate in arbitrary compute environments.

This means that over time, Dagster+'s support for different user deployment environments will expand and custom agents can take advantage of bespoke compute environments such as HPC.

Refer to the [Agents documentation](/todo) for more info, including the agents that are currently supported.

---

## Security

This section describes how Dagster+ interacts with user code. To summarize:

- No ingress is required from Dagster+ to user environments
- Dagster+ doesn't have access to user code. Metadata about the code is fetched over constrained APIs.
- The Dagster+ agent is [open source and auditable](https://github.com/dagster-io/dagster-cloud)

These highlights are described in more detail below:

- [Interactions and queries](#interactions-and-queries)
- [Runs](#runs)
- [Ingress](#ingress)

### Interactions and queries

When Dagster+ needs to interact with user code - for instance, to display the structure of a job in the Dagster+ user interface, to run the body of a sensor definition, or to launch a run for a job - it enqueues a message for the Dagster+ Agent. The Dagster+ Agent picks up this message and then launches or queries user code running on the appropriate compute substrate.

Depending on the agent implementation, user code may run in isolated OS processes, in Docker containers, in ECS Tasks, in Kubernetes Jobs and Services, or in a custom isolation strategy.

Queries to user code run over a well-defined gRPC interface. Dagster+ uses this interface to:

- Retrieve the names, config schemas, descriptions, tags, and structures of jobs, ops, repositories, partitions, schedules, and sensors defined in your code
- Evaluate schedule and sensor ticks and determine whether a run should be launched

When the agent queries user code, it writes the response back to Dagster+ over a well-defined GraphQL interface.

### Runs

Runs are launched by calling the `dagster api` CLI command in a separate process/container as appropriate to the agent type. Run termination is handled by interrupting the user code process/container as appropriate for the compute substrate.

When runs are launched, the user code process/container streams structured metadata (containing everything that's viewable in the integrated logs viewer in the Dagster+ UI) back to Dagster+ over a well-defined GraphQL interface. Structured metadata is stored in Amazon RDS, encrypted at rest.

By default, the run worker also uploads the compute logs (raw `stdout` and `stderr` from runs) to Dagster+. If you don't want to upload logs, you can disable this feature in the [agent settings](/dagster-plus/deployment/hybrid/agents/settings).

### Ingress

No ingress is required from Dagster+ to user environments. All network requests are outbound from user environments to Dagster+.
