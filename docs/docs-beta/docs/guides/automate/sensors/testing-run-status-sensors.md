---
title: Testing run status sensors
sidebar_position: 600
---

As with other sensors, you can directly invoke run status sensors. However, the `context` provided via <PyObject object="run_status_sensor" /> and <PyObject object="run_failure_sensor" /> contain objects that are typically only available during run time. Below you'll find code snippets that demonstrate how to build the context so that you can directly invoke your function in unit tests.

If you had written a status sensor like this (assuming you implemented the function `email_alert` elsewhere):

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_simple_success_sensor endbefore=end_simple_success_sensor
@run_status_sensor(run_status=DagsterRunStatus.SUCCESS)
def my_email_sensor(context: RunStatusSensorContext):
    message = f'Job "{context.dagster_run.job_name}" succeeded.'
    email_alert(message)
```

We can first write a simple job that will succeed:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_run_status_sensor_testing_with_context_setup endbefore=end_run_status_sensor_testing_with_context_setup
@op
def succeeds():
    return 1


@job
def my_job_succeeds():
    succeeds()
```

Then we can execute this job and pull the attributes we need to build the `context`. We provide a function <PyObject object="build_run_status_sensor_context" /> that will return the correct context object:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_run_status_sensor_testing_marker endbefore=end_run_status_sensor_testing_marker
# execute the job
instance = DagsterInstance.ephemeral()
result = my_job_succeeds.execute_in_process(instance=instance)

# retrieve the DagsterRun
dagster_run = result.dagster_run

# retrieve a success event from the completed execution
dagster_event = result.get_job_success_event()

# create the context
run_status_sensor_context = build_run_status_sensor_context(
    sensor_name="my_email_sensor",
    dagster_instance=instance,
    dagster_run=dagster_run,
    dagster_event=dagster_event,
)

# run the sensor
my_email_sensor(run_status_sensor_context)
```

We have provided convenience functions <PyObject object="ExecuteInProcessResult" method="get_job_success_event" /> and <PyObject object="ExecuteInProcessResult" method="get_job_failure_event" /> for retrieving `DagsterRunStatus.SUCCESS` and `DagsterRunStatus.FAILURE` events, respectively. If you have a run status sensor triggered on another status, you can retrieve all events from `result` and filter based on your event type.

We can use the same pattern to build the context for <PyObject object="run_failure_sensor" />. If we wanted to test this run failure sensor:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_simple_fail_sensor endbefore=end_simple_fail_sensor
@run_failure_sensor
def my_email_failure_sensor(context: RunFailureSensorContext):
    message = (
        f'Job "{context.dagster_run.job_name}" failed. Error:'
        f" {context.failure_event.message}"
    )
    email_alert(message)
```

We first need to make a simple job that will fail:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_failure_sensor_testing_with_context_setup endbefore=end_failure_sensor_testing_with_context_setup
from dagster import op, job


@op
def fails():
    raise Exception("failure!")


@job
def my_job_fails():
    fails()
```

Then we can execute the job and create our context:

```python file=/concepts/partitions_schedules_sensors/sensors/sensor_alert.py startafter=start_alert_sensor_testing_with_context_marker endbefore=end_alert_sensor_testing_with_context_marker
from dagster import DagsterInstance, build_run_status_sensor_context

# execute the job
instance = DagsterInstance.ephemeral()
result = my_job_fails.execute_in_process(instance=instance, raise_on_error=False)

# retrieve the DagsterRun
dagster_run = result.dagster_run

# retrieve a failure event from the completed job execution
dagster_event = result.get_job_failure_event()

# create the context
run_failure_sensor_context = build_run_status_sensor_context(
    sensor_name="my_email_failure_sensor",
    dagster_instance=instance,
    dagster_run=dagster_run,
    dagster_event=dagster_event,
).for_run_failure()

# run the sensor
my_email_failure_sensor(run_failure_sensor_context)
```

Note the additional function call <PyObject object="RunStatusSensorContext" method="for_run_failure" /> after creating the `context`. The `context` provided by <PyObject object="run_failure_sensor" /> is a subclass of the context provided by <PyObject object="run_status_sensor" /> and can be built using this additional call.
