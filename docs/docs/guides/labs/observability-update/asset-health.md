---
title: Asset health
description: With asset health criteria, you can quickly identify which datasets are performing well and which need attention.
sidebar_position: 300
---

You can quickly identify which assets are performing well and which need attention with health indicators that highlight data quality and platform reliability in real time. These indicators appear on the home page, throughout the asset catalog, and in the asset lineage view.

## Asset health indicators

| Icon | Health status | Latest materialization (unpartitioned) | Latest materialization (partitioned) | Freshness | Asset checks |
|---------|------|----------------------------------------|--------------------------------------|-----------|--------------|
| ![Unknown trend icon](/images/guides/labs/observability-update/status.svg) | Unknown       | Never materialized                     | All partitions are missing           | No freshness policy defined | No asset checks defined or executed |
| ![Healthy trend icon](/images/guides/labs/observability-update/successful_trend.svg) | Healthy |  Most recent materialization succeeded       | One or more partitions have executed successfully, and none are failing | Freshness policy is passing | All asset checks that have executed are passing |
| ![Warning trend icon](/images/guides/labs/observability-update/warning_trend.svg) | Warning | Not applicable | Not applicable | Freshness policy is failing with a warning | Some asset checks are failing with a warning |
| ![Degraded trend icon](/images/guides/labs/observability-update/failure_trend.svg) | Degraded |  Most recent materialization failed | More than one  partition is failing | Freshness policy is failing | Some asset checks are failing, or had an error on most recent execution |

:::note

The overall health status becomes the most elevated status from among each of the health components.

:::