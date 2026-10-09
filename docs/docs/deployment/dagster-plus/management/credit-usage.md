---
description: Understand which Dagster+ operations consume credits, including how steps, materializations, observable source assets, and dynamic partitions are billed.
sidebar_position: 2000
title: Credit usage
tags: [dagster-plus-feature]
---

This page explains how Dagster+ counts credits for common operations, including the difference between metadata updates and materializations.

## How credits are counted

Credit usage is the sum of two independent counts:

- **1 credit per step execution.** Any step Dagster runs costs a credit, whether or not it materializes an asset, and whether it succeeds or fails.
- **1 credit per asset materialization event.** Each materialization emitted by a step costs a credit on top of the step credit. Each partition emits a separate materialization event.

## What consumes credits

| Operation                                                  | Credit cost                            |
| ---------------------------------------------------------- | -------------------------------------- |
| A step that materializes one asset (or partition)          | 2 credits (1 step + 1 materialization) |
| Each additional asset materialized in the same step        | 1 credit                               |
| A step that materializes nothing (for example, a plain op) | 1 credit                               |
| An observable source asset execution                       | 1 credit                               |
| A step that failed without any successful materializations | 1 credit                               |

The following operations do not consume credits:

- Asset checks
- Asset observations
- Sensor evaluations
- Reporting an asset materialization from a sensor (with no step execution)

### Materializations with and without step execution

The materialization credit is charged only when a step produced the materialization — that is, when Dagster actually launched compute to produce the asset. If a sensor reports that an asset was materialized by an external system (using `context.log_for_asset(...)` or by yielding `AssetMaterialization` events), no step is executed and no credit is consumed, for either the step or the materialization. This means you can use sensors to track the state of externally-produced assets in the Dagster UI without incurring credit usage.

## Credit attribution in Insights

When a step materializes several assets, Insights splits the step's single credit across those asset keys, so a per-asset breakdown can show fractional credits. The total is unchanged.

## Retries and failures

A step that fails still costs its step credit. Assets that failed to materialize do not. A step that fails partway through costs 1 credit for the step plus 1 for each asset it did materialize before failing.

Retries within a run, such as those from an op retry policy, do not add credits: the attempts collapse into a single step execution charged once. Re-executing a run is different — that creates new step executions, and each one costs a credit the same way the original did.

## Dynamic partitions and observable source assets

Adding new partitions through `context.instance.add_dynamic_partitions()` is a metadata update. It does not consume credits regardless of how many partitions are added. The materializations of downstream assets that fill in those new partitions are what generate credit usage.

For example, suppose you use an observable source asset to detect new files (e.g., from Snowpipe) and add them as dynamic partitions. If the observable source asset discovers 500 new files:

- The discovery run costs **1 credit** (the observable source asset step, which materializes nothing).
- Adding the 500 partitions costs **0 credits**.
- Materializing a downstream asset across all 500 new partitions costs **1000 credits** (2 per partition: one step and one materialization).
- Each additional downstream asset that processes those partitions incurs its own per-partition credit cost.

## Reporting events from external systems

If you only need to record metadata about work that happened outside Dagster, [report it as an asset observation rather than a materialization](/deployment/dagster-plus/management/report-external-system-events). Observations don't count against credit usage.

## Related documentation

- [Reporting external system events without consuming credits](/deployment/dagster-plus/management/report-external-system-events)
- [Asset observations](/guides/build/assets/metadata-and-tags/asset-observations)
- [Asset checks](/guides/test/asset-checks)
- [Sensors](/guides/automate/sensors)
- [Dynamic partitions](/guides/build/partitions-and-backfills/partitioning-assets#dynamic-partitions)
