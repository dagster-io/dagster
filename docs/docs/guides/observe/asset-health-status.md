---
title: Asset health status (Dagster+)
description: With asset health criteria, you can quickly identify which datasets are performing well and which need attention in Dagster+.
sidebar_position: 300
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

All assets now have a single health status that combines the status of the most recent materialization, freshness, and asset checks. These statuses appear on the home page, throughout the asset catalog, and in the asset lineage view, and can be used to group and filter your assets.

:::info Health status change alerts

You set a [health status change alert](/guides/observe/alerts/creating-alerts) to notify you when the health status of an asset changes.

:::

## Asset health statuses

The overall health status for an asset becomes the most elevated status from among each of the health components.

| Icon                                                               | Health status | Latest materialization (unpartitioned) | Latest materialization (partitioned)                                    | Freshness                                  | Asset checks                                                            |
| ------------------------------------------------------------------ | ------------- | -------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| ![Unknown trend icon](/images/guides/observe/status.svg)           | Unknown       | Never materialized                     | All partitions are missing                                              | No freshness policy defined                | No asset checks defined or executed                                     |
| ![Healthy trend icon](/images/guides/observe/successful_trend.svg) | Healthy       | Most recent materialization succeeded  | One or more partitions have executed successfully, and none are failing | Freshness policy is passing                | All asset checks that have executed are passing                         |
| ![Warning trend icon](/images/guides/observe/warning_trend.svg)    | Warning       | Not applicable                         | Not applicable                                                          | Freshness policy is failing with a warning | Some asset checks are failing with a warning                            |
| ![Degraded trend icon](/images/guides/observe/failure_trend.svg)   | Degraded      | Most recent materialization failed     | More than one partition is failing                                      | Freshness policy is failing                | Some asset checks are failing, or had an error on most recent execution |

:::note Coming soon

Health statuses will take asset observations into account (currently they only account for materializations).

:::

## Filtering and grouping by health status

For example, can filter any view for `health_status: DEGRADED`

## Marking an asset as healthy

To mark an asset healthy, you can either

- Report a materialization event in the UI to manually change its status to healthy
- Wipe materialization events to remove past failures

:::info Limitations

Failures from more than TK days ago will not impact asset health.

:::
