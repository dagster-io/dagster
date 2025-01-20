---
title: Defining schedules
sidebar_position: 100
---

## Defining basic schedules

The following examples demonstrate how to define some basic schedules.

<Tabs>
  <TabItem value="Using ScheduleDefinition">

This example demonstrates how to define a schedule using <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> that will run a job every day at midnight. While this example uses [op jobs](/todo), the same approach will work with [asset jobs](/guides/build/assets/asset-jobs).

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_basic_schedule endbefore=end_basic_schedule
@job
def my_job(): ...


basic_schedule = ScheduleDefinition(job=my_job, cron_schedule="0 0 * * *")
```

:::note

The `cron_schedule` argument accepts standard [cron expressions](https://en.wikipedia.org/wiki/Cron). If your `croniter` dependency's version is `>= 1.0.12`, the argument will also accept the following:
<ul><li>`@daily`</li><li>`@hourly`</li><li>`@monthly`</li></ul>

:::

</TabItem>
<TabItem value="Using @schedule">

This example demonstrates how to define a schedule using <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />, which provides more flexibility than <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" />. For example, you can [configure job behavior based on its scheduled run time](configuring-job-behavior) or [emit log messages](#emitting-log-messages-from-schedule-evaluation).

```python
@schedule(job=my_job, cron_schedule="0 0 * * *")
def basic_schedule(): ...
  # things the schedule does, like returning a RunRequest or SkipReason
```

:::note

The `cron_schedule` argument accepts standard [cron expressions](https://en.wikipedia.org/wiki/Cron). If your `croniter` dependency's version is `>= 1.0.12`, the argument will also accept the following:
<ul><li>`@daily`</li><li>`@hourly`</li><li>`@monthly`</li></ul>

:::

</TabItem>
</Tabs>

## Emitting log messages from schedule evaluation

This example demonstrates how to emit log messages from a schedule during its evaluation function. These logs will be visible in the UI when you inspect a tick in the schedule's tick history.

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_schedule_logging endbefore=end_schedule_logging
@schedule(job=my_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a schedule!")
    return SkipReason("Nothing to do")
```

:::note

Schedule logs are stored in your [Dagster instance's compute log storage](/guides/deploy/dagster-instance-configuration#compute-log-storage). You should ensure that your compute log storage is configured to view your schedule logs.

:::

