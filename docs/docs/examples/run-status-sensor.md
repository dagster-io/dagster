---
title: Run status sensor
description: How to coordinate multiple jobs using run status sensors.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
  miniProject: true
tags: [mini-project]
---

In this example, we'll explore how to use run status [sensors](/guides/automate/sensors) to coordinate the execution of multiple independent [jobs](/guides/build/jobs). This pattern is particularly useful when you need to trigger a downstream job only after several upstream jobs have all completed successfully, but those upstream jobs might run independently or on different schedules.

### Problem: Coordinating multiple independent jobs

Imagine you have multiple independent jobs that process different data sources, and you want to trigger a downstream aggregation job only after all upstream jobs have completed successfully. Unlike regular asset dependencies, these jobs might:

- Run on different schedules
- Be triggered manually at different times
- Complete at different rates

You need a way to detect when all upstream jobs have successfully completed and trigger the downstream job exactly once per "batch" of completions.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/run_status_sensor/assets.py"
  language="python"
  title="assets.py"
/>

In this example, we have two upstream jobs (`upstream_job_1` and `upstream_job_2`) that process different assets, and a downstream job (`downstream_job`) that should only run after both upstream jobs complete successfully.

### Solution: Run status sensor with completion tracking

The run status sensor monitors the completion status of multiple jobs and uses a cursor to track which runs have already been processed, ensuring the downstream job triggers exactly once per batch of upstream completions.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/run_status_sensor/sensors.py"
  language="python"
  title="sensors.py"
/>

### Key components of the solution

**1. RunsFilter for querying job completions**
<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/run_status_sensor/sensors.py"
  startAfter="start_runs_filter"
  endBefore="end_runs_filter"
  language="python"
  title="sensors.py"
/>

The sensor uses `RunsFilter` to query for successful runs of each upstream job, allowing you to check completion status across multiple jobs.

**2. Cursor-based state tracking**
<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/run_status_sensor/sensors.py"
  startAfter="start_cursor_tracking"
  endBefore="end_cursor_tracking"
  language="python"
  title="sensors.py"
/>

The cursor stores the completion times of the last processed runs, ensuring the sensor doesn't retrigger on the same job completions.

**3. Conditional triggering with time-based filtering**
<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/run_status_sensor/sensors.py"
  startAfter="start_conditional_trigger"
  endBefore="end_conditional_trigger"
  language="python"
  title="sensors.py"
/>

The downstream job only triggers when:
- Both upstream jobs have completed successfully
- Both completions are recent (within the past day, `completion_time_a > one_day_ago`)
- Both completions are newer than the previously processed runs (cursor comparison)

### Benefits of this approach

- **Flexible coordination**: Works with jobs that run on different schedules or are triggered independently
- **Exactly-once semantics**: Uses cursor tracking to ensure the downstream job runs exactly once per batch of upstream completions
- **Time-based filtering**: Prevents stale or very old runs from inadvertently triggering downstream processing
- **Scalable**: Can easily be extended to monitor more than two upstream jobs by adding additional filters and cursor tracking

