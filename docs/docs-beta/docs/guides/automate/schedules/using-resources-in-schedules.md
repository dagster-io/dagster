---
title: Using resources in schedules
sidebar_position: 500
---

This example demonstrates how to use resources in schedules. To specify a resource dependency, annotate the resource as a parameter to the schedule's function.

:::note

This article assumes familiarity with [resources](/guides/build/external-resources/), [code locations and definitions](/guides/deploy/code-locations/), and [schedule testing](testing-schedules).

All Dagster definitions, including schedules and resources, must be attached to a <PyObject section="definitions" module="dagster" object="Definitions" /> call.

:::

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

## APIs in this guide

| Name | Description |
|------|-------------|
| <PyObject section="schedules-sensors" module="dagster" object="schedule" decorator /> | Decorator that defines a schedule that executes according to a given cron schedule. |
| <PyObject object="ConfigurableResource" /> | |
| <PyObject section="jobs" module="dagster" object="job" decorator /> | The decorator used to define a job. |
| <PyObject section="execution" module="dagster" object="RunRequest" />                          | A class that represents all the information required to launch a single run. |
| <PyObject object="RunConfig" /> | |
| <PyObject section="definitions" module="dagster" object="Definitions" /> | |
