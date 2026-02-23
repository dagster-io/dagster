---
title: Asset health monitoring
description: How to monitor critical assets with scheduled health checks.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore different approaches to monitoring critical (Tier-0) assets in Dagster. When you have assets that power downstream business processes, you need to ensure they are successfully materialized, passing data quality checks, and fresh according to defined policies.

## Problem: Monitoring critical data assets

Imagine you have a set of critical data assets that require monitoring. Without a monitoring strategy, you'd have to check each asset individually in the UI, manually verify freshness across multiple assets, and piece together health status from scattered logs.

To monitor critical data assets, you can use freshness policies, asset checks, or health monitoring.

| Strategy                                                                     | Use when                                                                                                                                                                                                                                          |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Freshness policies](#strategy-1-freshness-policies-for-staleness-detection) | <ul><li>You need automatic staleness detection</li><li>Assets have time-based freshness requirements</li><li>You want built-in UI indicators for data currency</li></ul>                                                                          |
| [Asset checks](#strategy-2-asset-checks-for-data-quality)                    | <ul><li>You need to validate data quality after materialization</li><li>Business rules must be enforced on asset outputs</li><li>You want pass/fail validation with severity levels</li></ul>                                                     |
| [Health monitoring asset](#strategy-3-aggregated-health-monitoring-asset)    | <ul><li>You need aggregated health status across multiple assets</li><li>Scheduled health reports are required at specific times (for example, at the start or end of the day)</li><li>You want historical tracking of health over time</li></ul> |

:::info Alerting
To get notified when assets become stale or fail checks, use [alert policies](/guides/observe/alerts) (Dagster+) or [sensors](/guides/automate/sensors) to react to run or asset status.
:::

## Strategy 1: Freshness policies for staleness detection

[Freshness policies](/guides/observe/asset-freshness-policies) define acceptable staleness thresholds for your assets. Dagster automatically tracks whether assets are fresh and displays status in the UI.

**Benefits**:

- Dagster automatically monitors time since asset materialization.
- Assets have built-in freshness status badges in the UI.

**Drawbacks:**

- No built-in history of freshness status.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/asset_health_monitoring/tier0_assets.py"
  language="python"
  title="Asset with freshness policy and asset check"
  startAfter="start_critical_asset_with_freshness"
  endBefore="end_critical_asset_with_freshness"
/>

## Strategy 2: Asset checks for data quality

Asset checks provide the following:

- **Validation scope**: Per-asset data quality rules
- **Severity levels**: ERROR (blocking) or WARN (non-blocking)
- **Execution**: Runs after materialization or on-demand
- **Aggregated view**: Check results visible per-asset, not aggregated

[Asset checks](/guides/test/asset-checks) validate data quality after materialization, providing pass/fail results with configurable severity levels. You can define multiple assets with different freshness requirements and paired checks.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/asset_health_monitoring/tier0_assets.py"
  language="python"
  title="Multiple assets with checks"
  startAfter="start_multiple_tier0_assets"
  endBefore="end_multiple_tier0_assets"
/>

## Strategy 3: Aggregated health monitoring asset

For centralized monitoring with scheduled execution, create a dedicated asset that queries the Dagster instance and aggregates health across all critical assets. This approach combines the benefits of freshness policies and asset checks into a single, scheduled health report.

### Step 1: Define a health check function

First, define a function that examines three dimensions of health for each asset:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/asset_health_monitoring/health_check.py"
  language="python"
  title="Health check function"
  startAfter="start_health_check_function"
  endBefore="end_health_check_function"
/>

| Check                      | How it works                                                                                               | Status impact                                  |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Materialization status** | Calls `instance.get_latest_materialization_event()` to verify the asset has been successfully materialized | `WARNING` if never materialized                |
| **Asset check evaluation** | Queries the event log for `ASSET_CHECK_EVALUATION` events and aggregates pass/fail status                  | `UNHEALTHY` for errors, `WARNING` for warnings |
| **Freshness calculation**  | Compares the lag since last materialization against the `fail_window` and `warn_window` thresholds         | `UNHEALTHY` if stale, `WARNING` if approaching |

### Step 2: Create a health monitoring asset

Create an asset that uses the health check function from [step 1](#step-1-define-a-health-check-function) to aggregate health across all Tier-0 assets. The health monitoring asset iterates through the `TIER0_ASSETS` list, calls `get_asset_health()` for each, and produces a structured output with `overall_status` that downstream processes can consume.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/asset_health_monitoring/health_check.py"
  language="python"
  title="Health monitoring asset"
  startAfter="start_health_monitoring_asset"
  endBefore="end_health_monitoring_asset"
/>

### Step 3: Schedule health checks

Finally, schedule asset health monitoring for predictable check times:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/asset_health_monitoring/health_check.py"
  language="python"
  title="Health check schedules"
  startAfter="start_schedules"
  endBefore="end_schedules"
/>

:::tip Optional: Add alerting
You can trigger alerts when the health monitoring asset's `overall_status` indicates an issue by using [alert policies](/guides/observe/alerts) (Dagster+) or [sensors](/guides/automate/sensors) that react to the asset's materialization result.
:::
