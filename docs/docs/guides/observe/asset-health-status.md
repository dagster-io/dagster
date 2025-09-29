---
title: Asset health status (Dagster+)
description: With asset health criteria, you can quickly identify which datasets are performing well and which need attention in Dagster+.
sidebar_position: 300
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

All assets now have a single health status that combines the status of the most recent materialization, freshness, and asset checks. These statuses appear on the home page, throughout the asset catalog, and in the asset lineage view, and can be used to group and filter your assets.

## Asset health statuses

The overall health status for an asset becomes the most elevated status from among each of the health components.

| Icon                                                               | Health status | Latest materialization (unpartitioned) | Latest materialization (partitioned)                                    | Freshness                                  | Asset checks                                                            |
| ------------------------------------------------------------------ | ------------- | -------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| ![Unknown trend icon](/images/guides/observe/status.svg)           | Unknown       | Never materialized                     | All partitions are missing                                              | No freshness policy defined                | No asset checks defined or executed                                     |
| ![Healthy trend icon](/images/guides/observe/successful_trend.svg) | Healthy       | Most recent materialization succeeded  | One or more partitions have executed successfully, and none are failing | Freshness policy is passing                | All asset checks that have executed are passing                         |
| ![Warning trend icon](/images/guides/observe/warning_trend.svg)    | Warning       | Not applicable                         | Not applicable                                                          | Freshness policy is failing with a warning | Some asset checks are failing with a warning                            |
| ![Degraded trend icon](/images/guides/observe/failure_trend.svg)   | Degraded      | Most recent materialization failed     | More than one partition is failing                                      | Freshness policy is failing                | Some asset checks are failing, or had an error on most recent execution |

:::note Known limitations

- Health statuses currently only account for materializations. (They will take asset observations into account soon.)
- Asset failures prior to the date the updated observability features were enabled for your organization will not be represented in the event log, but asset health status will still be computed correctly.

:::

## Alerting on health status change

You set a [health status change alert](/guides/observe/alerts/creating-alerts) to notify you when the health status of an asset changes.

## Grouping and filtering asset selections by health status

To display assets grouped by health status, click the **Group By** dropdown and select **Health Status** on any saved selection:

![Group by health status dropdown](/images/guides/observe/group-by-health-status.png)

To only show assets with a particular health status, you can add a filter to the saved selection. For example, to filter for degraded assets in a saved selection called Analytics Team that shows assets owned by the `ANALYTICS` group, you would add `and status:DEGRADED` to the selection:

![Analytics team saved selection with asset health status filter](/images/guides/observe/filter-degraded-status-assets.png)

For a full list of asset health statuses that you can filter on, see the [asset selection syntax reference](/guides/build/assets/asset-selection-syntax/reference#filters).

## Marking an asset as healthy

To manually mark an asset healthy, you can either:

- Report a materialization event in the UI
- Wipe materialization events to remove past failures
