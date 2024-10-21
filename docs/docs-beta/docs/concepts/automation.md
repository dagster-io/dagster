---
title: About Automation
---

There are several ways to automate the execution of your data pipelines with Dagster.

The first system, and the most basic, is the [Schedule](/guides/schedules), which responds to time.

[Sensors](/guides/sensors) are like schedules, but they respond to an external event defined by the user.

[Asset Sensors](/guides/asset-sensors) are a special case of sensor that responds to changes in asset materialization
as reported by the Event Log.

Finally, the Declarative Automation system is a
more complex system that uses conditions on the assets to determine when to execute.

## Schedules

In Dagster, a schedule is defined by the `ScheduleDefinition` class, or through the `@schedule` decorator. The `@schedule`
decorator is more flexible than the `ScheduleDefinition` class, allowing you to configure job behavior or emit log messages
as the schedule is processed.

Schedules were one of the first types of automation in Dagster, created before the introduction of Software-Defined Assets.
As such, you may find that many of the examples can seem foreign if you are used to only working within the asset framework.

For more on how assets and ops inter-relate, read about [Assets and Ops](/concepts/assets#assets-and-ops)

The `dagster-daemon` process is responsible for submitting runs by checking each schedule at a regular interval to determine
if it's time to execute the underlying job.

A schedule can be thought of as a wrapper around two pieces:

- A `JobDefinition`, which is a set of assets to materialize or ops to execute.
- A `cron` string, which describes the schedule.

### Define a schedule using `ScheduleDefinition`

```python
ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_job,
    cron_schedule="15 5 * * 1-5",
)
```

By default, schedules aren't enabled. You can enable them by visiting the Automation tab and toggling the schedule,
or set a default status to `RUNNING` when you define the schedule.

```python
ecommerce_schedule = ScheduleDefinition(
    job=ecommerce_job,
    cron_schedule="15 5 * * 1-5",
    default_status=DefaultScheduleStatus.RUNNING,
)
```

### Define a schedule using `@schedule`

If you want more control over the schedule, you can use the `@schedule` decorator. In doing so, you are then responsible for either
emitting a `RunRequest` or a `SkipReason`. You can also emit logs, which will be visible in the Dagster UI for a given schedule's tick history.

```python
@schedule(cron_schedule="15 5 * * 1-5")
def ecommerce_schedule(context):
    context.log.info("This log message will be visible in the Dagster UI.")
    return RunRequest()
```
