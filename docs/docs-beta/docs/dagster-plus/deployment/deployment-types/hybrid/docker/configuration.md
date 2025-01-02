---
title: Docker agent configuration
sidebar_position: 200
---

:::note
This guide is applicable to Dagster+.
:::

{/* This reference describes the various configuration options Dagster+ currently supports for [Docker agents](/dagster-plus/deployment/agents/docker/configuring-running-docker-agent). */}
This reference describes the various configuration options Dagster+ currently supports for [Docker agents](/todo).

---

## Environment variables and secrets

Using the `container_context.docker.env_vars` property, you can include environment variables and secrets in the Docker container associated with a specific code location. For example:

```yaml
# dagster_cloud.yaml
locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      docker:
        env_vars:
          - DATABASE_NAME
          - DATABASE_USERNAME=hooli_testing
```

The `container_context.docker.env_vars` property is a list, where each item can be either `KEY` or `KEY=VALUE`. If only `KEY` is specified, the value will be pulled from the local environment.

Refer to the following guides for more info about environment variables:

{/* - [Dagster+ environment variables and secrets](/dagster-plus/managing-deployments/environment-variables-and-secrets) */}
- [Dagster+ environment variables and secrets](/todo)
{/* - [Using environment variables and secrets in Dagster code](/guides/dagster/using-environment-variables-and-secrets) */}
- [Using environment variables and secrets in Dagster code](/todo)

