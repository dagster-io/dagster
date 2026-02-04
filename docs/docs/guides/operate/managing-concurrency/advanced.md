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

## Limit concurrent runs across all branch deployments (Dagster+ only) {#branch-deployment-concurrency}

In Dagster+, you can limit the total number of concurrent runs across all [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) using the organization-scoped `max_concurrent_branch_deployment_runs` setting. By default, this value is 50.

This setting is useful for preventing branch deployments from consuming too many resources, especially when multiple developers are working simultaneously.

To view or modify this setting, use the `dagster-cloud` CLI (requires a user token with the Organization Admin role):

```bash
# View current settings
dagster-cloud organization settings get

# Save settings to a file, edit, then sync
dagster-cloud organization settings get > org-settings.yaml
# Edit org-settings.yaml to change max_concurrent_branch_deployment_runs
dagster-cloud organization settings set-from-file org-settings.yaml
```

For more details, see [Managing branch deployments across multiple deployments](/deployment/dagster-plus/deploying-code/branch-deployments/multiple-deployments#setting-the-concurrency-limit-for-runs-across-all-branch-deployments).
