---
description: Understand which Dagster+ operations consume credits, including how observable source assets and dynamic partitions are billed.
sidebar_position: 2000
title: Credit usage
tags: [dagster-plus-feature]
---

This page explains how Dagster+ counts credits for common operations, including the difference between metadata updates and materializations.

## What consumes credits

| Operation                                                                  | Credit cost               |
| -------------------------------------------------------------------------- | ------------------------- |
| An asset materialization (per partition)                                   | 1 credit                  |
| An observable source asset execution                                       | 1 credit                  |
| Adding a dynamic partition via `context.instance.add_dynamic_partitions()` | 0 credits (metadata only) |
| Asset observations                                                         | 0 credits                 |

## Dynamic partitions and observable source assets

Adding new partitions through `context.instance.add_dynamic_partitions()` is a metadata update. It does not consume credits regardless of how many partitions are added. The materializations of downstream assets that fill in those new partitions are what generate credit usage.

For example, suppose you use an observable source asset to detect new files (e.g., from Snowpipe) and add them as dynamic partitions. If the observable source asset discovers 500 new files:

- The discovery run costs **1 credit** (the observable source asset execution itself).
- Adding the 500 partitions costs **0 credits**.
- Materializing a downstream asset across all 500 new partitions costs **500 credits** (1 per partition).
- Each additional downstream asset that processes those partitions incurs its own per-partition credit cost.

## Reporting events from external systems

If you only need to record metadata about work that happened outside Dagster, [report it as an asset observation rather than a materialization](/deployment/dagster-plus/management/report-external-system-events). Observations don't count against credit usage.

## Related documentation

- [Reporting external system events without consuming credits](/deployment/dagster-plus/management/report-external-system-events)
- [Asset observations](/guides/build/assets/metadata-and-tags/asset-observations)
- [Dynamic partitions](/guides/build/partitions-and-backfills/partitioning-assets#dynamic-partitions)
