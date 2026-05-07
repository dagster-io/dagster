---
title: dbt project path validation errors thrown by pydantic in the Launchpad
sidebar_position: 90
description: How to resolve pydantic validation errors for DbtCliResource project_dir paths when launching jobs from the Launchpad.
---

## Problem description

When launching jobs through the Launchpad interface with custom resource configurations, users may encounter validation errors related to the dbt project directory path. This occurs particularly when trying to materialize jobs with overridden warehouse settings.

Example error message:

```text
pydantic_core._pydantic_core.ValidationError: 1 validation error for DbtCliResource
project_dir
  Value error, The absolute path of '...') does not exist [type=value_error, input_value='...', input_type=str]
```

## Symptoms

- Job runs fail with a pydantic validation error for `DbtCliResource`.
- Error message indicates that the absolute path of the dbt project directory does not exist.
- The issue may be intermittent, with some retries succeeding.

## Root cause

The error occurs because the absolute path of the dbt project changes when code is redeployed, causing the stored Launchpad configuration to become stale and reference an outdated path.

## Solution

Remove the resources configuration from the Launchpad before launching the job to use the default values.

### Step-by-step resolution

1. Open the Launchpad interface.
2. Delete the entire `resources` section from the configuration.
3. Launch the job with the cleaned configuration.

### Alternative solutions

If you need to maintain other resource configurations, you can alternatively delete only the `dbt` key from within the `resources` block while keeping other resource settings.

## Prevention

When using the Launchpad for job launches with custom configurations, avoid storing dbt project path configurations and rely on the default values defined in your code.

## Related documentation

- [Using dbt with Dagster](/integrations/libraries/dbt/using-dbt-with-dagster-plus)
