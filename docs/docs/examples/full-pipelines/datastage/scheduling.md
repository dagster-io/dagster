---
title: Schedule IBM DataStage replication jobs
description: Schedule IBM DataStage replication jobs using flexible asset selection syntax
last_update:
  author: Dennis Hume
sidebar_position: 30
---

With the replication assets defined, the next step is to schedule them. This example uses two schedules: a daily run for data replication and a weekly run for data quality checks. Rather than hardcoding asset keys into each schedule, we use Dagster's asset selection syntax to target assets by tag or group so schedules remain correct as the table list grows or changes.

## The scheduling component

`ScheduledJobComponent` takes a cron expression and an asset selection string and creates a Dagster job with a schedule:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/scheduled_job_component.py"
  language="python"
  startAfter="start_scheduled_job_component"
  endBefore="end_scheduled_job_component"
  title="src/project_datastage/components/scheduled_job_component.py"
/>

The `asset_selection` field accepts the same syntax as Dagster's asset selection UI: `tag:key=value`, `group:name`, `kind:name`, and boolean operators like `and`, `or`, `not`. This makes it easy to target a subset of assets without modifying the component.

## Putting it together with YAML

The full pipeline showcases a replication job that copies five tables from a DB2 mainframe to Snowflake with inline data-quality checks, plus two schedules; declared in a single `defs.yaml` file as three composed components:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/defs/datastage_pipeline/defs.yaml"
  language="yaml"
  title="src/project_datastage/defs/datastage_pipeline/defs.yaml"
/>

The first document declares the `DataStageJobComponent` with `demo_mode: true` so it runs locally without a `cpdctl` installation. The second runs the replication daily at 6 AM UTC, targeting `tag:schedule=daily` which matches the tag set by `DataStageTranslator.get_tags`. The third reruns all assets in the `datastage_replication` group every Monday at 8 AM UTC because checks run inline with materialization, this also re-executes the row count and freshness checks for every table. Changing the schedule frequency or adding a third schedule requires only a new YAML document, no Python changes needed.
