---
title: Configuring job behavior based on scheduled run time
sidebar_position: 200
---

This example demonstrates how to use run config to vary the behavior of a job based on its scheduled run time.

<CodeExample path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedules/schedules.py" startAfter="start_run_config_schedule" endBefore="end_run_config_schedule" />

## APIs in this example

* <PyObject section="ops" module="dagster" object="op" decorator />
* <PyObject section="jobs" module="dagster" object="job" decorator />
* <PyObject section="execution" module="dagster" object="OpExecutionContext" />
* <PyObject section="schedules-sensors" object="ScheduleEvaluationContext" />
* <PyObject section="schedules-sensors" module="dagster" object="RunRequest" />
