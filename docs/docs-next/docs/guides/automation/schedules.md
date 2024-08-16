---
title: "Scheduling pipelines"
sidebar_label: "Running pipelines on a schedule"
sidebar_position: 10
---

## Basic Schedule Example

A basic schedule is defined by a `JobDefinition` and a `cron_schedule` using the `ScheduleDefinition` class.

<CodeExample filePath="guides/automation/simple-schedule-example.py" language="python" title="Simple Schedule Example" />

## How to Set Custom Timezones

By default, schedules without a timezone will run in UTC. If you want to run a schedule in a different timezone, you can
set the `timezone` parameter.

```python
ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_job,
    cron_schedule="15 5 * * 1-5",
timezone="America/Los_Angeles",
)
```

## How to Create Partitioned Schedules

If you have a partitioned asset and job, you can create a schedule from the partition using `build_schedule_from_partitioned_job`.
The schedule will execute as the same cadence specified by the partition definition.

```python
from dagster import (
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
    DailyPartitionsDefinition,
)

daily_partition = DailyPartitionsDefinition(start_date="2024-05-20")


@asset(partitions_def=daily_partition)
def daily_asset(): ...

partitioned_asset_job = define_asset_job("partitioned_job", selection=[daily_asset])

# highlight-start
# This partition will run daily
asset_partitioned_schedule = build_schedule_from_partitioned_job(
    partitioned_asset_job,
)
# highlight-end

```

If you have a partitioned job, you can create a schedule from the partition using `build_schedule_from_partitioned_job`.

```python
from dagster import build_schedule_from_partitioned_job, job


@job(config=partitioned_config)
def partitioned_op_job(): ...

# highlight-start
partitioned_op_schedule = build_schedule_from_partitioned_job(
    partitioned_op_job,
)
# highlight-end
```

---

For more information about how Schedules work, see the [About Schedules](/concepts/schedules) concept page.
