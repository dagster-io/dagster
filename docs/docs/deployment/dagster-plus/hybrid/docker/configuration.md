---
description: Configure Docker agents in Dagster+.
sidebar_position: 4200
title: Docker agent configuration
tags: [dagster-plus-feature]
---

This reference describes the various configuration options Dagster+ currently supports for Docker agents.

## Per-location configuration

For per-location Docker configuration, create a `container_context.yaml` file in your project directory. This file contains agent-specific runtime settings like environment variables.

For a complete overview of the configuration file structure, see the [Deployment configuration reference](/deployment/dagster-plus/management/build-yaml).

## Environment variables and secrets

Using the `docker.env_vars` property in your `container_context.yaml`, you can include environment variables and secrets in the Docker container associated with a specific code location. For example:

```yaml
# container_context.yaml
docker:
  env_vars:
    - DATABASE_NAME
    - DATABASE_USERNAME=hooli_testing
```

:::note

Older deployments may use a `dagster_cloud.yaml` file with a `locations` key that embeds `container_context` within each location. This legacy format is still supported. See the [Deployment configuration reference](/deployment/dagster-plus/management/build-yaml#legacy-format-dagster_cloudyaml) for migration guidance.

:::

The `docker.env_vars` property is a list, where each item can be either `KEY` or `KEY=VALUE`. If only `KEY` is specified, the value will be pulled from the local environment.

Refer to the following guides for more info about environment variables:

- [Dagster+ environment variables and secrets](/deployment/dagster-plus/management/environment-variables)
- [Using environment variables and secrets in Dagster code](/guides/operate/configuration/using-environment-variables-and-secrets)
