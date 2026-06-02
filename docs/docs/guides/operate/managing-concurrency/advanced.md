---
title: Advanced concurrency configuration
description: Advanced concurrency configuration including using job metadata and schedules to prevent concurrent runs and limiting concurrent runs across branch deployments.
sidebar_position: 500
---

## Use job metadata and schedules to prevent runs from starting if another run is already occurring (advanced)

You can use Dagster's rich metadata to use a schedule or a sensor to only start a run when there are no currently running jobs.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/concurrency_no_more_than_1_job.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

## Limit concurrent runs in branch deployments (Dagster+ only) \{#branch-deployment-concurrency}

In Dagster+, [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) share a set of organization-scoped concurrency settings that apply to every branch deployment in the organization:

- `max_concurrent_branch_deployment_runs`: caps the total number of concurrent runs across **all** branch deployments (default `50`).
- `max_concurrent_runs_per_branch_deployment`: caps the number of concurrent runs within an **individual** branch deployment (default no limit).
- `branch_deployment_tag_concurrency_limits`: caps the number of concurrent runs with matching run tags across **all** branch deployments.

These settings are useful for preventing branch deployments from consuming too many resources, especially when multiple developers are working simultaneously.

For details on each setting and how to edit them in the Dagster+ UI or with the `dg` CLI, see [Configuring concurrency for branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/branch-deployment-concurrency).
