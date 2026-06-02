---
title: Define environment-aware assets
description: Write assets that behave differently in dev, staging, and prod
sidebar_position: 10
---

A key challenge in multi-environment deployments is writing code that adapts to its environment without requiring separate codebases. Dagster+ injects a `DAGSTER_CLOUD_DEPLOYMENT_NAME` environment variable into every run, which you can use to drive environment-specific behavior.

## Step 1: Read the deployment name

Create a helper function that reads the deployment name and falls back to `"local"` when running outside of Dagster+:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/src/project_dagster_plus_deployment/defs/assets.py"
  language="python"
  startAfter="start_get_deployment_name"
  endBefore="end_get_deployment_name"
  title="src/project_dagster_plus_deployment/defs/assets.py"
/>

The fallback to `"local"` means your assets behave like dev assets when you run `dg dev` on your laptop — no special configuration needed.

## Step 2: Define assets with environment-aware behavior

Organize assets into three groups that represent the layers of a typical data pipeline: `raw_data`, `staging`, and `analytics`. Each asset uses the deployment name to adjust its behavior — for example, processing more rows in prod than in dev.

The `raw_data` group ingests from source systems:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/src/project_dagster_plus_deployment/defs/assets.py"
  language="python"
  startAfter="start_raw_assets"
  endBefore="end_raw_assets"
  title="src/project_dagster_plus_deployment/defs/assets.py"
/>

The `staging` group cleans and validates the raw data:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/src/project_dagster_plus_deployment/defs/assets.py"
  language="python"
  startAfter="start_staging_assets"
  endBefore="end_staging_assets"
  title="src/project_dagster_plus_deployment/defs/assets.py"
/>

The `analytics` group computes downstream metrics:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/src/project_dagster_plus_deployment/defs/assets.py"
  language="python"
  startAfter="start_analytics_assets"
  endBefore="end_analytics_assets"
  title="src/project_dagster_plus_deployment/defs/assets.py"
/>

The asset metadata records which deployment materialized the asset, making it easy to trace runs back to their environment in the Dagster+ UI.

## Step 3: Define a schedule

Add a schedule in a separate file that runs the full analytics pipeline every morning:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/src/project_dagster_plus_deployment/defs/schedules.py"
  language="python"
  startAfter="start_schedule"
  endBefore="end_schedule"
  title="src/project_dagster_plus_deployment/defs/schedules.py"
/>

Setting `default_status=STOPPED` means the schedule won't automatically activate in branch deployments or when the code location first loads — you enable it explicitly per environment.

## Step 4: Configure the code location

The `dagster_cloud.yaml` file tells Dagster+ how to find your code and which container registry to pull images from:

<CodeExample
  path="docs_projects/project_dagster_plus_deployment/dagster_cloud.yaml"
  language="yaml"
  title="dagster_cloud.yaml"
/>

The `${DAGSTER_CONTAINER_REGISTRY}` placeholder is substituted at deploy time by the CI/CD pipeline using the `CONTAINER_REGISTRY` GitHub variable.

## Step 5: Verify the definitions load

Use `dg check` to confirm all assets and schedules are valid before moving on:

```shell
dg check defs
```

## Next steps

Continue this example with [containerizing the project](/examples/full-pipelines/dagster-plus-deployment/containerize).
