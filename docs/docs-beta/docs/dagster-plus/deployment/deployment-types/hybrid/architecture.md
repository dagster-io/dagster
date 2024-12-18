---
title: 'Dagster+ Hybrid architecture'
sidebar_position: 10
---

The Hybrid architecture is the most flexible and secure way to deploy Dagster+. It allows you to run your user code in your environment while leveraging Dagster+'s infrastructure for orchestration and metadata management

## Hybrid architecture overview

A **hybrid deployment** utilizes a combination of your infrastructure and Dagster-hosted backend services.

The Dagster backend services - including the web frontend, GraphQL API, metadata database, and daemons (responsible for executing schedules and sensors) - are hosted in Dagster+. You are responsible for running an [agent](index.md#dagster-hybrid-agents) in your environment.

![Dagster+ Hybrid deployment architecture](/images/dagster-cloud/deployment/hybrid-architecture.png)

Work is enqueued for your agent when:

- Users interact with the web front end,
- The GraphQL API is queried, or
- Schedules and sensors tick

The agent polls the agent API to see if any work needs to be done and launches user code as appropriate to fulfill requests. User code then streams metadata back to the agent API (GraphQL over HTTPS) to make it available in Dagster+.

All user code runs within your environment, in isolation from Dagster system code.

## The agent

Because the agent communicates with the Dagster+ control plane over the agent API, it's possible to support agents that operate in arbitrary compute environments.

This means that over time, Dagster+'s support for different user deployment environments will expand and custom agents can take advantage of bespoke compute environments such as HPC.

See the [setup page](index.md#dagster-hybrid-agents) for a list of agents that are currently supported.

## Security

Dagster+ Hybrid relies on a shared security model.

The Dagster+ control plane is SOC 2 Type II certified and follows best practices such as:
- encrypting data at rest (AES 256) and in transit (TLS 1.2+)
- highly available, with disaster recovery and backup strategies
- only manages metadata such as pipeline names, execution status, and run duration

The execution environment is managed by the customer:
- Dagster+ doesn't have access to user code—your code never leaves your environment. Metadata about the code is fetched over constrained APIs.
- All connections to databases, file systems, and other resources are made from your environment.
- The execution environment only requires egress access to Dagster+. No ingress is required from Dagster+ to user environments.

Additionally, the Dagster+ agent is [open source and auditable](https://github.com/dagster-io/dagster-cloud)

The following highlights are described in more detail below:

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

By default, the run worker also uploads the compute logs (raw `stdout` and `stderr` from runs) to Dagster+. If you don't want to upload logs, you can disable this feature in the [agent settings](/dagster-plus/deployment/management/settings/hybrid-agent-settings).

### Ingress

No ingress is required from Dagster+ to user environments. All network requests are outbound from user environments to Dagster+.
