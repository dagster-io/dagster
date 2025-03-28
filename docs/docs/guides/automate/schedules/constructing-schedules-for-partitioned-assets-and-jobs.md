---
title: 'Constructing schedules from partitioned assets and jobs'
description: 'Learn to construct schedules for your partitioned jobs.'
sidebar_position: 400
---

In this guide, we'll walk you through how to construct schedules from partitioned [assets](/guides/build/assets/) and jobs. By the end, you'll be able to:

- Construct a schedule for a time-partitioned job
- Customize a partitioned job's starting time
- Customize the most recent partition in a set
- Construct a schedule for a statically-partitioned job

:::note

This article assumes familiarity with:

- Schedules
- [Partitions](/guides/build/partitions-and-backfills/partitioning-assets)
- [Asset definitions](/guides/build/assets/defining-assets)
- [Asset jobs](/guides/build/jobs/asset-jobs) and [op jobs](/guides/build/jobs/op-jobs)

:::

## Working with time-based partitions

For jobs partitioned by time, you can use the <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job"/> to construct a schedule for the job. The schedule's interval will match the spacing of the partitions in the job. For example, if you have a daily partitioned job that fills in a date partition of a table each time it runs, you likely want to run that job every day.

Refer to the following tabs for examples of asset and op-based jobs using <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job"/> to construct schedules:

<Tabs>
<TabItem value="Asset jobs">

**Asset jobs**

Asset jobs are defined using <PyObject section="assets" module="dagster" object="define_asset_job" />. In this example, we created an asset job named `partitioned_job` and then constructed `asset_partitioned_schedule` by using <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job"/>:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedule_from_partitions.py"
  startAfter="start_partitioned_asset_schedule"
  endBefore="end_partitioned_asset_schedule"
/>

</TabItem>
<TabItem value="Op jobs">

**Op jobs**

Op jobs are defined using the <PyObject section="jobs" module="dagster" object="job" decorator />. In this example, we created a partitioned job named `partitioned_op_job` and then constructed `partitioned_op_schedule` using <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job"/>:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedule_from_partitions.py"
  startAfter="start_marker"
  endBefore="end_marker"
/>

</TabItem>
</Tabs>

### Customizing schedule timing

The `minute_of_hour`, `hour_of_day`, `day_of_week`, and `day_of_month` parameters of `build_schedule_from_partitioned_job` can be used to control the timing of the schedule.

Consider the following job:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedule_from_partitions.py"
  startAfter="start_partitioned_schedule_with_offset"
  endBefore="end_partitioned_schedule_with_offset"
/>

On May 20, 2024, the schedule will evaluate at 1:30 AM UTC and then start a run for the partition key of the previous day, `2024-05-19`.

### Customizing the ending partition in a set

:::tip

The examples in this section use daily partitions, but the same logic also applies to other time-based partitions, such as hourly, weekly, and monthly partitions.

:::

Each schedule tick of a partitioned job targets the latest partition in the partition set that exists as of the tick time. For example, consider a schedule that runs a daily-partitioned job. When the schedule runs on `2024-05-20`, it will target the most recent partition, which will correspond to the previous day: `2024-05-19`.

| If a job runs on this date... | It will target this partition |
| ----------------------------- | ----------------------------- |
| 2024-05-20                    | 2024-05-19                    |
| 2024-05-21                    | 2024-05-20                    |
| 2024-05-22                    | 2024-05-21                    |

This occurs because each partition is a **time window**. A time window is a set period of time with a start and an end time. The partition's key is the start of the time window, but the partition isn't included in the partition set until its time window has completed. Kicking off a run after the time window completes allows the run to process data for the entire time window.

Continuing with the daily partition example, the `2024-05-20` partition would have the following start and end times:

- **Start time** - `2024-05-20 00:00:00`
- **End time** - `2024-05-20 23:59:59`

After `2024-05-20 23:59:59` passes, the time window is complete and Dagster will add a new `2024-05-20` partition to the partition set. At this point, the process will repeat with the next time window of `2024-05-21`.

If you need to customize the ending, or most recent partition in a set, use the `end_offset` parameter in the partition's config:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedule_from_partitions.py"
  startAfter="start_offset_partition"
  endBefore="end_offset_partition"
/>

Setting this parameter changes the partition that will be filled in at each schedule tick. Positive and negative integers are accepted, which will have the following effects:

- **Positive numbers**, like `1`, cause the schedule to fill in the partition of the **current** hour/day/week/month
- **Negative numbers**, like `-1,` cause the schedule to fill in the partition of an **earlier** hour/day/week/month

Generally, the calculation for `end_offset` can be expressed as:

```shell
current_date - 1 type_of_partition + end_offset
```

Let's look at an example schedule that's partitioned by day and how different `end_offset` values would affect the most recent partition in the set. In this example, we're using a start date of `2024-05-20`:

| End offset   | Calculated as                 | Ending (most recent) partition          |
| ------------ | ----------------------------- | --------------------------------------- |
| Offset of -1 | `2024-05-20 - 1 day + -1 day` | 2024-05-18 (2 days prior to start date) |
| No offset    | `2024-05-20 - 1 day + 0 days` | 2024-05-19 (1 day prior to start date)  |
| Offset of 1  | `2024-05-20 - 1 day + 1 day`  | 2024-05-20 (start date)                 |

## Working with static partitions

Next, we'll demonstrate how to create a schedule for a job with a static partition. To do this, we'll construct the schedule from scratch using the <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> decorator, rather than using a helper function like <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job"/>. This will allow more flexibility in determining which partitions should be run by the schedule.

In this example, the job is partitioned by continent:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/static_partitioned_asset_job.py"
  startAfter="start_job"
  endBefore="end_job"
/>

Using the <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> decorator, we'll write a schedule that targets each partition, or `continent`:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/static_partitioned_asset_job.py"
  startAfter="start_schedule_all_partitions"
  endBefore="end_schedule_all_partitions"
/>

If we only want to target the `Antarctica` partition, we can create a schedule like the following:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/static_partitioned_asset_job.py"
  startAfter="start_single_partition"
  endBefore="end_single_partition"
/>

## APIs in this guide

| Name                                                                                                   | Description                                                                                              |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />                  | Decorator that defines a schedule that executes according to a given cron schedule.                      |
| <PyObject section="schedules-sensors" module="dagster" object="build_schedule_from_partitioned_job" /> | A function that constructs a schedule whose interval matches the partitioning of a partitioned job.      |
| <PyObject section="schedules-sensors" module="dagster" object="RunRequest" />                          | A class that represents all the information required to launch a single run.                             |
| <PyObject section="assets" module="dagster" object="define_asset_job" />                               | A function for defining a job from a [selection of assets](/guides/build/assets/asset-selection-syntax). |
| <PyObject section="jobs" module="dagster" object="job" decorator />                                    | The decorator used to define a job.                                                                      |
