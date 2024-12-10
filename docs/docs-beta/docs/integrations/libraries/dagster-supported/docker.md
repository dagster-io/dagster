---
layout: Integration
status: published
name: Docker
title: Dagster & Docker
sidebar_label: Docker
excerpt: Run runs external processes in docker containers directly from Dagster.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-docker
docslink:
partnerlink: https://www.docker.com/
logo: /integrations/Docker.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-docker` integration library provides the `PipesDockerClient` resource, enabling you to launch Docker containers and execute external code directly from Dagster assets and ops. This integration allows you to pass parameters to Docker containers while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster-docker
```

### Example

<CodeExample filePath="integrations/docker.py" language="python" />

### Deploying to Docker?

- Deploying to Dagster+: Use with a Dagster+ Hybrid deployment, the Docker agent executes Dagster jobs on a Docker cluster. Checkout the [Dagster+ Docker Agent](https://docs.dagster.io/dagster-plus/deployment/agents/docker) guide for more information.
- Deploying to Open Source: Visit the [Deploying Dagster to Docker](https://docs.dagster.io/deployment/guides/docker) guide for more information.

### About Docker

**Docker** is a set of platform-as-a-service products that use OS-level virtualization to deliver software in packages called containers. The service has both free and premium tiers. The software that hosts the containers is called Docker Engine.
