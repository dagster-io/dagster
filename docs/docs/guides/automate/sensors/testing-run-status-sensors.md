---
title: Testing run status sensors
sidebar_position: 600
---

As with other sensors, you can directly invoke run status sensors. However, the `context` provided via <PyObject section="schedules-sensors" module="dagster" object="run_status_sensor" /> and <PyObject section="schedules-sensors" module="dagster" object="run_failure_sensor" /> contain objects that are typically only available during run time. Below you'll find code snippets that demonstrate how to build the context so that you can directly invoke your function in unit tests.

If you had written a status sensor like this (assuming you implemented the function `email_alert` elsewhere):


<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_simple_success_sensor" endBefore="end_simple_success_sensor" />

We can first write a simple job that will succeed:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_run_status_sensor_testing_with_context_setup" endBefore="end_run_status_sensor_testing_with_context_setup" />

Then we can execute this job and pull the attributes we need to build the `context`. We provide a function <PyObject section="schedules-sensors" module="dagster" object="build_run_status_sensor_context" /> that will return the correct context object:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_run_status_sensor_testing_marker" endBefore="end_run_status_sensor_testing_marker" />

{/* TODO the methods and statuses below do not exist in API docs
We have provided convenience functions <PyObject section="execution" module="dagster" object="ExecuteInProcessResult" method="get_job_success_event" /> and <PyObject section="execution" module="dagster" object="ExecuteInProcessResult" method="get_job_failure_event" /> for retrieving `DagsterRunStatus.SUCCESS` and `DagsterRunStatus.FAILURE` events, respectively. If you have a run status sensor triggered on another status, you can retrieve all events from `result` and filter based on your event type.
*/}

We can use the same pattern to build the context for <PyObject section="schedules-sensors" module="dagster" object="run_failure_sensor" />. If we wanted to test this run failure sensor:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_simple_fail_sensor" endBefore="end_simple_fail_sensor" />

We first need to make a simple job that will fail:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_failure_sensor_testing_with_context_setup" endBefore="end_failure_sensor_testing_with_context_setup" />

Then we can execute the job and create our context:

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py" startAfter="start_alert_sensor_testing_with_context_marker" endBefore="end_alert_sensor_testing_with_context_marker" />

Note the additional function call <PyObject section="schedules-sensors" module="dagster" object="RunStatusSensorContext" method="for_run_failure" /> after creating the `context`. The `context` provided by <PyObject section="schedules-sensors" module="dagster" object="run_failure_sensor" /> is a subclass of the context provided by <PyObject section="schedules-sensors" module="dagster" object="run_status_sensor" /> and can be built using this additional call.
