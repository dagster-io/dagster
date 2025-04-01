---
title: 'Testing partitioned config and jobs'
description: Test your partition configuration and jobs.
sidebar_position: 500
---

In this article, we'll cover a few ways to test your partitioned config and jobs.

:::note

This article assumes familiarity with [partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets).

:::

## Testing partitioned config

Invoking a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> object directly invokes the decorated function.

If you want to check whether the generated run config is valid for the config of a job, you can use the <PyObject section="execution" module="dagster" object="validate_run_config" /> function.

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_config_test.py"
  startAfter="start_partition_config"
  endBefore="end_partition_config"
/>

If you want to test that a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> creates the partitions you expect, use the `get_partition_keys` or `get_run_config_for_partition_key` functions:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_config_test.py"
  startAfter="start_partition_keys"
  endBefore="end_partition_keys"
/>

## Testing partitioned jobs

{/* TODO fix the API docs so this can be a PyObject */}

To run a partitioned job in-process on a particular partition, supply a value for the `partition_key` argument of [`dagster.JobDefinition.execute_in_process`](/api/python-api/execution):

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_job_test.py"
  startAfter="start"
  endBefore="end"
/>
