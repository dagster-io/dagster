---
title: Asset health reporting
description: With asset health criteria, you can quickly identify which datasets are performing well and which need attention.
tags: [dagster-plus]
sidebar_position: 200
---

All assets now have a single health status that combines the status of the most recent materialization, freshness, and asset checks. These statuses appear on the home page, throughout the asset catalog, and in the asset lineage view, and can be used to group and filter your assets. You can also [set alerts](/guides/labs/observability-update/alerts) to send notifications when the health status of the asset changes.

## Asset health statuses

The overall health status for an asset becomes the most elevated status from among each of the health components.

| Icon                                                                                 | Health status | Latest materialization (unpartitioned) | Latest materialization (partitioned)                                    | Freshness                                  | Asset checks                                                            |
| ------------------------------------------------------------------------------------ | ------------- | -------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| ![Unknown trend icon](/images/guides/labs/observability-update/status.svg)           | Unknown       | Never materialized                     | All partitions are missing                                              | No freshness policy defined                | No asset checks defined or executed                                     |
| ![Healthy trend icon](/images/guides/labs/observability-update/successful_trend.svg) | Healthy       | Most recent materialization succeeded  | One or more partitions have executed successfully, and none are failing | Freshness policy is passing                | All asset checks that have executed are passing                         |
| ![Warning trend icon](/images/guides/labs/observability-update/warning_trend.svg)    | Warning       | Not applicable                         | Not applicable                                                          | Freshness policy is failing with a warning | Some asset checks are failing with a warning                            |
| ![Degraded trend icon](/images/guides/labs/observability-update/failure_trend.svg)   | Degraded      | Most recent materialization failed     | More than one partition is failing                                      | Freshness policy is failing                | Some asset checks are failing, or had an error on most recent execution |

:::note Coming soon

- Health statuses will take asset observations into account (currently they only account for materializations).
- Alerts will be added for health status changes.

:::
