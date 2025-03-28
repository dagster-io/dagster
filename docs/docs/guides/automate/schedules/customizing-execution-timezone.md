---
title: Customizing a schedule's execution timezone
sidebar_position: 300
---

Schedules that don't have a set timezone will, by default, execute in [UTC](https://en.wikipedia.org/wiki/Coordinated_Universal_Time). In this guide, you will learn to:

- Set custom timezones on schedule definitions
- Set custom timezones on partitioned jobs
- Account for the impact of Daylight Savings Time on schedule execution times

:::note

This guide assumes familiarity with:

- Schedules
- Jobs, either [asset](/guides/build/jobs/asset-jobs) or op-based
- [Partitions](/guides/build/partitions-and-backfills/partitioning-assets)

:::

## Setting timezones on schedule definitions

Using the `execution_timezone` parameter allows you to specify a timezone for the schedule on the following objects:

- <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />
- <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" />
- <PyObject section="libraries" object="build_schedule_from_dbt_selection" module="dagster_dbt" />

This parameter accepts any [`tz` timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). For example, the following schedule will execute **every day at 9:00 AM in US Pacific time (America/Los_Angeles)**:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedules/schedules.py"
  startAfter="start_timezone"
  endBefore="end_timezone"
/>

## Setting timezones on partitioned jobs

Schedules constructed from partitioned jobs execute in the timezone defined on the partition's config. Partitions definitions have a `timezone` parameter, which accepts any [`tz` timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

For example, the following partition uses the **US Pacific (America/Los_Angeles)** timezone:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/partition_with_timezone.py" />

## Execution times and Daylight Savings Time

When Daylight Savings Time (DST) begins and ends, there may be some impact on your schedules' execution times.

### Impact on daily schedules

Because of DST transitions, it's possible to specify an execution time that doesn't exist for every scheduled interval.

Let's say you have a **schedule that executes every day at 2:30 AM.** On the day DST begins, time jumps from 2:00AM to 3:00AM, which means the time of 2:30 AM won't exist.

Dagster would instead run the schedule at the next time that exists, which would be 3:00 AM:

```markdown
# DST begins: time jumps forward an hour at 2:00 AM

- 12:30 AM
- 1:00 AM
- 1:30 AM
- 3:00 AM ## time transition; schedule executes
- 3:30 AM
- 4:00 AM
```

It's also possible to specify an execution time that exists twice on one day every year.

Let's say you have a **schedule that executes every day at 1:30 AM.** On the day DST ends, the hour from 1:00 AM to 2:00 AM repeats, which means the time of 1:30 AM will exist twice. This means there are two possible times the schedule could run.

In this case, Dagster would execute the schedule at the second iteration of 1:30 AM:

```markdown
# DST ends: time jumps backward an hour at 2:00 AM

- 12:30 AM
- 1:00 AM
- 1:30 AM
- 1:00 AM ## time transition
- 1:30 AM ## schedule executes
- 2:00 AM
```

### Impact on hourly schedules

Hourly schedules are unaffected by daylight savings time transitions. Schedules will continue to run exactly once an hour, even as DST ends and the hour from 1:00 AM to 2:00 AM repeats.

Let's say you have a **schedule that executes hourly at 30 minutes past the hour.** On the day DST ends, the schedule would run at 12:30 AM and both instances of 1:30 AM before proceeding normally at 2:30 AM:

```markdown
# DST ends: time jumps backward an hour at 2:00 AM

- 12:30 AM ## schedule executes
- 1:00 AM
- 1:30 AM ## schedule executes
- 1:00 AM ## time transition
- 1:30 AM ## schedule executes
- 2:00 AM
- 2:30 AM ## schedule executes
```

## APIs in this guide

| Name                                                                                                    | Description                                                                                         |
| ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />                   | Decorator that defines a schedule that executes according to a given cron schedule.                 |
| <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" />                   | Class for schedules.                                                                                |
| <PyObject section="schedules-sensors" module="dagster"  object="build_schedule_from_partitioned_job" /> | A function that constructs a schedule whose interval matches the partitioning of a partitioned job. |
| <PyObject section="libraries" object="build_schedule_from_dbt_selection" module="dagster_dbt" />        | A function that constructs a schedule that materializes a set of specified dbt resources.           |
