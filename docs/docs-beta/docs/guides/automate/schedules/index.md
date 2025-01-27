---
title: "Schedules"
sidebar_position: 10
---

Schedules enable automated execution of jobs at specified intervals. These intervals can range from common frequencies like hourly, daily, or weekly, to more intricate patterns defined using cron expressions.

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [assets](/guides/build/assets/)
- Familiarity with [jobs](/guides/build/assets/asset-jobs/)
</details>

## Basic schedule

A basic schedule is defined by a `JobDefinition` and a `cron_schedule` using the `ScheduleDefinition` class. A job can be thought of as a selection of assets or operations executed together.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/automation/simple-schedule-example.py" language="python" />

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

For more information, see "[Customizing a schedule's execution timezone](customizing-execution-timezone)".

## Create schedules from partitions

If using partitions and jobs, you can create a schedule using the partition with `build_schedule_from_partitioned_job`. The schedule will execute at the same cadence specified by the partition definition.

<Tabs>
<TabItem value="assets" label="Assets">

If you have a [partitioned asset](/guides/build/partitions-and-backfills) and job:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/automation/schedule-with-partition.py" language="python" />

</TabItem>
<TabItem value="ops" label="Ops">

If you have a partitioned op job:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/automation/schedule-with-partition-ops.py" language="python" />

</TabItem>
</Tabs>

## Next steps

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints:

- Learn more about schedules in [Understanding automation](/guides/automate/index.md)
- React to events with [sensors](/guides/automate/sensors)
- Explore [Declarative Automation](/guides/automate/declarative-automation) as an alternative to schedules
