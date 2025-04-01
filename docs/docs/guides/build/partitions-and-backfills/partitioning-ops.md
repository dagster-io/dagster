---
title: Partitioning ops | Dagster
description: Partitioned ops enable launching backfills, where each partition processes a subset of data.
---

# Partitioning ops

:::note

This page is specific to ops. To learn about partitioning assets, see "[Partitioning assets](/guides/build/partitions-and-backfills/partitioning-assets)".

:::

When defining a job that uses [ops](/guides/build/ops/) you can partition it by supplying <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> object as its config.

In this guide, we'll demonstrate to use partitions with ops and [jobs](/guides/build/jobs/).

## Prerequisites

Before continuing, you should be familiar with:

- [Ops](/guides/build/ops/)
- [Jobs](/guides/build/jobs/)
- [Run configuration](/guides/operate/configuration/run-configuration)

## Relevant APIs

| Name                                                       | Description                                                                                         |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| <PyObject section="partitions" module="dagster" object="PartitionedConfig" />                    | Determines a set of partitions and how to generate run config for a partition.                      |
| <PyObject section="partitions" module="dagster" object="daily_partitioned_config" decorator />   | Decorator for constructing partitioned config where each partition is a date.                       |
| <PyObject section="partitions" module="dagster" object="hourly_partitioned_config" decorator />  | Decorator for constructing partitioned config where each partition is an hour of a date.            |
| <PyObject section="partitions" module="dagster" object="weekly_partitioned_config" decorator />  | Decorator for constructing partitioned config where each partition is a week.                       |
| <PyObject section="partitions" module="dagster" object="monthly_partitioned_config" decorator /> | Decorator for constructing partitioned config where each partition is a month.                      |
| <PyObject section="partitions" module="dagster" object="static_partitioned_config" decorator />  | Decorator for constructing partitioned config for a static set of partition keys.                   |
| <PyObject section="partitions" module="dagster" object="dynamic_partitioned_config" decorator /> | Decorator for constructing partitioned config for a set of partition keys that can grow over time.  |
| `build_schedule_from_partitioned_job`  | A function that constructs a schedule whose interval matches the partitioning of a partitioned job. |

## Defining jobs with time partitions

The most common kind of partitioned job is a time-partitioned job - each partition is a time window, and each run for a partition processes data within that time window.

- [Non-partitioned job with date config](#non-partitioned-job-with-date-config)
- [Date-partitioned job](#date-partitioned-job)

### Non-partitioned job with date config

Before we dive in, let's look at a non-partitioned job that computes some data for a given date:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/date_config_job.py" />

It takes, as config, a string `date`. This piece of config defines which date to compute data for. For example, if you wanted to compute for `May 5th, 2020`, you would execute the graph with the following config:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/config.yaml" />

### Date-partitioned job

With the job above, it's possible to supply any value for the `date` param. This means if you wanted to launch a backfill, Dagster wouldn't know what values to run it on. You can instead build a partitioned job that operates on a defined set of dates.

First, define the <PyObject section="partitions" module="dagster" object="PartitionedConfig"/>. In this case, because each partition is a date, you can use the <PyObject section="partitions" module="dagster" object="daily_partitioned_config" decorator /> decorator. This decorator defines the full set of partitions - every date between the start date and the current date, as well as how to determine the run config for a given partition.

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_job.py" startAfter="start_partitioned_config" endBefore="end_partitioned_config" />

Then you can build a job that uses the `PartitionedConfig` by supplying it to the `config` argument when you construct the job:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partitioned_job.py" startAfter="start_partitioned_job" endBefore="end_partitioned_job" />

## Defining jobs with static partitions

Not all jobs are partitioned by time. For example, the following example shows a partitioned job where the partitions are continents:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/static_partitioned_job.py" />

## Creating schedules from partitioned jobs

Running a partitioned job on a schedule is a common use case. For example, if your job has a partition for each date, you likely want to run that job every day, on the partition for that day.

Refer to the [Schedule documentation](/guides/automate/schedules/) for more info about constructing both schedules for asset and op-based jobs.

## Partitions in the Dagster UI

In the UI, you can view runs by partition in the **Partitions tab** of a **Job** page:

![Partitions tab](/images/guides/build/partitions-and-backfills/partitioned-job.png)

In the **Run Matrix**, each column corresponds to one of the partitions in the job. The time listed corresponds to the start time of the partition. Each row corresponds to one of the steps in the job. You can click on an individual box to navigate to logs and run information for the step.

You can view and use partitions in the UI Launchpad tab for a job. In the top bar, you can select from the list of all available partitions. Within the config editor, the config for the selected partition will be populated.

In the screenshot below, we select the `2020-01-02` partition, and we can see that the run config for the partition has been populated in the editor.

![Partitions in the Dagster UI Launchpad](/images/guides/build//partitions-and-backfills/launchpad.png)

In addition to the <PyObject section="partitions" module="dagster" object="daily_partitioned_config" decorator /> decorator, Dagster also provides <PyObject section="partitions" module="dagster" object="monthly_partitioned_config" decorator />, <PyObject section="partitions" module="dagster" object="weekly_partitioned_config" decorator />, <PyObject section="partitions" module="dagster" object="hourly_partitioned_config" decorator />. See the API docs for each of these decorators for more information on how partitions are built based on different `start_date`, `minute_offset`, `hour_offset`, and `day_offset` inputs.
