---
description: dagster-cloud CLI reference
sidebar_position: 200
title: dagster-cloud CLI reference
---

## Custom configuration file path

Point the CLI at an alternate config location by specifying the `DAGSTER_CLOUD_CLI_CONFIG` environment variable.

## Environment variables and CLI options

Environment variables and CLI options can be used in place of or to override the CLI configuration file.

The priority of these items is as follows:

- **CLI options** - highest
- **Environment variables**
- **CLI configuration** - lowest

| Setting      | Environment variable         | CLI flag               | CLI config value     |
| ------------ | ---------------------------- | ---------------------- | -------------------- |
| Organization | `DAGSTER_CLOUD_ORGANIZATION` | `--organization`, `-o` | `organization`       |
| Deployment   | `DAGSTER_CLOUD_DEPLOYMENT`   | `--deployment`, `-d`   | `default_deployment` |
| User Token   | `DAGSTER_CLOUD_API_TOKEN`    | `--user-token`, `-u`   | `user_token`         |
