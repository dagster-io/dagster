---
title: "Schedule cron-based pipelines"
sidebar_label: "Schedules"
sidebar_position: 10
---

Schedules enable automated execution of jobs at specified intervals. These intervals can range from common frequencies like hourly, daily, or weekly, to more intricate patterns defined using cron expressions.

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
</details>

## Basic schedule

A basic schedule is defined by a `JobDefinition` and a `cron_schedule` using the `ScheduleDefinition` class. A job can be thought of as a selection of assets or operations executed together.

<CodeExample filePath="guides/automation/simple-schedule-example.py" language="python" />

## Run schedules in a different timezone

By default, schedules without a timezone will run in Coordinated Universal Time (UTC). To run a schedule in a different timezone, set the `timezone` parameter:

```python
daily_schedule = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 0 * * *",
    # highlight-next-line
    timezone="America/Los_Angeles",
)
```

## Create schedules from partitions

If using partitions and jobs, you can create a schedule using the partition with `build_schedule_from_partitioned_job`. The schedule will execute at the same cadence specified by the partition definition.

<Tabs>
<TabItem value="assets" label="Assets">

If you have a [partitioned asset](/guides/partitioning) and job:

<CodeExample filePath="guides/automation/schedule-with-partition.py" language="python" />

</TabItem>
<TabItem value="ops" label="Ops">

If you have a partitioned op job:

<CodeExample filePath="guides/automation/schedule-with-partition-ops.py" language="python" />

</TabItem>
</Tabs>

## Next steps

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints:

- Learn more about schedules in [Understanding automation](/concepts/automation)
- React to events with [sensors](/guides/sensors)
- Explore [Declarative Automation](/concepts/automation/declarative-automation) as an alternative to schedules
