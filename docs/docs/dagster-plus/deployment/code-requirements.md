---
description: Dagster+ code must load from a single entry point and be able to be run in an environment where the dagster and dagster-cloud 0.13.2+ Python packages are installed, plus meet additional requirements for hybrid deployments.
sidebar_label: Code requirements
sidebar_position: 10
title: Dagster+ code requirements
---

Your Dagster project must meet a few requirements to run in Dagster+.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Python project structure and Docker

</details>

## General requirements

:::tip
**Learn by example?** Check out [an example repo](https://github.com/dagster-io/hooli-data-eng-pipelines) which is set up to run in Dagster+.
:::

To work with Dagster+, your Dagster code:

- **Must be loaded from a single entry point: either a Python file or package.** This entry point can load repositories from other files or packages.

- **Must run in an environment where the `dagster` and `dagster-cloud` 0.13.2 or later Python packages are installed.**

**Note**:

- Different code locations can use different versions of Dagster
- Dagster+ doesn't require a [`workspace.yaml` file](/guides/deploy/code-locations/workspace-yaml). You can still create a `workspace.yaml` file to load your code in an open source Dagster webserver instance, but doing so won't affect how your code is loaded in Dagster+.

## Hybrid deployment requirements

If you're using [Hybrid Deployment](/dagster-plus/deployment/deployment-types/hybrid), there are a few additional requirements.

- **If using an Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent**, your code must be packaged into a Docker image and pushed to a registry your agent can access. Dagster+ doesn't need access to your image - the agent only needs to be able to pull it.

  Additionally, the Dockerfile for your image doesn't need to specify an entry point or command. These will be supplied by the agent when it runs your code using the supplied image.

- **If using a local agent**, your code must be in a Python environment that can be accessed on the same machine as your agent.

Additionally, your code doesn't need to use the same version of Dagster as your agent.
