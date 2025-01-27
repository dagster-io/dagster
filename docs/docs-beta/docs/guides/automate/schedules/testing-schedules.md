---
title: "Testing schedules"
sidebar_position: 600
---

In this article, we'll show you how to use the Dagster UI and Python to test your [schedules](index.md).

## Testing schedules in the Dagster UI

Using the UI, you can manually trigger test evaluations of a schedule and view the results. This can be helpful when [creating a schedule](defining-schedules) or for [troubleshooting unexpected scheduling behavior](troubleshooting-schedules).

1. In the UI, click **Overview > Schedules tab**.

2. Click the schedule you want to test.

3. Click the **Test Schedule** button, located near the top right corner of the page.

4. You'll be prompted to select a mock schedule evaluation time. As schedules are defined on a cadence, the evaluation times in the dropdown are past and future times along that cadence.

   For example, let's say you're testing a schedule with a cadence of `"Every day at X time"`. In the dropdown, you'd see past and future evaluation times along that cadence:

    ![Selecting a mock evaluation time for a schedule in the Dagster UI](/images/guides/automate/schedules/testing-select-timestamp-page.png)

5. After selecting an evaluation time, click the **Evaluate** button.

A window containing the evaluation result will display after the test completes. If the evaluation was successful, click **Open in Launchpad** to launch a run with the same config as the test evaluation.

## Testing schedules in Python

You can also test your schedules directly in Python. In this section, we'll demonstrate how to test:

- [`@schedule`-decorated functions](#testing-schedule-decorated-functions)
- [Schedules with resources](#testing-schedules-with-resources)

### Testing @schedule-decorated functions

To test a function decorated by the <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> decorator, you can invoke the schedule definition like it's a regular Python function. The invocation will return run config, which can then be validated using the <PyObject section="execution" module="dagster" object="validate_run_config" /> function.

Let's say we want to test the `configurable_job_schedule` in this example:

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedules.py startafter=start_run_config_schedule endbefore=end_run_config_schedule
@op(config_schema={"scheduled_date": str})
def configurable_op(context: OpExecutionContext):
    context.log.info(context.op_config["scheduled_date"])


@job
def configurable_job():
    configurable_op()


@schedule(job=configurable_job, cron_schedule="0 0 * * *")
def configurable_job_schedule(context: ScheduleEvaluationContext):
    scheduled_date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {"configurable_op": {"config": {"scheduled_date": scheduled_date}}}
        },
        tags={"date": scheduled_date},
    )
```

To test this schedule, we used <PyObject section="schedules-sensors" module="dagster" object="build_schedule_context" /> to construct a <PyObject section="schedules-sensors" module="dagster" object="ScheduleEvaluationContext" /> to provide to the `context` parameter:

{/* TODO convert to <CodeExample> */}
```python file=concepts/partitions_schedules_sensors/schedules/schedule_examples.py startafter=start_test_cron_schedule_context endbefore=end_test_cron_schedule_context
from dagster import build_schedule_context, validate_run_config


def test_configurable_job_schedule():
    context = build_schedule_context(
        scheduled_execution_time=datetime.datetime(2020, 1, 1)
    )
    run_request = configurable_job_schedule(context)
    assert validate_run_config(configurable_job, run_request.run_config)
```

If your <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />-decorated function doesn't have a context parameter, you don't need to provide one when invoking it.

### Testing schedules with resources

For schedules that utilize [resources](/guides/build/external-resources), you can provide the resources when invoking the schedule function.

Let's say we want to test the `process_data_schedule` in this example:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_on_schedule endbefore=end_new_resource_on_schedule dedent=4
from dagster import (
    schedule,
    ScheduleEvaluationContext,
    ConfigurableResource,
    job,
    RunRequest,
    RunConfig,
    Definitions,
)
from datetime import datetime
from typing import List

class DateFormatter(ConfigurableResource):
    format: str

    def strftime(self, dt: datetime) -> str:
        return dt.strftime(self.format)

@job
def process_data(): ...

@schedule(job=process_data, cron_schedule="* * * * *")
def process_data_schedule(
    context: ScheduleEvaluationContext,
    date_formatter: DateFormatter,
):
    formatted_date = date_formatter.strftime(context.scheduled_execution_time)

    return RunRequest(
        run_key=None,
        tags={"date": formatted_date},
    )

defs = Definitions(
    jobs=[process_data],
    schedules=[process_data_schedule],
    resources={"date_formatter": DateFormatter(format="%Y-%m-%d")},
)
```

In the test for this schedule, we provided the `date_formatter` resource to the schedule when we invoked its function:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/resources/pythonic_resources.py startafter=start_test_resource_on_schedule endbefore=end_test_resource_on_schedule dedent=4
from dagster import build_schedule_context, validate_run_config

def test_process_data_schedule():
    context = build_schedule_context(
        scheduled_execution_time=datetime.datetime(2020, 1, 1)
    )
    run_request = process_data_schedule(
        context, date_formatter=DateFormatter(format="%Y-%m-%d")
    )
    assert (
        run_request.run_config["ops"]["fetch_data"]["config"]["date"]
        == "2020-01-01"
    )
```

## APIs in this guide

| Name                                            | Description                                                                           |
| ----------------------------------------------- | ------------------------------------------------------------------------------------- |
| <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator />        | Decorator that defines a schedule that executes according to a given cron schedule.   |
| <PyObject section="execution" module="dagster" object="validate_run_config" />       | A function that validates a provided run config blob against a job.                   |
| <PyObject section="schedules-sensors" module="dagster" object="build_schedule_context" />    | A function that constructs a `ScheduleEvaluationContext`, typically used for testing. |
| <PyObject section="schedules-sensors" module="dagster" object="ScheduleEvaluationContext" /> | The context passed to the schedule definition execution function.                     |
