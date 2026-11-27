---
description: Guide on automating asset jobs with Declarative Automation
sidebar_position: 150
title: Automating jobs
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

In addition to individual assets and asset checks, automation conditions can be used to automate the execution of asset jobs. This is useful when a set of assets should always be executed together in a single run, rather than each asset being evaluated and requested independently.

To automate a job, pass an `automation_condition` to <PyObject section="assets" module="dagster" object="define_asset_job" />. Job-scoped conditions are built by wrapping an asset-level condition (such as `eager()`, `missing()`, or `on_cron()`) with one of the following:

- <PyObject section="assets" module="dagster" object="AutomationCondition.any_job_root_assets_match" />: true for the
  job if the wrapped condition is true for **at least one** of the job's root assets.
- <PyObject section="assets" module="dagster" object="AutomationCondition.all_job_root_assets_match" />: true for the
  job if the wrapped condition is true for **all** of the job's root assets.

The job's root assets are the assets in the job's selection that have no parents within the job. The wrapped condition is only evaluated against these root assets; when the job's condition becomes true, a single run of the entire job is launched, executing the root assets and everything downstream of them within the job.

In the following example, whenever `raw_data` is updated, the `eager()` condition becomes true for `processed_data` (the job's only root asset), and a single run of `analytics_job` is launched that executes both `processed_data` and `report`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/automate/declarative_automation/jobs/basic.py"
  language="python"
  title="src/<project_name>/defs/jobs.py"
/>

**Behavior**

- The wrapped condition is evaluated against the job's root assets only. Assets downstream of the roots within the job are executed as part of the launched run without being evaluated separately.
- Each time the job's condition becomes true, one run is launched covering the job's full selection.
- Jobs with automation conditions are evaluated by the default automation condition sensor (`default_automation_condition_sensor`), which must be enabled in the UI. For more information, see [automation condition sensors](/guides/automate/declarative-automation/automation-condition-sensors). Custom automation condition sensors cannot target jobs, so jobs are always handled by the default sensor.

## Partitioned jobs

If the assets in the job are partitioned, the job's condition is evaluated on a per-partition basis, and one run is launched for each partition for which the condition is true. Each run is tagged with its partition key.

The following restrictions apply to partitioned jobs with automation conditions:

- All assets in the job must share the same partitions definition.
- A job with an automation condition cannot also have partitioned run config. Providing both an `automation_condition` and a <PyObject section="partitions" module="dagster" object="PartitionedConfig" /> (or a `config` value on a partitioned job) will raise an error when the job is resolved.
- Runs requested for a partitioned job are launched individually and are not grouped into backfills.
