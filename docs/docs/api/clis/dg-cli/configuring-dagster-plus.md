---
description: Authenticate and configure the dg CLI for Dagster+.
title: Configuring Dagster+ with the dg CLI
sidebar_position: 5000
---

The `dg` CLI includes built-in commands for authenticating with Dagster+ and managing your configuration. This guide covers how to log in, set configuration, and view your current settings.

:::note Prerequisites

- Python 3.10+
- The `dg` CLI installed. See the [dg CLI reference](/api/clis/dg-cli/dg-cli-reference) for installation instructions.

:::

## Logging in

The simplest way to configure the `dg` CLI for Dagster+ is to log in interactively:

```shell
dg plus login
```

This opens your browser to authenticate, then prompts you to select a default deployment. Your credentials are saved to `~/.dagster_cloud_cli/config`.

For EU-hosted Dagster+ organizations, use the `--region` flag:

```shell
dg plus login --region eu
```

## Setting config non-interactively

For CI/CD pipelines and automation, you can set configuration without interactive prompts:

```shell
dg plus config set --api-token <TOKEN> --organization <ORG> --deployment prod
```

Available options:

| Option           | Description                |
| ---------------- | -------------------------- |
| `--api-token`    | Dagster+ API token         |
| `--organization` | Dagster+ organization name |
| `--deployment`   | Default deployment name    |
| `--url`          | Dagster+ URL               |
| `--region`       | Region (`us` or `eu`)      |

You can also use environment variables instead of the configuration file:

| Environment variable         | Description        |
| ---------------------------- | ------------------ |
| `DAGSTER_CLOUD_API_TOKEN`    | API token          |
| `DAGSTER_CLOUD_ORGANIZATION` | Organization name  |
| `DAGSTER_CLOUD_DEPLOYMENT`   | Default deployment |

## Viewing config

To view your current configuration:

```shell
dg plus config view
```

This displays your organization, deployment, and a censored API token. To show the full token:

```shell
dg plus config view --show-token
```

## Switching deployments

To switch your default deployment:

```shell
dg plus config set --deployment <deployment_name>
```

## Configuration file location

The `dg` CLI stores Dagster+ configuration at `~/.dagster_cloud_cli/config`. This file is shared with the `dagster-cloud` CLI, so logging in with either tool configures both.

## Migrating from the dagster-cloud CLI

If you're currently using the `dagster-cloud` CLI, here's how the commands map:

| dagster-cloud CLI                     | dg CLI                                  |
| ------------------------------------- | --------------------------------------- |
| `dagster-cloud config setup`          | `dg plus login` or `dg plus config set` |
| `dagster-cloud config view`           | `dg plus config view`                   |
| `dagster-cloud config set-deployment` | `dg plus config set --deployment`       |
