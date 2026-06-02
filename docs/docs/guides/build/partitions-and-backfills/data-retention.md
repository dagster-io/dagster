---
title: Data retention for partitioned assets
description: Implement a data retention policy that deletes old data and keeps Dagster's partition view in sync with the underlying storage.
sidebar_position: 500
---

Dagster does not automatically clean up partition metadata when the underlying data is deleted, and there is no built-in retention policy that coordinates data deletion with partition management. To enforce a retention window, pair a data-deletion sensor with a partition-synchronization sensor against your dynamic partitions.

This pattern keeps the asset view in the Dagster UI accurate without accumulating partition metadata for data that no longer exists.

## When to use this pattern

Reach for this pattern when you have:

- Accumulating partition data that is past its useful retention window.
- A partition view in Dagster that shows partitions for data that has already been deleted.
- Misalignment between actual data availability and Dagster's partition view.

## Set up dynamic partitions

Define your asset with a <PyObject section="partitions" module="dagster" object="DynamicPartitionsDefinition" />. Dynamic partitions are required because they let you add and remove partition keys at runtime to reflect storage state:

<CodeExample
  path="docs_snippets/docs_snippets/guides/build/partitions_backfills/data_retention.py"
  startAfter="start_partitioned_asset"
  endBefore="end_partitioned_asset"
  title="src/<project_name>/defs/assets.py"
/>

## Add a retention sensor

The retention sensor enforces the maximum age. It walks all current partition keys, deletes the underlying data for any partition older than your retention window, and removes the partition from Dagster:

<CodeExample
  path="docs_snippets/docs_snippets/guides/build/partitions_backfills/data_retention.py"
  startAfter="start_retention_sensor"
  endBefore="end_retention_sensor"
  title="src/<project_name>/defs/sensors.py"
/>

## Add a synchronization sensor

The sync sensor reconciles Dagster's view with whatever partitions actually exist in storage. It adds keys for newly arrived data and removes keys whose underlying data was deleted out of band:

<CodeExample
  path="docs_snippets/docs_snippets/guides/build/partitions_backfills/data_retention.py"
  startAfter="start_sync_sensor"
  endBefore="end_sync_sensor"
  title="src/<project_name>/defs/sensors.py"
/>

:::tip

Adding and removing dynamic partition keys is a metadata-only operation in Dagster+ and does not consume credits. For details on what does count toward credits, see [Insights](/guides/observe/insights).

:::

## Alternative approaches

- Schedule deletion of old files in your storage layer (S3 lifecycle rules, database TTL, etc.) and let the sync sensor reconcile Dagster's view.
- Use the <PyObject section="internals" module="dagster" object="DagsterInstance" /> API to clean up old run and event logs as a separate concern.
- Configure tick retention in your `dagster.yaml` for schedules and sensors. For details, see [Instance configuration: data retention](/deployment/oss/oss-instance-configuration#data-retention).

## Operating the sensors

Monitor your retention sensors so you notice when they stop running:

- Alert if either sensor's last successful tick is older than expected.
- Alert if partition counts grow unexpectedly, which can indicate the retention sensor is failing silently.
- Alert if the sync sensor reports large numbers of orphaned partitions, which can indicate the storage layer changed without Dagster being notified.

## Related documentation

- [Dynamic partitions](/guides/build/partitions-and-backfills/partitioning-assets#dynamic-partitions)
- [Instance configuration: data retention](/deployment/oss/oss-instance-configuration#data-retention)
- [Dagster+ Insights](/guides/observe/insights)
