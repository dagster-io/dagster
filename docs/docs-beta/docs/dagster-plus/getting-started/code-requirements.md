---
title: 'Code requirements'
displayed_sidebar: 'dagsterPlus'
---

# Code requirements

Your Dagster project must meet a few requirements to run in Dagster+.

:::info
**Learn by example?** Check out [an example repo](https://github.com/dagster-io/hooli-data-eng-pipelines) which is set up to run in Dagster+.
:::

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Python project structure and Docker.
- Familiarity with [deploying open source Dagster](/guides/deployment).
</details>

---

To work with Dagster+, your Dagster code:

- **Must be loaded from a single entry point: either a Python file or package.** This entry point can load repositories from other files or packages.

- **Must run in an environment where the `dagster` and `dagster-cloud` 0.13.2 or later Python packages are installed.**

- **If using [Hybrid Deployment](/dagster-plus/deployment/hybrid)**:

  - **And you're using an Amazon Elastic Container Service (ECS), Kubernetes, or Docker agent**, your code must be packaged into a Docker image and pushed to a registry your agent can access. Dagster+ doesn't need access to your image - only your agent needs to be able to pull it.

    Additionally, the Dockerfile for your image doesn't need to specify an entry point or command. These will be supplied by the agent when it runs your code using your supplied image.

  - **And you're using a local agent**, your code must be in a Python environment that can be accessed on the same machine as your agent.

**Note:**:

- Your code doesn't need to use the same version of Dagster as your agent
- Different code locations can use different versions of Dagster
- Dagster+ doesn't require a [`workspace.yaml` file](/todo). You can still create a `workspace.yaml` file to load your code in an open source Dagster webserver instance, but doing so won't affect how your code is loaded in Dagster+.
