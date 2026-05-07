---
title: Deployment fails with bad git executable error in branch deployment code locations
sidebar_position: 110
description: Resolve "Bad git executable" DagsterImportError that affects dagster-dbt in branch deployment code locations.
---

## Problem description

Users experience deployment failures with the `dagster-dbt` integration when deploying branch-deployment code locations due to a missing or improperly configured git executable.

## Symptoms

- `DagsterImportError` with message `"Failed to initialize: Bad git executable"`
- Error occurs during code location deployment, specifically when importing `dagster-dbt` modules.
- Stack trace shows failure in `git/__init__.py` when trying to refresh git executable.
- Deployment worked previously but suddenly started failing without configuration changes.

## Root cause

This is a known issue in Dagster where the git executable is not properly available in the deployment environment. The `dagster-dbt` integration requires git to be accessible, but the deployment environment may not have git installed or properly configured in the `PATH`.

## Solution

Pin your Dagster version to avoid the problematic version until the fix is released.

### Step-by-step resolution

1. Identify your current Dagster version and pin to a stable version in your `requirements.txt` or `pyproject.toml`:

   ```text
   dagster==1.8.x  # Replace x with the last working version
   ```

2. Redeploy your code location with the pinned version.
3. Verify the deployment completes successfully without git executable errors.

### Alternative solutions

If pinning the version doesn't work, you can try setting the `GIT_PYTHON_REFRESH` environment variable to suppress the error:

```bash
export GIT_PYTHON_REFRESH=quiet
```

## Prevention

Monitor Dagster release notes for updates on this issue and upgrade to newer versions once the fix is available. Consider testing deployments in a staging environment before promoting to production.

## Related documentation

- [GitHub PR with fix](https://github.com/dagster-io/dagster/pull/32756)
