---
title: Creating sensors that react to run statuses
sidebar_position: 500
---

If you want to act on the status of a run, Dagster provides a way to create a sensor that reacts to run statuses. You can use <PyObject object="run_status_sensor" /> with a specified <PyObject object="DagsterRunStatus" /> to decorate a function that will run when the given status occurs. This can be used to launch other runs, send alerts to a monitoring service on run failure, or report a run success.

Here is an example of a run status sensor that launches a run of `status_reporting_job` if a run is successful:

```python file=concepts/partitions_schedules_sensors/sensors/run_status_run_requests.py startafter=start endbefore=end
@run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
    request_job=status_reporting_job,
)
def report_status_sensor(context):
    # this condition prevents the sensor from triggering status_reporting_job again after it succeeds
    if context.dagster_run.job_name != status_reporting_job.name:
        run_config = {
            "ops": {
                "status_report": {"config": {"job_name": context.dagster_run.job_name}}
            }
        }
        return RunRequest(run_key=None, run_config=run_config)
    else:
        return SkipReason("Don't report status of status_reporting_job")
```

`request_job` is the job that will be run when the `RunRequest` is returned.

Note that in `report_status_sensor` we conditionally return a `RunRequest`. This ensures that when `report_status_sensor` runs `status_reporting_job` it doesn't enter an infinite loop where the success of `status_reporting_job` triggers another run of `status_reporting_job`, which triggers another run, and so on.

Here is an example of a sensor that reports job success in a Slack message:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_success_sensor_marker endbefore=end_success_sensor_marker
from dagster import run_status_sensor, RunStatusSensorContext, DagsterRunStatus


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
def my_slack_on_run_success(context: RunStatusSensorContext):
    slack_client = WebClient(token=os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"])

    slack_client.chat_postMessage(
        channel="#alert-channel",
        text=f'Job "{context.dagster_run.job_name}" succeeded.',
    )
```

When a run status sensor is triggered by a run but doesn't return anything, Dagster will report an event back to the run to indicate that the sensor ran.

Once you have written your sensor, you can add the sensor to a <PyObject object="Definitions" /> object so it can be enabled and used the same as other sensors:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_definitions_marker endbefore=end_definitions_marker
from dagster import Definitions


defs = Definitions(jobs=[my_sensor_job], sensors=[my_slack_on_run_success])
```
