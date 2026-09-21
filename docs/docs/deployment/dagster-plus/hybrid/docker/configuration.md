---
description: Configure Docker agents in Dagster+.
sidebar_position: 4200
title: Docker agent configuration
tags: [dagster-plus-feature]
---

This reference describes the various configuration options Dagster+ currently supports for Docker agents.

## Environment variables and secrets

Using the `docker.env_vars` property in [`container_context.yaml`](/deployment/dagster-plus/management/build-yaml#container_contextyaml), you can include environment variables and secrets in the Docker container associated with a specific code location. For example:

```yaml
# container_context.yaml
docker:
  env_vars:
    - DATABASE_NAME
    - DATABASE_USERNAME=hooli_testing
```

The `docker.env_vars` property is a list, where each item can be either `KEY` or `KEY=VALUE`. If only `KEY` is specified, the value will be pulled from the local environment.

Refer to the following guides for more info about environment variables:

- [Dagster+ environment variables and secrets](/deployment/dagster-plus/management/environment-variables)
- [Using environment variables and secrets in Dagster code](/guides/operate/configuration/using-environment-variables-and-secrets)
