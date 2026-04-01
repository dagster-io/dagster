---
title: Deploying to both Serverless and Hybrid code locations
description: Deploy both Dagster+ Serverless and Hybrid code locations from a single repository using agent queues and separate CI/CD workflows.
sidebar_position: 9000
tags: [dagster-plus-feature]
---

Deploy both Dagster+ Serverless and Hybrid code locations from a single repository using agent queues and separate CI/CD workflows.

Serverless code locations require no additional deployment configuration. Hybrid code locations need a `build.yaml` to configure Docker image builds, and `agent_queue` set in [`pyproject.toml`](/api/clis/dg-cli/dg-cli-configuration#project-configuration-file) to route to the correct agent.

## Prerequisites

- A repository containing the code for both Serverless and Hybrid code locations
- An agent configured to serve the Hybrid queue. For details, see [Routing requests to specific agents](/deployment/dagster-plus/hybrid/multiple#routing-requests-to-specific-agents).

:::note

Agent queues are a Dagster+ Pro feature.

:::

## Step 1: Configure the Hybrid code location

Add a `build.yaml` to the directory containing the Hybrid code location. The Hybrid location uses Docker images and routes to a dedicated agent queue.

The `build.registry` field specifies where the Docker image is stored.

```yaml title="build.yaml"
locations:
  - location_name: hybrid-location
    code_source:
      package_name: hybrid_location.definitions
    working_directory: ./src/
    build:
      registry: ghcr.io/my-org/my-repo/hybrid-location
```

Configure `agent_queue` in `pyproject.toml` to route this location to agents serving that queue name:

```toml title="pyproject.toml"
[tool.dg.project]
root_module = "hybrid_location"
agent_queue = "hybrid-queue"
```

For a full `build.yaml` specification, see the [build.yaml reference](/deployment/dagster-plus/management/build-yaml).

## Full working example

A complete example is available in the [Dagster repository](https://github.com/dagster-io/dagster/tree/master/examples/docs_projects/project_serverless_hybrid).
