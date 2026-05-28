---
description: Use asset observations instead of materializations to report events from external systems without consuming Dagster+ credits.
sidebar_position: 2100
title: Reporting external system events without consuming credits
tags: [dagster-plus-feature]
---

When you set up sensors or assets that report events from external systems (for example, recording that an upstream pipeline finished, or that a third-party warehouse loaded a table), you can choose how Dagster+ counts that work.

| Method                                                                         | Credit cost        | When to use                                                                                                   |
| ------------------------------------------------------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------- |
| Asset materialization with step execution                                      | 1 credit per event | The event represents work performed by Dagster, or you want it to count toward materialization-based metrics. |
| Asset materialization reported from a sensor (no step execution)               | 0 credits          | You want to record that an asset was materialized externally and surface it in the asset graph.               |
| [Asset observation](/guides/build/assets/metadata-and-tags/asset-observations) | 0 credits          | The event represents work performed outside Dagster, and you only need the metadata visible in the UI.        |

Sensor evaluations themselves never consume credits. Both materialization reports and observations from sensors surface metadata in the Dagster+ UI, so for pure external-event reporting you can track asset state without driving up credit usage.

## When to prefer observations

Use observations whenever:

- A sensor watches an external system (e.g., Snowflake table updates, S3 object arrivals, third-party job completions) and only needs to record that something happened. Note that sensor evaluations themselves never consume credits.
- You want to attach metadata (timestamps, row counts, file URIs) to an asset without claiming Dagster materialized it.
- High-frequency external events would otherwise generate unexpected credit consumption.

For details on implementing them, see the [Asset observations guide](/guides/build/assets/metadata-and-tags/asset-observations).

## Related documentation

- [Credit usage](/deployment/dagster-plus/management/credit-usage)
- [Asset observations](/guides/build/assets/metadata-and-tags/asset-observations)
