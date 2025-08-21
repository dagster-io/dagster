---
description: Create Dagster sensors to react to run statuses using run_status_sensor and DagsterRunStatus for automated actions like launching runs or sending alerts.
sidebar_position: 500
title: Creating sensors that react to run statuses
---

If you want to act on the status of a run, Dagster provides a way to create a sensor that reacts to run statuses. You can use <PyObject section="schedules-sensors" module="dagster" object="run_status_sensor" /> with a specified <PyObject section="internals" module="dagster" object="DagsterRunStatus" /> to decorate a function that will run when the given status occurs. This can be used to launch other runs, send alerts to a monitoring service on run failure, or report a run success.

Here is an example of a run status sensor that launches a run of `status_reporting_job` if a run is successful:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/run_status_run_requests.py"
  startAfter="start"
  endBefore="end"
  title="src/<project_name>/defs/sensors.py"
/>

`request_job` is the job that will be run when the `RunRequest` is returned.

Note that in `report_status_sensor` we conditionally return a `RunRequest`. This ensures that when `report_status_sensor` runs `status_reporting_job` it doesn't enter an infinite loop where the success of `status_reporting_job` triggers another run of `status_reporting_job`, which triggers another run, and so on.

Here is an example of a sensor that reports job success in a Slack message:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensor_alert.py"
  startAfter="start_success_sensor_marker"
  endBefore="end_success_sensor_marker"
  title="src/<project_name>/defs/sensors.py"
/>

When a run status sensor is triggered by a run but doesn't return anything, Dagster will report an event back to the run to indicate that the sensor ran.
