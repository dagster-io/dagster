---
description: Use run config to vary run behavior based on its scheduled launch time.
sidebar_position: 200
title: Configuring behavior based on scheduled run time
---

This example demonstrates how to use run config to vary the behavior of a run based on its scheduled launch time.

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/schedules/schedules.py"
  startAfter="start_run_config_schedule"
  endBefore="end_run_config_schedule"
  title="src/<project_name>/defs/assets.py"
/>

## APIs in this example

- <PyObject section="assets" module="dagster" object="asset" decorator />
- <PyObject section="execution" module="dagster" object="AssetExecutionContext" />
- <PyObject section="schedules-sensors" object="ScheduleEvaluationContext" />
- <PyObject section="schedules-sensors" module="dagster" object="RunRequest" />
