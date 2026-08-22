---
title: Deployment fails with bad git executable error in branch deployment code locations
sidebar_position: 1100
description: Resolve "Bad git executable" DagsterImportError that affects older dagster-dbt versions in branch deployment code locations.
---

## Problem description

Users on older `dagster-dbt` versions experience deployment failures when deploying branch-deployment code locations due to a missing or improperly configured git executable.

## Symptoms

- `DagsterImportError` with message `"Failed to initialize: Bad git executable"`
- Error occurs during code location deployment, specifically when importing `dagster-dbt` modules.
- Stack trace shows failure in `git/__init__.py` when trying to refresh git executable.
- Deployment worked previously but suddenly started failing without configuration changes.

## Root cause

Older `dagster-dbt` versions imported GitPython at module load time. GitPython probes for a git executable during import and raises if git is missing or not on `PATH`.

Current `dagster-dbt` no longer depends on GitPython. It invokes the git CLI only when cloning a remote dbt project (for example, a `DbtProjectComponent` configured with `repo_url`). Importing `dagster-dbt` no longer requires git.

## Solution

Upgrade `dagster-dbt` to a version that no longer depends on GitPython. Importing the library will no longer fail when git is absent.

If you load a remote dbt project from git, the git CLI must still be installed and on `PATH` in that environment. The clone is given 30 minutes by default; set `DAGSTER_DBT_GIT_CLONE_TIMEOUT_SECONDS` if a large repository or a slow link needs longer.

### Workaround for older versions

If you cannot upgrade yet, set the `GIT_PYTHON_REFRESH` environment variable to suppress GitPython's import-time check:

```bash
export GIT_PYTHON_REFRESH=quiet
```

## Prevention

Keep `dagster-dbt` current. When using a remote git dbt project, install git in the deployment image and confirm it is on `PATH`.

## Related documentation

- [GitHub PR that deferred the GitPython import](https://github.com/dagster-io/dagster/pull/32756)
