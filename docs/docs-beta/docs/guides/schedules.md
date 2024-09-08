---
title: "Schedule cron-based pipelines"
sidebar_label: "Schedules"
sidebar_position: 10
---

Schedules enable automated execution of jobs at specified intervals. These intervals can range from common frequencies like hourly, daily, or weekly, to more intricate patterns defined using cron expressions.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
</details>

## Basic schedule

A basic schedule is defined by a `JobDefinition` and a `cron_schedule` using the `ScheduleDefinition` class. A job can be thought of as a selection of assets or operations executed together.

<CodeExample filePath="guides/automation/simple-schedule-example.py" language="python" title="Simple Schedule Example" />

## Run schedules in a different timezone

By default, schedules without a timezone will run in Coordinated Universal Time (UTC). If you want to run a schedule in a different timezone, you can set the `timezone` parameter.

```python
daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 0 * * *",
    timezone="America/Los_Angeles",
)
```

## Run schedules on a partitioned asset

If you have a partitioned asset and job, you can create a schedule using the partition with `build_schedule_from_partitioned_job`.
The schedule will execute as the same cadence specified by the partition definition.

<CodeExample filePath="guides/automation/schedule-with-partition.py" language="python" title="Schedule with partition" />

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



## Next steps

- Learn more about schedules in [Understanding Automation](/concepts/automation)
- React to events with [sensors](/guides/sensors)
- Explore [Declarative Automation](/concepts/automation/declarative-automation) as an alternative to schedules

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints.
