---
title: "Running a Dagster+ agent locally"
displayed_sidebar: "dagsterPlus"
sidebar_position: 40
sidebar_label: "Local"
---

# Running a Dagster+ agent locally

This page provides instructions for running the [Dagster+ agent](dagster-plus/getting-started/whats-dagster-plus#Agents) locally. Local agents aren't well-suited for production deployments and are typically only used for development or experimentation.

## Installation


### Step 1: Install dagster-cloud

```shell
pip install dagster-cloud
```

## Step 2: Configure the agent

[Generate an agent token](dagster-plus/deployment/tokens) and configure your agent

```shell
dagster-cloud configure
```

## Step 3: Run the agent

```
dagster-cloud agent run
```

## Common configurations

You can pass additional configurations to the agent using a `dagster.yaml` file in  your `$DAGSER_HOME` directory.

### Configuring your agents to serve branch deployments

[Branch deployments](dagster-plus/deployment/branch-deployments) are lightweight staging environments created for each code change. To configure your Dagster+ agent to manage them:

```yaml
#dagster.yaml
instance_class:
  module: dagster_cloud.instance
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  branch_deployments: true
```

```shell
dagster-cloud agent run
```
